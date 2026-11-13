"""Collect system facts from Linux interfaces and psutil."""

from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import psutil


@dataclass(frozen=True)
class SystemInfo:
    distribution: str
    os_version: str
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


def _os_release() -> tuple[str, str]:
    fields: dict[str, str] = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator:
                fields[key] = value.strip().strip('"')
    except OSError:
        pass
    return fields.get("PRETTY_NAME", platform.system()), fields.get("VERSION_ID", "")


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
        name, _, driver = nvidia.partition(",")
        return name.strip(), driver.strip() or "NVIDIA"

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

    for line in _run(["lspci", "-mm"]).splitlines():
        if any(kind in line for kind in ('"VGA compatible controller"', '"3D controller"', '"Display controller"')):
            fields = line.split('"')
            return (fields[5] if len(fields) > 5 else "GPU detected"), ""
    return "Not detected", ""


def _resolution() -> str:
    for line in _run(["xrandr", "--current"]).splitlines():
        if " connected " not in line:
            continue
        for token in line.split():
            if "x" in token and token.split("x", 1)[0].isdigit():
                return token.split("+", 1)[0]
    return "Unknown"


def _cpu_name() -> str:
    name = platform.processor()
    if name:
        return name
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith(("model name", "hardware")) and ":" in line:
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return "Unknown"


def collect_system_info() -> SystemInfo:
    """Collect a snapshot of the current machine; unavailable details stay explicit."""
    distribution, version = _os_release()
    memory, swap, disk = psutil.virtual_memory(), psutil.swap_memory(), psutil.disk_usage("/")
    frequency = psutil.cpu_freq()
    gpu, gpu_driver = _gpu_details()
    desktop = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or "Unknown"
    window_manager = "Hyprland" if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE") else os.environ.get("XDG_SESSION_DESKTOP", "Unknown")
    return SystemInfo(
        distribution=distribution,
        os_version=version or "Unknown",
        kernel=platform.release(),
        architecture=platform.machine() or "Unknown",
        hostname=socket.gethostname(),
        username=os.environ.get("USER") or "Unknown",
        uptime_seconds=max(0, int(time.time() - psutil.boot_time())),
        desktop=desktop,
        window_manager=window_manager,
        display_server=os.environ.get("XDG_SESSION_TYPE", "Unknown").capitalize(),
        shell=Path(os.environ.get("SHELL", "")).name or "Unknown",
        terminal=os.environ.get("TERM_PROGRAM") or os.environ.get("TERM", "Unknown"),
        resolution=_resolution(),
        cpu=_cpu_name(),
        physical_cores=psutil.cpu_count(logical=False),
        logical_threads=psutil.cpu_count(logical=True),
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

