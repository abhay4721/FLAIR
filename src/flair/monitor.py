"""Live resource and network monitor."""

from __future__ import annotations

import time
from pathlib import Path
import platform
import shutil
import subprocess
import threading
from types import SimpleNamespace

import psutil
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from flair.system import format_bytes
from flair.theme import load_theme

_GPU_LOCK = threading.Lock()
_GPU_VALUE = "Unavailable"
_GPU_THREAD: threading.Thread | None = None


def _read_gpu() -> None:
    """Refresh an NVIDIA or AMD reading in the background."""
    global _GPU_VALUE
    value = "Unavailable"
    if shutil.which("nvidia-smi"):
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=1, check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                value = result.stdout.strip().splitlines()[0].replace(",", " ·")
        except (OSError, subprocess.TimeoutExpired):
            pass
    elif platform.system() == "Linux":
        value = _amd_gpu_status()
    with _GPU_LOCK:
        _GPU_VALUE = value


def _amd_gpu_status() -> str:
    """Read AMD/DRM counters directly from sysfs when the driver exposes them."""
    for device in sorted(Path("/sys/class/drm").glob("card[0-9]/device")):
        try:
            if (device / "vendor").read_text().strip().lower() != "0x1002":
                continue
            parts = []
            busy = device / "gpu_busy_percent"
            if busy.is_file():
                parts.append(f"{busy.read_text().strip()}%")
            used, total = device / "mem_info_vram_used", device / "mem_info_vram_total"
            if used.is_file() and total.is_file():
                parts.append(f"VRAM {int(used.read_text()) // 1048576}/{int(total.read_text()) // 1048576} MiB")
            for hwmon in (device / "hwmon").glob("hwmon*"):
                sensor = next(iter(sorted(hwmon.glob("temp*_input"))), None)
                if sensor:
                    parts.append(f"{int(sensor.read_text()) / 1000:.0f}°C")
                    break
            if parts:
                return " · ".join(parts)
        except (OSError, ValueError):
            continue
    return "Unavailable"


def _gpu_status() -> str:
    """Return the cached GPU reading and start a refresh when idle."""
    global _GPU_THREAD
    if not shutil.which("nvidia-smi") and platform.system() != "Linux":
        return "Unavailable"
    with _GPU_LOCK:
        if _GPU_THREAD is None or not _GPU_THREAD.is_alive():
            _GPU_THREAD = threading.Thread(target=_read_gpu, daemon=True)
            _GPU_THREAD.start()
        return _GPU_VALUE


def _dashboard(interval: float, colors: dict[str, str], root: str, display: dict[str, bool]) -> Table:
    cpu = psutil.cpu_percent(interval=None)
    try:
        memory = psutil.virtual_memory()
    except (OSError, NotImplementedError):
        memory = SimpleNamespace(percent=0.0, used=0)
    try:
        swap = psutil.swap_memory()
    except (OSError, NotImplementedError):
        swap = SimpleNamespace(percent=0.0, used=0)
    try:
        disk = psutil.disk_usage(root)
    except (OSError, NotImplementedError):
        disk = SimpleNamespace(percent=0.0, used=0)
    try:
        net = psutil.net_io_counters() or SimpleNamespace(bytes_sent=0, bytes_recv=0)
    except (OSError, NotImplementedError):
        net = SimpleNamespace(bytes_sent=0, bytes_recv=0)
    try:
        frequency = psutil.cpu_freq()
    except (OSError, AttributeError, NotImplementedError):
        frequency = None
    now = time.monotonic()
    previous = getattr(_dashboard, "previous", (now, net.bytes_sent, net.bytes_recv))
    elapsed = max(now - previous[0], 0.001)
    upload = max(0, net.bytes_sent - previous[1]) / elapsed
    download = max(0, net.bytes_recv - previous[2]) / elapsed
    _dashboard.previous = (now, net.bytes_sent, net.bytes_recv)

    table = Table(title="FLAIR · live monitor", border_style=colors["primary"], header_style=colors["secondary"])
    table.add_column("Resource", style=colors["text"])
    table.add_column("Use", min_width=24)
    table.add_column("Rate / amount", justify="right")
    resources = []
    if display.get("show_cpu", True):
        resources.append(("CPU", cpu, None, colors["cpu"]))
    if display.get("show_memory", True):
        resources.append(("Memory", memory.percent, format_bytes(memory.used), colors["memory"]) if memory.total else ("Memory", -1, "Unavailable", colors["memory"]))
        resources.append(("Swap", swap.percent, format_bytes(swap.used), colors["gpu"]) if swap.total else ("Swap", -1, "Unavailable", colors["gpu"]))
    if display.get("show_disk", True):
        resources.append(("Disk", disk.percent, format_bytes(disk.used), colors["disk"]) if getattr(disk, "total", 0) else ("Disk", -1, "Unavailable", colors["disk"]))
    for name, percent, used, color in resources:
        if percent < 0:
            table.add_row(name, "", used)
            continue
        bar_width = 20
        filled = round(bar_width * max(0, min(100, percent)) / 100)
        bar = Text("█" * filled, style=color) + Text("░" * (bar_width - filled), style=colors["muted"])
        table.add_row(name, bar, f"{percent:.0f}%" + (f" · {used}" if used else ""))
    if display.get("show_network", True):
        table.add_row("Network ↑", "", f"{format_bytes(int(upload))}/s")
        table.add_row("Network ↓", "", f"{format_bytes(int(download))}/s")
    if display.get("show_gpu", True):
        table.add_row("GPU", "", _gpu_status())
    if display.get("show_cpu", True):
        table.add_row("CPU clock", "", f"{frequency.current:.0f} MHz" if frequency else "Unavailable")
    if display.get("show_uptime", True):
        try:
            uptime = max(0, int(time.time() - psutil.boot_time()))
        except (OSError, NotImplementedError):
            uptime = 0
        table.add_row("Uptime", "", f"{uptime // 86400}d {(uptime % 86400) // 3600}h {(uptime % 3600) // 60}m")
    table.caption = f"Refreshes every {interval:g}s · Ctrl+C to exit"
    return table


def run_live(interval: float, console: Console | None = None, *, theme: str = "arch-blue", display: dict[str, bool] | None = None) -> None:
    """Refresh the resource dashboard until Ctrl+C."""
    if not 0.2 <= interval <= 30:
        raise ValueError("Refresh interval must be between 0.2 and 30 seconds")
    console = console or Console()
    colors = load_theme(theme)
    display = display or {}
    root = Path.home().anchor or "/"
    psutil.cpu_percent(interval=None)
    if not console.is_terminal:
        console.print(_dashboard(interval, colors, root, display))
        return
    try:
        with Live(_dashboard(interval, colors, root, display), console=console, refresh_per_second=max(1, int(1 / interval))) as live:
            while True:
                time.sleep(interval)
                live.update(_dashboard(interval, colors, root, display), refresh=True)
    except KeyboardInterrupt:
        console.print("\n[dim]Monitoring stopped.[/]")
