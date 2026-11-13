"""Built-in and user-managed terminal artwork."""

from __future__ import annotations

import re
from pathlib import Path

from flair.config import config_dir

ART: dict[str, str] = {
    "arch": """       /\\
      /  \\
     /    \\
    /      \\
   /   ,,   \\
  /   |  |   \\
 /_-''    ''-_\\""",
    "ubuntu": """        .---.
     _/     \\
    /  .-. .-.
   |  /   Y   \\
   |  \\  |  /
    \\  `-' /
     `----'""",
    "debian": """       .----.
      /  .-.  \\
     |  /   \\  |
     |  \\_.-/  |
      \\     / /
       `---'""",
    "fedora": """       _______
      /  ___  \\
     |  /   \\  |
     |  \\___/  |
      \\_______/
          | |""",
    "manjaro": """     ||||||||||
     |||  ||  |||
     |||  ||  |||
     |||  ||  |||
     ||||||||||""",
    "endeavouros": """       /\\
      /  \\
   __/    \\__
  /          \\
  \\__________/""",
    "kali": """       .--.
      /  _  \\
     |  (_)  |
      \\     /
       `---'""",
    "mint": """       .----.
      /  __  \\
     |  /  \\  |
     | |    | |
      \\____/""",
    "pop-os": """    .--------.
   /  .----.  \\
  |  |      |  |
  |  |      |  |
   \\  '----' /
    '--------'""",
    "opensuse": """      _______
     / ____  \\
    / /    \\  \\
   | |  ()  | |
    \\ \\____/ /
     \\_______/""",
    "nixos": """      /\\_/\\
     /  o o  \\
    ( ==  ^ == )
     )         (
    (           )
   ( (  )   (  ) )""",
    "gentoo": """       .----.
      /      \\
     |  (..)  |
      \\      /
       `----'""",
    "alpine": """      /\
     /  \\
    / / | |
   / ____ \\
  /_/    \\_\\""",
    "void": """    __     __
    \\ \\   / /
     \\ \\ / /
      \\ V /
       \\_/
        | |""",
    "raspberry-pi": """     .----.
    / .--. \\
   | |    | |
   | |    | |
    \\ '--' /
     `----'""",
    "elementary": """       .-.
      /   \\
     |  .-. |
     |  '-' |
      \\   /
       `-'""",
    "solus": """       .-.
      /   \\
     |  .  |
     |  |  |
      \\_|_/""",
    "termux": """     .----.
    / .--. \\
   | |    | |
   | |    | |
    \\ '--' /
     `----'""",
    "windows": """   ┌──────┬──────┐
   │      │      │
   ├──────┼──────┤
   │      │      │
   └──────┴──────┘""",
    "macos": """      .----.
    / .--. \\
   | |    | |
   | |    | |
    \\ '--' /
     `----'""",
}
ART["pop"] = ART["pop-os"]
ART["raspbian"] = ART["raspberry-pi"]


def available_art() -> list[str]:
    """Return built-in and imported logo names."""
    custom = [path.stem for path in art_dir().glob("*.txt")] if art_dir().exists() else []
    return sorted(set(ART) | set(custom))


def art_dir() -> Path:
    """Return the directory used for imported artwork."""
    return config_dir() / "art"


def get_art(name: str) -> str:
    """Read a custom logo first, then fall back to the built-in collection."""
    safe_name = name.casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", safe_name):
        raise ValueError("Logo names may contain letters, numbers, dashes and underscores")
    custom = art_dir() / f"{safe_name}.txt"
    if custom.is_file():
        return custom.read_text(encoding="utf-8").rstrip("\n")
    if safe_name not in ART:
        raise ValueError(f"Unknown logo '{name}'. Use 'flair art list' to see available logos.")
    return ART[safe_name]


def import_art(source: Path, name: str | None = None) -> Path:
    """Copy a non-empty text logo into FLAIR's artwork directory."""
    if not source.is_file():
        raise ValueError(f"Artwork file not found: {source}")
    if source.stat().st_size > 262144:
        raise ValueError("Artwork files must be 256 KiB or smaller")
    text = source.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("Artwork file is empty")
    if len(text.splitlines()) > 1000 or any(len(line) > 400 for line in text.splitlines()):
        raise ValueError("Artwork is too large to display safely in a terminal")
    target_name = (name or source.stem).casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", target_name):
        raise ValueError("Logo names may contain letters, numbers, dashes and underscores")
    art_dir().mkdir(parents=True, exist_ok=True)
    target = art_dir() / f"{target_name}.txt"
    if target.exists():
        raise FileExistsError(f"Logo already exists: {target}")
    target.write_text(text.rstrip("\n") + "\n", encoding="utf-8")
    return target


def remove_art(name: str) -> Path:
    """Remove an imported logo; built-in artwork cannot be deleted."""
    safe_name = name.casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", safe_name):
        raise ValueError("Logo names may contain letters, numbers, dashes and underscores")
    target = art_dir() / f"{safe_name}.txt"
    if not target.is_file():
        raise ValueError(f"No imported logo named '{name}'")
    target.unlink()
    return target
