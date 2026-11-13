"""Read and initialize FLAIR's TOML configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

DEFAULT_CONFIG: dict[str, Any] = {
    "theme": "arch-blue",
    "animation": True,
    "show_logo": True,
    "display": {"show_cpu": True, "show_memory": True, "show_disk": True},
}

DEFAULT_TOML = '''theme = "arch-blue"
animation = true
show_logo = true

[display]
show_cpu = true
show_memory = true
show_disk = true
'''


def config_path() -> Path:
    """Return the user's configuration path, following XDG when set."""
    base = os.environ.get("XDG_CONFIG_HOME")
    return Path(base).expanduser() / "flair" / "config.toml" if base else Path.home() / ".config" / "flair" / "config.toml"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load configuration, creating defaults without replacing an existing file."""
    target = path or config_path()
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("x", encoding="utf-8") as config_file:
                config_file.write(DEFAULT_TOML)
        except FileExistsError:
            pass
    try:
        with target.open("rb") as config_file:
            values = tomllib.load(config_file)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"Could not read {target}: {exc}") from exc

    if not isinstance(values.get("theme", "arch-blue"), str):
        raise ValueError("'theme' must be a string")
    for key in ("animation", "show_logo"):
        if not isinstance(values.get(key, DEFAULT_CONFIG[key]), bool):
            raise ValueError(f"'{key}' must be true or false")
    display = values.get("display", {})
    if not isinstance(display, dict) or any(not isinstance(value, bool) for value in display.values()):
        raise ValueError("'display' must contain true/false values")
    merged = {**DEFAULT_CONFIG, **values}
    merged["display"] = {**DEFAULT_CONFIG["display"], **display}
    return merged

