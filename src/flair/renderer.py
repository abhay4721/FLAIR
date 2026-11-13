"""Configurable fetch-style terminal output."""

from pathlib import Path

from rich.console import Console, Group
from rich.table import Table
from rich.text import Text

from flair.art import get_art
from flair.system import SystemInfo, format_bytes, format_uptime
from flair.theme import load_theme

STYLE_MODULES: dict[str, list[str]] = {
    "default": ["title", "separator", "os", "os_age", "kernel", "packages", "shell", "wm", "cpu", "gpu", "screen", "memory", "disk", "uptime", "colors"],
    "detailed": ["title", "separator", "os", "host", "kernel", "uptime", "packages", "shell", "de", "wm", "screen", "cpu", "gpu", "memory", "disk", "colors"],
    "classic": ["title", "separator", "os", "kernel", "uptime", "packages", "shell", "de", "screen", "cpu", "gpu", "memory", "disk", "colors"],
    "minimal": ["title", "os", "cpu", "memory", "disk", "uptime"],
}

MODULE_LABELS: dict[str, tuple[str, str]] = {
    "os": ("󰣇 OS", "primary"),
    "os_age": (" OS Age", "primary"),
    "kernel": ("󰌽 Kernel", "secondary"),
    "packages": ("󰏖 Packages", "accent"),
    "host": ("󰌢 Host", "primary"),
    "uptime": ("󰔚 Uptime", "warning"),
    "shell": (" Shell", "success"),
    "terminal": (" Terminal", "success"),
    "wm": (" WM", "wm"),
    "de": ("󰧨 DE", "wm"),
    "display_server": ("󰍹 Display", "screen"),
    "architecture": ("󰻠 Arch", "secondary"),
    "cpu": (" CPU", "cpu"),
    "cores": ("󰘚 Cores", "cpu"),
    "frequency": ("󰓅 Frequency", "cpu"),
    "gpu": ("󰢮 GPU 0", "gpu"),
    "gpu_driver": ("󰍹 Driver", "gpu"),
    "screen": ("󰍹 Screen", "screen"),
    "memory": (" Memory", "memory"),
    "swap": ("󰓡 Swap", "memory"),
    "disk": ("󰋊 Disk 1", "disk"),
}


def module_names() -> list[str]:
    """Return the module names accepted by config and CLI overrides."""
    return ["title", "separator", *MODULE_LABELS, "colors"]


def modules_for(style: str, configured: list[str] | None = None) -> list[str]:
    """Choose a fetch layout and validate a configured module list."""
    if style not in STYLE_MODULES:
        raise ValueError(f"Unknown fetch style '{style}'")
    if configured is not None:
        invalid = [item for item in configured if item not in module_names()]
        if invalid:
            raise ValueError("Unknown module(s): " + ", ".join(invalid))
        return list(configured)
    return list(STYLE_MODULES[style])


def _module_value(name: str, info: SystemInfo) -> str:
    values = {
        "os": info.distribution,
        "os_age": info.os_age,
        "kernel": info.kernel,
        "packages": info.packages,
        "host": info.host_model if info.host_model != "Unknown" else info.hostname,
        "uptime": format_uptime(info.uptime_seconds),
        "shell": info.shell,
        "terminal": info.terminal,
        "wm": info.window_manager,
        "de": info.desktop,
        "display_server": info.display_server,
        "architecture": info.architecture,
        "cpu": info.cpu,
        "cores": f"{info.physical_cores or '?'} physical / {info.logical_threads or '?'} logical",
        "frequency": f"{info.cpu_frequency_mhz:.0f} MHz" if info.cpu_frequency_mhz else "Unavailable",
        "gpu": info.gpu,
        "gpu_driver": info.gpu_driver,
        "screen": info.resolution,
        "memory": f"{format_bytes(info.memory_used)} / {format_bytes(info.memory_total)} ({info.memory_percent:.0f}%)" if info.memory_total else "Unavailable",
        "swap": f"{format_bytes(info.swap_used)} / {format_bytes(info.swap_total)}" if info.swap_total else "Unavailable",
        "disk": f"{format_bytes(info.disk_used)} / {format_bytes(info.disk_total)} ({info.disk_percent:.0f}%)" if info.disk_total else "Unavailable",
    }
    if name == "cpu" and info.cpu_frequency_mhz:
        return f"{info.cpu} @{info.cpu_frequency_mhz / 1000:.1f}GHz"
    return values[name]


