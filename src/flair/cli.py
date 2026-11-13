"""Command line entry point for FLAIR."""

import typer
from rich.console import Console

from flair import __version__
from flair.animations import intro
from flair.config import load_config
from flair.renderer import render_showcase
from flair.system import collect_system_info

app = typer.Typer(help="A clear, compact view of your Linux system.", no_args_is_help=False, add_completion=False)
console = Console()


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
    if ctx.invoked_subcommand is not None:
        return
    try:
        config = load_config()
        intro(console, enabled=config["animation"] and not no_animation)
        render_showcase(collect_system_info(), console, show_logo=config["show_logo"])
    except ValueError as exc:
        console.print(f"[red]Configuration error:[/] {exc}")
        raise typer.Exit(code=2) from exc


@app.command()
def system() -> None:
    """Print the system snapshot without the startup animation."""
    try:
        config = load_config()
        render_showcase(collect_system_info(), console, show_logo=config["show_logo"])
    except ValueError as exc:
        console.print(f"[red]Configuration error:[/] {exc}")
        raise typer.Exit(code=2) from exc

