"""Fastfetch-inspired terminal presentation for the system snapshot."""

from pathlib import Path

from rich.console import Console, Group
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

COLORS = {
    "os": "#56B6FF",
    "kernel": "#BE8CFF",
    "packages": "#FF9E64",
    "shell": "#66E880",
    "wm": "#E5D142",
    "cpu": "#45E3CD",
    "gpu": "#E485F6",
    "screen": "#7A9CFF",
    "memory": "#FF75A0",
    "disk": "#94F0AD",
    "uptime": "#F7C77E",
}


def _logo() -> str:
    """Use the Fastfetch logo file when present, with a built-in fallback."""
    source = Path.home() / ".config" / "fastfetch" / "arch.txt"
    try:
        return source.read_text(encoding="utf-8").rstrip("\n")
    except OSError:
        return ARCH_LOGO


def _swatches() -> Text:
    return Text.assemble(
        ("  ", "white"),
        ("󰮯 ", "#FFE156"),
        (" ", "#45C9E5"),
        ("󰊠 ", "#FF6384"),
        ("󰊠 ", "#4ADE80"),
        ("󰊠 ", "#38BDF8"),
        ("󰊠 ", "#C084FC"),
        ("󰊠", "white"),
    )


def _value_table(info: SystemInfo) -> Table:
    rows = Table.grid(padding=(0, 0))
    rows.add_column(width=14, no_wrap=True)
    rows.add_column(overflow="fold")

    def add(label: str, color: str, value: str) -> None:
        rows.add_row(Text(label, style=color), Text("  " + value))

    add(" 󰣇 OS", COLORS["os"], info.distribution)
    add("  OS Age", COLORS["os"], info.os_age)
    add(" 󰌽 Kernel", COLORS["kernel"], info.kernel)
    add(" 󰏖 Packages", COLORS["packages"], info.packages)
    add("  Shell", COLORS["shell"], info.shell)
    add("  WM", COLORS["wm"], info.window_manager)
    cpu = info.cpu
    if info.cpu_frequency_mhz:
        cpu += f" @{info.cpu_frequency_mhz / 1000:.1f}GHz"
    add("  CPU", COLORS["cpu"], cpu)
    add(" 󰢮 GPU 0", COLORS["gpu"], info.gpu)
    add(" 󰍹 Screen", COLORS["screen"], info.resolution)
    add("  Memory", COLORS["memory"], f"{format_bytes(info.memory_used)} / {format_bytes(info.memory_total)} ({info.memory_percent:.0f}%)")
    add(" 󰋊 Disk 1", COLORS["disk"], f"{format_bytes(info.disk_used)} / {format_bytes(info.disk_total)} ({info.disk_percent:.0f}%)")
    for index, disk in enumerate(info.extra_disks, start=2):
        add(f" 󰋊 Disk {index}", COLORS["disk"], f"{format_bytes(disk.used)} / {format_bytes(disk.total)} ({disk.percent:.0f}%)")
    add(" 󰔚 Uptime", COLORS["uptime"], format_uptime(info.uptime_seconds))
    rows.add_row("", "")
    rows.add_row(Text(" 󰸱 Color", style="white"), _swatches())
    return rows


def render_showcase(info: SystemInfo, console: Console | None = None, *, show_logo: bool = True) -> None:
    """Render the machine snapshot in the supplied Fastfetch-style layout."""
    console = console or Console()
    title = Text.assemble(
        (info.username, "#FF8282"),
        ("@", "#666666"),
        (info.hostname, "#FFACF3"),
    )
    details = Group(title, Text("───────────────", style="#666666"), _value_table(info))
    if show_logo:
        logo = Text("\n\n" + "\n".join(f"  {line}" for line in _logo().splitlines()), style="#56B6FF")
        layout = Table.grid(padding=(0, 2), expand=False)
        layout.add_column()
        layout.add_column()
        layout.add_row(logo, details)
        console.print(layout)
    else:
        console.print(details)

