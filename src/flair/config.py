"""Read and initialize FLAIR's TOML configuration."""

from __future__ import annotations

import os
import platform
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
    "refresh_interval": 1.0,
    "logo": {"name": "auto"},
    "display": {"show_cpu": True, "show_gpu": True, "show_memory": True, "show_disk": True, "show_network": True, "show_uptime": True},
}

DEFAULT_TOML = '''theme = "arch-blue"
animation = true
show_logo = true
refresh_interval = 1.0

[logo]
name = "auto"

[display]
show_cpu = true
show_gpu = true
show_memory = true
show_disk = true
show_network = true
show_uptime = true
'''


def config_path() -> Path:
    """Return the platform's normal per-user configuration path."""
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        root = Path(base).expanduser()
    elif platform.system() == "Windows":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif platform.system() == "Darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path.home() / ".config"
    return root / "flair" / "config.toml"


def config_dir() -> Path:
    """Return FLAIR's per-user data and configuration directory."""
    return config_path().parent


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load configuration, creating defaults without replacing an existing file."""
    target = path or config_path()
    try:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8") as config_file:
                config_file.write(DEFAULT_TOML)
    except FileExistsError:
        pass
    except OSError as exc:
        raise ValueError(f"Could not create {target}: {exc}") from exc
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
    logo = values.get("logo", {})
    if not isinstance(logo, dict) or not isinstance(logo.get("name", "auto"), str):
        raise ValueError("'logo.name' must be a string")
    merged = {**DEFAULT_CONFIG, **values}
    merged["display"] = {**DEFAULT_CONFIG["display"], **display}
    merged["logo"] = {**DEFAULT_CONFIG["logo"], **logo}
    interval = merged.get("refresh_interval", 1.0)
    if isinstance(interval, bool) or not isinstance(interval, (int, float)) or not 0.2 <= interval <= 30:
        raise ValueError("'refresh_interval' must be between 0.2 and 30 seconds")
    return merged