def _swatches() -> Text:
    return Text.assemble(
        ("  ", "white"), ("󰮯 ", "#FFE156"), (" ", "#45C9E5"),
        ("󰊠 ", "#FF6384"), ("󰊠 ", "#4ADE80"), ("󰊠 ", "#38BDF8"), ("󰊠 ", "#C084FC"), ("󰊠", "white"),
    )


def _module_table(key_width: int) -> Table:
    rows = Table.grid(padding=(0, 0))
    rows.add_column(width=key_width, no_wrap=True)
    rows.add_column(overflow="fold")
    return rows


def _logo_text(name: str, path: str, colors: dict[str, str]) -> Text:
    if path:
        source = Path(path).expanduser()
        if not source.is_file() or source.stat().st_size > 262144:
            raise ValueError("Logo file must exist and be no larger than 256 KiB")
        logo = source.read_text(encoding="utf-8").rstrip("\n")
        if not logo.strip():
            raise ValueError("Logo file is empty")
    else:
        logo = get_art(name)
    return Text(logo, style=colors["primary"])


def _resolve_auto_logo(info: SystemInfo) -> str:
    label = info.distribution.casefold()
    if "raspberry" in label or "raspbian" in label:
        return "raspberry-pi"
    if "pop" in label:
        return "pop"
    if "android" in label or "termux" in label:
        return "termux"
    return next((name for name in ("windows", "macos", "endeavouros", "elementary", "mint", "kali", "ubuntu", "debian", "fedora", "manjaro", "opensuse", "nixos", "gentoo", "alpine", "void", "solus", "arch") if name in label), "arch")


def render_showcase(
    info: SystemInfo,
    console: Console | None = None,
    *,
    show_logo: bool = True,
    theme: str = "arch-blue",
    logo_name: str = "auto",
    logo_path: str = "",
    logo_padding: dict[str, int] | None = None,
    display: dict[str, bool] | None = None,
    style: str = "default",
    modules: list[str] | None = None,
    separator: str = "  ",
    key_width: int = 14,
    layout: str = "auto",
) -> None:
    """Render a selected FLAIR layout with optional custom modules."""
    console = console or Console()
    colors = load_theme(theme)
    display = display or {}
    logo_padding = logo_padding or {"top": 2, "left": 2, "right": 4}
    selected = modules_for(style, modules)
    hidden_by_setting = {
        "show_cpu": {"cpu", "cores", "frequency"},
        "show_gpu": {"gpu", "gpu_driver"},
        "show_memory": {"memory", "swap"},
        "show_disk": {"disk"},
        "show_uptime": {"uptime"},
    }
    for setting, hidden_modules in hidden_by_setting.items():
        if not display.get(setting, True):
            selected = [name for name in selected if name not in hidden_modules]

    rows = _module_table(key_width)
    title = Text.assemble((info.username, colors["error"]), ("@", colors["muted"]), (info.hostname, colors["title_host"]))
    blocks: list[object] = []
    for module in selected:
        if module == "title":
            if rows.row_count:
                blocks.append(rows)
                rows = _module_table(key_width)
            blocks.append(title)
            continue
        if module == "separator":
            if rows.row_count:
                blocks.append(rows)
                rows = _module_table(key_width)
            blocks.append(Text("───────────────", style=colors["muted"]))
            continue
        if module == "colors":
            rows.add_row(Text("󰸱 Color", style=colors["text"]), _swatches())
            continue
        label, color_key = MODULE_LABELS[module]
        rows.add_row(Text(label, style=colors[color_key]), Text(separator + _module_value(module, info)))
        if module == "disk":
            for index, disk in enumerate(info.extra_disks, start=2):
                value = f"{format_bytes(disk.used)} / {format_bytes(disk.total)} ({disk.percent:.0f}%)"
                rows.add_row(Text(f"󰋊 Disk {index}", style=colors["disk"]), Text(separator + value))
    if rows.row_count:
        blocks.append(rows)
    content = Group(*blocks)
    if show_logo:
        raw_logo = _logo_text(logo_name if logo_name != "auto" else _resolve_auto_logo(info), logo_path, colors)
        top = max(0, logo_padding.get("top", 0))
        left = max(0, logo_padding.get("left", 0))
        logo = Text("\n" * top + "\n".join(" " * left + line for line in raw_logo.plain.splitlines()), style=colors["primary"])
        effective_layout = "side-by-side" if layout == "auto" and console.width >= 88 else "top" if layout == "auto" else layout
        if effective_layout == "top":
            console.print(logo)
            console.print(content)
        else:
            row = Table.grid(padding=(0, max(0, logo_padding.get("right", 4) // 2)), expand=False)
            row.add_column()
            row.add_column()
            row.add_row(logo, content)
            console.print(row)
    else:
        console.print(content)

