"""Terminal presentation for the static system showcase."""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from flair.system import SystemInfo, format_bytes, format_uptime

ARCH_LOGO = """       /\\
      /  \\
     /    \\
    /      \\
   /   ,,   \\
  /   |  |   \\
 /_-''    ''-_\\"""


def render_showcase(info: SystemInfo, console: Console | None = None, *, show_logo: bool = True) -> None:
    """Render the machine snapshot in a compact panel."""
    console = console or Console()
    details = Table.grid(padding=(0, 1))
    details.add_column(style="bold #1793D1", no_wrap=True)
    details.add_column(style="#E6EDF3", overflow="fold")
    details.add_row("OS", f"{info.distribution} {info.os_version} · {info.architecture}")
    details.add_row("Kernel", info.kernel)
    details.add_row("Host", f"{info.username}@{info.hostname}")
    details.add_row("Uptime", format_uptime(info.uptime_seconds))
    details.add_row("Desktop", f"{info.desktop} · {info.window_manager} · {info.display_server}")
    details.add_row("Shell", f"{info.shell} · {info.terminal}")
    details.add_row("Display", info.resolution)
    details.add_row("CPU", f"{info.cpu} · {info.physical_cores or '?'} cores / {info.logical_threads or '?'} threads")
    if info.cpu_frequency_mhz:
        details.add_row("Frequency", f"{info.cpu_frequency_mhz:.0f} MHz")
    details.add_row("GPU", f"{info.gpu}" + (f" · driver {info.gpu_driver}" if info.gpu_driver != "Unknown" else ""))
    details.add_row("Memory", f"{format_bytes(info.memory_used)} / {format_bytes(info.memory_total)} ({info.memory_percent:.0f}%)")
    details.add_row("Swap", f"{format_bytes(info.swap_used)} / {format_bytes(info.swap_total)}")
    details.add_row("Root disk", f"{format_bytes(info.disk_used)} / {format_bytes(info.disk_total)} ({info.disk_percent:.0f}%)")
    content = Table.grid(expand=True, padding=(0, 2))
    if show_logo:
        content.add_column(width=20, justify="center")
    content.add_column(ratio=1)
    content.add_row(Text(ARCH_LOGO, style="#56B4E9"), details) if show_logo else content.add_row(details)
    title = Text(" FLAIR ", style="bold white on #1793D1")
    console.print(Panel(content, title=title, subtitle="Your machine. Your style. Your terminal.", border_style="#1793D1", box=box.ROUNDED, padding=(1, 2)))

