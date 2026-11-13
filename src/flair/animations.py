"""Small startup cue, skipped automatically for redirected output."""

import time

from rich.console import Console


def intro(console: Console, enabled: bool = True) -> None:
    """Show a short reveal when output is an interactive terminal."""
    if not enabled or not console.is_terminal:
        return
    for label in ("F", "FL", "FLA", "FLAI", "FLAIR"):
        console.print(f"[bold #1793D1]{label}[/]", justify="center")
        time.sleep(0.045)
    console.print()

