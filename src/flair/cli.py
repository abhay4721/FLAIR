"""Command line interface for FLAIR."""

from __future__ import annotations

import os
import platform
import shlex
import shutil
import subprocess
from pathlib import Path

import psutil
import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from flair import __version__
from flair.animations import intro
from flair.art import available_art, get_art, import_art, remove_art
from flair.config import DEFAULT_TOML, config_path, load_config
from flair.monitor import run_live
from flair.renderer import render_showcase
from flair.system import collect_system_info, format_bytes
from flair.theme import list_themes, load_theme, save_theme_choice

console = Console()
app = typer.Typer(help="A fast system showcase and monitor for your terminal.", no_args_is_help=False, add_completion=False)
art_app = typer.Typer(help="Browse and manage terminal artwork.", no_args_is_help=False)
theme_app = typer.Typer(help="Choose or preview a color theme.", no_args_is_help=False)
config_app = typer.Typer(help="View and edit FLAIR configuration.", no_args_is_help=False)
system_app = typer.Typer(help="Inspect individual system details.", no_args_is_help=False)


def _config() -> dict:
    try:
        return load_config()
    except ValueError as exc:
        console.print(f"[red]Configuration error:[/] {exc}")
        raise typer.Exit(code=2) from exc


def _show_snapshot(info=None, *, no_animation: bool = True) -> None:
    config = _config()
    try:
        if not no_animation:
            intro(console, enabled=config["animation"])
        render_showcase(
            info or collect_system_info(),
            console,
            show_logo=config["show_logo"],
            theme=config["theme"],
            logo_name=config["logo"]["name"],
            display=config["display"],
        )
    except ValueError as exc:
        console.print(f"[red]FLAIR:[/] {exc}")
        raise typer.Exit(code=2) from exc


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    no_animation: bool = typer.Option(False, "--no-animation", help="Skip the startup reveal."),
    version: bool = typer.Option(False, "--version", help="Print the installed version and exit.", is_eager=True),
) -> None:
    """Show a snapshot of this machine."""
    if version:
        console.print(f"FLAIR {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        _show_snapshot(no_animation=no_animation)


@app.command()
def live(interval: float | None = typer.Option(None, min=0.2, max=30, help="Refresh interval in seconds.")) -> None:
    """Open the live CPU, memory, disk and network dashboard."""
    config = _config()
    try:
        run_live(interval or float(config["refresh_interval"]), console, theme=config["theme"], display=config["display"])
    except ValueError as exc:
        console.print(f"[red]FLAIR:[/] {exc}")
        raise typer.Exit(code=2) from exc


@app.command("themes")
def themes_command() -> None:
    """List built-in and installed user themes."""
    selected = _config()["theme"]
    for name in list_themes():
        console.print(f"{'*' if name == selected else ' '} {name}")


@app.command("doctor")
def doctor() -> None:
    """Check FLAIR's runtime environment and optional system tools."""
    table = Table(title="FLAIR doctor", show_header=True)
    table.add_column("Check")
    table.add_column("Result")
    table.add_row("Platform", f"{platform.system()} · {platform.release()} · Python {platform.python_version()}")
    try:
        process_access = "available" if psutil.Process().pid else "unavailable"
    except (OSError, psutil.Error):
        process_access = "unavailable"
    table.add_row("Process access", process_access)
    table.add_row("Config", str(config_path()))
    try:
        config = load_config()
        load_theme(config["theme"])
        table.add_row("Config and theme", "valid")
    except (OSError, ValueError) as exc:
        table.add_row("Config and theme", f"[red]{exc}[/]")
    for tool in ("nvidia-smi", "lspci", "hyprctl", "wlr-randr", "xrandr"):
        if shutil.which(tool):
            table.add_row(tool, "available")
    console.print(table)


@art_app.callback(invoke_without_command=True)
def art_root(ctx: typer.Context) -> None:
    """List artwork, or show the chosen logo when called directly."""
    if ctx.invoked_subcommand is None:
        art_list()


@art_app.command("list")
def art_list() -> None:
    """List built-in and imported logos."""
    for name in available_art():
        console.print(name)


@art_app.command("show")
def art_show(name: str = "arch") -> None:
    """Print a logo preview."""
    try:
        console.print(Text(get_art(name), style="#56B6FF"))
    except (OSError, ValueError) as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=2) from exc


@art_app.command("import")
def art_import(source: Path, name: str | None = None) -> None:
    """Import a text logo without replacing existing artwork."""
    try:
        destination = import_art(source.expanduser(), name)
    except (OSError, ValueError) as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=2) from exc
    console.print(f"Imported [bold]{destination.stem}[/] to {destination}")


@art_app.command("add")
def art_add(source: Path, name: str | None = None) -> None:
    """Add an artwork file (same behavior as import)."""
    art_import(source, name)


