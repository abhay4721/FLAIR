"""Collect system facts from Linux interfaces and psutil."""

from __future__ import annotations

import json
import getpass
import os
import platform
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import psutil


@dataclass(frozen=True)
class DiskMount:
    mountpoint: str
    total: int
    used: int
    percent: float


@dataclass(frozen=True)
class SystemInfo:
    distribution: str
    os_version: str
    os_age: str
    packages: str
    kernel: str
    architecture: str
    hostname: str
    username: str
    uptime_seconds: int
    desktop: str
    window_manager: str
    display_server: str
    shell: str
    terminal: str
    resolution: str
    cpu: str
    physical_cores: int | None
    logical_threads: int | None
    cpu_frequency_mhz: float | None
    gpu: str
    gpu_driver: str
    memory_total: int
    memory_used: int
    memory_percent: float
    swap_total: int
    swap_used: int
    disk_total: int
    disk_used: int
    disk_percent: float
    extra_disks: tuple[DiskMount, ...]


def _os_release() -> tuple[str, str]:
    system = platform.system()
    if system == "Windows":
        version, _, build = platform.win32_ver()
        caption = _run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_OperatingSystem).Caption"])
        return caption or f"Windows {version or platform.version()}", build or version
    if system == "Darwin":
        version = platform.mac_ver()[0]
        return f"macOS {version}" if version else "macOS", version
    if os.environ.get("TERMUX_VERSION") or Path("/data/data/com.termux/files/usr").exists():
        android_version = _run(["getprop", "ro.build.version.release"])
        return (f"Android {android_version} (Termux)" if android_version else "Android (Termux)"), android_version
    fields: dict[str, str] = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator:
                fields[key] = value.strip().strip('"')
    except OSError:
        pass
    return fields.get("PRETTY_NAME", platform.platform()), fields.get("VERSION_ID", "")


def _run(command: list[str]) -> str:
    """Run a read-only system query; missing utilities are ordinary."""
    if not shutil.which(command[0]):
        return ""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=2, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _gpu_details() -> tuple[str, str]:
    nvidia = _run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"])
    if nvidia:
        name, _, driver = nvidia.splitlines()[0].partition(",")
        return name.strip(), driver.strip() or "NVIDIA"

    if platform.system() == "Darwin":
        details = _run(["system_profiler", "SPDisplaysDataType"])
        for line in details.splitlines():
            if line.strip().startswith("Chipset Model:"):
                return line.split(":", 1)[1].strip(), ""
    elif platform.system() == "Windows":
        details = _run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_VideoController).Name"])
        if details:
            return details.splitlines()[0].strip(), ""

    for line in _run(["lspci", "-mm"]).splitlines():
        if any(kind in line for kind in ('"VGA compatible controller"', '"3D controller"', '"Display controller"')):
            fields = line.split('"')
            return (fields[5] if len(fields) > 5 else "GPU detected"), ""

    for device in sorted(Path("/sys/class/drm").glob("card[0-9]/device")):
        try:
            vendor = (device / "vendor").read_text().strip().lower()
            if vendor in {"0x1002", "0x8086", "0x10de"}:
                pci_id = next(
                    (line.partition("=")[2] for line in (device / "uevent").read_text(errors="replace").splitlines() if line.startswith("PCI_ID=")),
                    "",
                )
                return (f"GPU ({vendor}, PCI {pci_id})" if pci_id else f"GPU ({vendor})"), ""
        except OSError:
            continue
    return "Not detected", ""


