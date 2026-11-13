"""Fastfetch-inspired terminal presentation for the system snapshot."""

from rich.console import Console, Group
from rich.table import Table
from rich.text import Text

from flair.art import get_art
from flair.system import SystemInfo, format_bytes, format_uptime
from flair.theme import load_theme

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


def _value_table(info: SystemInfo, colors: dict[str, str], display: dict[str, bool]) -> Table:
    rows = Table.grid(padding=(0, 0))
    rows.add_column(width=14, no_wrap=True)
    rows.add_column(overflow="fold")

    def add(label: str, color: str, value: str) -> None:
        rows.add_row(Text(label, style=color), Text("  " + value))

    add(" 󰣇 OS", colors["primary"], info.distribution)
    add("  OS Age", colors["primary"], info.os_age)
    add(" 󰌽 Kernel", colors["secondary"], info.kernel)
    add(" 󰏖 Packages", colors["accent"], info.packages)
    add("  Shell", colors["success"], info.shell)
    add("  WM", colors["wm"], info.window_manager)
    if display.get("show_cpu", True):
        cpu = info.cpu
        if info.cpu_frequency_mhz:
            cpu += f" @{info.cpu_frequency_mhz / 1000:.1f}GHz"
        add("  CPU", colors["cpu"], cpu)
    if display.get("show_gpu", True):
        add(" 󰢮 GPU 0", colors["gpu"], info.gpu)
    add(" 󰍹 Screen", colors["screen"], info.resolution)
    if display.get("show_memory", True):
        memory = f"{format_bytes(info.memory_used)} / {format_bytes(info.memory_total)} ({info.memory_percent:.0f}%)" if info.memory_total else "Unavailable"
        add("  Memory", colors["memory"], memory)
    if display.get("show_disk", True):
        disk = f"{format_bytes(info.disk_used)} / {format_bytes(info.disk_total)} ({info.disk_percent:.0f}%)" if info.disk_total else "Unavailable"
        add(" 󰋊 Disk 1", colors["disk"], disk)
        for index, disk in enumerate(info.extra_disks, start=2):
            add(f" 󰋊 Disk {index}", colors["disk"], f"{format_bytes(disk.used)} / {format_bytes(disk.total)} ({disk.percent:.0f}%)")
    if display.get("show_uptime", True):
        add(" 󰔚 Uptime", colors["warning"], format_uptime(info.uptime_seconds))
    rows.add_row("", "")
    rows.add_row(Text(" 󰸱 Color", style="white"), _swatches())
    return rows


def render_showcase(
    info: SystemInfo,
    console: Console | None = None,
    *,
    show_logo: bool = True,
    theme: str = "arch-blue",
    logo_name: str = "auto",
    display: dict[str, bool] | None = None,
) -> None:
    """Render the machine snapshot in the supplied Fastfetch-style layout."""
    console = console or Console()
    colors = load_theme(theme)
    display = display or {}
    if logo_name == "auto":
        label = info.distribution.casefold()
        if "raspberry" in label or "raspbian" in label:
            logo_name = "raspberry-pi"
        elif "pop" in label:
            logo_name = "pop"
        else:
            logo_name = next((name for name in ("termux", "windows", "macos", "endeavouros", "elementary", "mint", "kali", "ubuntu", "debian", "fedora", "manjaro", "opensuse", "nixos", "gentoo", "alpine", "void", "solus", "arch") if name in label), "arch")
        if "android" in label:
            logo_name = "termux"
    logo = get_art(logo_name) if show_logo else ""
    title = Text.assemble(
        (info.username, colors["error"]),
        ("@", colors["muted"]),
        (info.hostname, colors["title_host"]),
    )
    details = Group(title, Text("───────────────", style=colors["muted"]), _value_table(info, colors, display))
    if show_logo:
        logo_text = Text("\n\n" + "\n".join(f"  {line}" for line in logo.splitlines()), style=colors["primary"])
        layout = Table.grid(padding=(0, 2), expand=False)
        layout.add_column()
        layout.add_column()
        layout.add_row(logo_text, details)
        console.print(layout)
    else:
        console.print(details)