@art_app.command("remove")
def art_remove(name: str, yes: bool = typer.Option(False, "--yes", help="Remove without asking.")) -> None:
    """Remove an imported logo."""
    if not yes and not typer.confirm(f"Remove custom logo '{name}'?", default=False):
        raise typer.Abort()
    try:
        removed = remove_art(name)
    except (OSError, ValueError) as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=2) from exc
    console.print(f"Removed {removed}")


@theme_app.command("set")
def theme_set(name: str) -> None:
    """Set the active theme."""
    try:
        path = save_theme_choice(name)
    except (OSError, ValueError) as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=2) from exc
    console.print(f"Theme set to [bold]{name}[/] ({path})")


@theme_app.command("preview")
def theme_preview(name: str) -> None:
    """Preview a palette in the current terminal."""
    try:
        colors = load_theme(name)
    except ValueError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=2) from exc
    console.print(Text(f" {name} ", style=f"bold white on {colors['primary']}"))
    for field, color in colors.items():
        console.print(Text(f"  {field:<12} FLAIR terminal palette", style=color))


@config_app.callback(invoke_without_command=True)
def config_root(ctx: typer.Context) -> None:
    """Print the active configuration path and contents."""
    if ctx.invoked_subcommand is None:
        path = config_path()
        _config()
        console.print(f"[bold]{path}[/]")
        console.print(path.read_text(encoding="utf-8"))


@config_app.command("edit")
def config_edit() -> None:
    """Open the configuration in the configured text editor."""
    path = config_path()
    _config()
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    command = shlex.split(editor) if editor else (["notepad"] if platform.system() == "Windows" else ["nano"])
    try:
        subprocess.run([*command, str(path)], check=False)
    except OSError as exc:
        console.print(f"[red]Could not open editor:[/] {exc}")
        raise typer.Exit(code=2) from exc


@config_app.command("reset")
def config_reset(yes: bool = typer.Option(False, "--yes", help="Reset without asking.")) -> None:
    """Back up and reset the FLAIR configuration."""
    if not yes and not typer.confirm("Reset FLAIR configuration to defaults?", default=False):
        raise typer.Abort()
    path = config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            backup = path.with_suffix(path.suffix + ".bak")
            counter = 1
            while backup.exists():
                backup = path.with_suffix(path.suffix + f".bak.{counter}")
                counter += 1
            shutil.copy2(path, backup)
            console.print(f"Saved previous config to {backup}")
        path.write_text(DEFAULT_TOML, encoding="utf-8")
    except OSError as exc:
        console.print(f"[red]Could not reset configuration:[/] {exc}")
        raise typer.Exit(code=2) from exc
    console.print(f"Reset {path}")


@system_app.callback(invoke_without_command=True)
def system_root(ctx: typer.Context) -> None:
    """Show the full machine snapshot or choose one detail below."""
    if ctx.invoked_subcommand is None:
        _show_snapshot()


@system_app.command("cpu")
def system_cpu() -> None:
    """Show processor model, cores, threads and frequency."""
    info = collect_system_info()
    frequency = f" · {info.cpu_frequency_mhz:.0f} MHz" if info.cpu_frequency_mhz else ""
    console.print(f"{info.cpu} · {info.physical_cores or '?'} cores / {info.logical_threads or '?'} threads{frequency}")


@system_app.command("gpu")
def system_gpu() -> None:
    """Show the detected graphics adapter."""
    info = collect_system_info()
    console.print(info.gpu + (f" · driver {info.gpu_driver}" if info.gpu_driver != "Unknown" else ""))


@system_app.command("memory")
def system_memory() -> None:
    """Show memory and swap use."""
    info = collect_system_info()
    console.print(f"RAM {format_bytes(info.memory_used)} / {format_bytes(info.memory_total)} ({info.memory_percent:.0f}%)" if info.memory_total else "RAM Unavailable")
    console.print(f"Swap {format_bytes(info.swap_used)} / {format_bytes(info.swap_total)}" if info.swap_total else "Swap Unavailable")


@system_app.command("disk")
def system_disk() -> None:
    """Show root and removable disk use."""
    info = collect_system_info()
    console.print(f"Disk 1 {format_bytes(info.disk_used)} / {format_bytes(info.disk_total)} ({info.disk_percent:.0f}%)" if info.disk_total else "Disk 1 Unavailable")
    for index, disk in enumerate(info.extra_disks, start=2):
        console.print(f"Disk {index} {disk.mountpoint}: {format_bytes(disk.used)} / {format_bytes(disk.total)} ({disk.percent:.0f}%)")


app.add_typer(art_app, name="art")
app.add_typer(theme_app, name="theme")
app.add_typer(config_app, name="config")
app.add_typer(system_app, name="system")