def _resolution() -> str:
    if platform.system() == "Windows":
        try:
            import ctypes

            width = ctypes.windll.user32.GetSystemMetrics(0)
            height = ctypes.windll.user32.GetSystemMetrics(1)
            return f"{width}x{height}" if width and height else "Unknown"
        except (AttributeError, OSError):
            return "Unknown"
    if platform.system() == "Darwin":
        details = _run(["system_profiler", "SPDisplaysDataType"])
        for line in details.splitlines():
            if line.strip().startswith("Resolution:"):
                return line.split(":", 1)[1].strip()
        return "Unknown"
    monitors = _run(["hyprctl", "monitors", "-j"])
    if monitors:
        try:
            connected = json.loads(monitors)
            monitor = next((item for item in connected if item.get("focused")), connected[0] if connected else {})
            width, height = monitor.get("width"), monitor.get("height")
            if width and height:
                refresh = monitor.get("refreshRate")
                suffix = f" @ {refresh:g}Hz" if isinstance(refresh, (int, float)) and refresh > 0 else ""
                return f"{width}x{height}{suffix}"
        except (ValueError, TypeError, KeyError):
            pass

    for line in _run(["wlr-randr"]).splitlines():
        if "(current" in line:
            tokens = line.split()
            dimensions = next((token for token in tokens if "x" in token and token.split("x", 1)[0].isdigit()), "")
            hz_index = next((index for index, token in enumerate(tokens) if token == "Hz"), -1)
            refresh = tokens[hz_index - 1].rstrip(",") + "Hz" if hz_index > 0 else ""
            if dimensions:
                return f"{dimensions} @ {refresh}" if refresh else dimensions

    for line in _run(["xrandr", "--current"]).splitlines():
        if " connected " not in line:
            continue
        tokens = line.split()
        for index, token in enumerate(tokens):
            if "x" in token and token.split("x", 1)[0].isdigit():
                resolution = token.split("+", 1)[0]
                refresh = next((rate.rstrip("*+") for rate in tokens[index + 1:] if "*" in rate), "")
                return f"{resolution} @ {refresh}Hz" if refresh else resolution
    return "Unknown"


def _os_age() -> str:
    """Estimate the root filesystem age, matching Fastfetch's birth/mtime fallback."""
    if platform.system() != "Linux":
        return "Unknown"
    raw = _run(["stat", "-c", "%w", "/"])
    if not raw or raw == "-":
        raw = _run(["stat", "-c", "%y", "/"])
    if not raw:
        return "Unknown"
    try:
        from datetime import date

        installed = date.fromisoformat(raw.split()[0])
        days = max(0, (date.today() - installed).days)
        return f"{installed.isoformat()} , {days} days ({days // 365} years)"
    except ValueError:
        return "Unknown"


def _package_count() -> str:
    """Count packages with an installed package manager, if available."""
    checks = (
        (["pacman", "-Qq"], "pacman"),
        (["dpkg-query", "-f", "${binary:Package}\\n", "-W"], "dpkg"),
        (["rpm", "-qa", "--qf", "%{NAME}\\n"], "rpm"),
        (["apk", "info"], "apk"),
        (["xbps-query", "-l"], "xbps"),
        (["brew", "list", "--formula", "--versions"], "Homebrew"),
    )
    for command, manager in checks:
        output = _run(command)
        if output:
            return f"{len(output.splitlines())} ({manager})"
    return "Unknown"


def _cpu_name() -> str:
    if platform.system() == "Darwin":
        name = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
        if name:
            return name
    if platform.system() == "Windows":
        name = _run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)"])
        if name:
            return name
    if platform.system() == "Linux":
        try:
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace").splitlines():
                if line.lower().startswith(("model name", "hardware")) and ":" in line:
                    return line.split(":", 1)[1].strip()
        except OSError:
            pass
    name = platform.processor()
    if name:
        return name
    return "Unknown"


def collect_system_info() -> SystemInfo:
    """Collect a snapshot of the current machine; unavailable details stay explicit."""
    distribution, version = _os_release()
    try:
        memory = psutil.virtual_memory()
    except (OSError, NotImplementedError):
        memory = SimpleNamespace(total=0, used=0, percent=0.0)
    try:
        swap = psutil.swap_memory()
    except (OSError, NotImplementedError):
        swap = SimpleNamespace(total=0, used=0, percent=0.0)
    root = Path.home().anchor or "/"
    try:
        disk = psutil.disk_usage(root)
    except (OSError, NotImplementedError):
        try:
            disk = psutil.disk_usage(str(Path.home()))
        except (OSError, NotImplementedError):
            disk = SimpleNamespace(total=0, used=0, percent=0.0)
    try:
        frequency = psutil.cpu_freq()
    except (OSError, AttributeError, NotImplementedError):
        frequency = None
    gpu, gpu_driver = _gpu_details()
    system = platform.system()
    if os.environ.get("TERMUX_VERSION") or distribution.endswith("(Termux)"):
        desktop, window_manager, display_server = "Termux", "Android", "Terminal"
    elif system == "Windows":
        desktop, window_manager, display_server = "Windows", "Desktop Window Manager", "Unknown"
    elif system == "Darwin":
        desktop, window_manager, display_server = "Aqua", "Quartz Compositor", "Quartz"
    else:
        desktop = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or "Unknown"
        window_manager = "Hyprland" if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE") else os.environ.get("XDG_SESSION_DESKTOP", "Unknown")
        display_server = os.environ.get("XDG_SESSION_TYPE", "Unknown").capitalize()
    try:
        disk_parts = psutil.disk_partitions(all=False)
    except (OSError, NotImplementedError):
        disk_parts = []
    seen_devices = {part.device for part in disk_parts if os.path.normcase(part.mountpoint) == os.path.normcase(root)}
    extra_disks: list[DiskMount] = []
    for part in disk_parts:
        mountpoint = Path(part.mountpoint)
        if part.device in seen_devices or not mountpoint.is_dir():
            continue
        if system == "Windows":
            include_mount = True
        else:
            include_mount = str(mountpoint).startswith(("/run/media/", "/media/", "/mnt/", "/Volumes/"))
        if not include_mount:
            continue
        try:
            usage = psutil.disk_usage(str(mountpoint))
        except (OSError, NotImplementedError):
            continue
        seen_devices.add(part.device)
        extra_disks.append(DiskMount(str(mountpoint), usage.total, usage.used, usage.percent))
    try:
        physical_cores = psutil.cpu_count(logical=False)
        logical_threads = psutil.cpu_count(logical=True)
    except (OSError, AttributeError, NotImplementedError):
        physical_cores = logical_threads = os.cpu_count()
    try:
        boot_time = psutil.boot_time()
        uptime = max(0, int(time.time() - boot_time))
    except (OSError, AttributeError, NotImplementedError):
        uptime = 0
    try:
        username = getpass.getuser()
    except (KeyError, OSError):
        username = "Unknown"
    return SystemInfo(
        distribution=distribution,
        os_version=version or "Unknown",
        os_age=_os_age(),
        packages=_package_count(),
        kernel=platform.release(),
        architecture=platform.machine() or "Unknown",
        hostname=socket.gethostname(),
        username=os.environ.get("USER") or os.environ.get("USERNAME") or username,
        uptime_seconds=uptime,
        desktop=desktop,
        window_manager=window_manager,
        display_server=display_server,
        shell=Path(os.environ.get("SHELL") or os.environ.get("COMSPEC", "")).name or "Unknown",
        terminal=os.environ.get("TERM_PROGRAM") or ("Windows Terminal" if os.environ.get("WT_SESSION") else os.environ.get("TERM", "Unknown")),
        resolution=_resolution(),
        cpu=_cpu_name(),
        physical_cores=physical_cores,
        logical_threads=logical_threads,
        cpu_frequency_mhz=frequency.current if frequency else None,
        gpu=gpu,
        gpu_driver=gpu_driver or "Unknown",
        memory_total=memory.total,
        memory_used=memory.used,
        memory_percent=memory.percent,
        swap_total=swap.total,
        swap_used=swap.used,
        disk_total=disk.total,
        disk_used=disk.used,
        disk_percent=disk.percent,
        extra_disks=tuple(extra_disks),
    )


def format_bytes(value: int) -> str:
    """Format bytes with readable binary units."""
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TiB"


def format_uptime(seconds: int) -> str:
    """Format seconds as days, hours and minutes."""
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    parts = ([f"{days}d"] if days else []) + ([f"{hours}h"] if hours or days else []) + [f"{minutes}m"]
    return " ".join(parts)

