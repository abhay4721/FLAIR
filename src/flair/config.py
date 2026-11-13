"""Read and initialize FLAIR's TOML configuration."""

from __future__ import annotations

import os
import platform
import re
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

DEFAULT_CONFIG: dict[str, Any] = {
    "theme": "arch-blue",
    "style": "default",
    "auto_update": True,
    "startup_status": True,
    "show_logo": True,
    "refresh_interval": 1.0,
    "separator": "  ",
    "layout": "auto",
    "color": "auto",
    "key_width": 14,
    "modules": [],
    "logo": {"name": "auto", "path": "", "padding": {"top": 2, "left": 2, "right": 4}},
    "display": {"show_cpu": True, "show_gpu": True, "show_memory": True, "show_disk": True, "show_network": True, "show_uptime": True},
}

DEFAULT_TOML = '''theme = "arch-blue"
style = "default"
auto_update = true
startup_status = true
show_logo = true
refresh_interval = 1.0
separator = "  "
layout = "auto"
color = "auto"
key_width = 14
modules = []

[logo]
name = "auto"
path = ""

[logo.padding]
top = 2
left = 2
right = 4

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


def write_root_choice(path: Path, key: str, value: str) -> Path:
    """Update a simple root-level choice without rewriting other TOML settings."""
    if key not in {"theme", "style"} or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value):
        raise ValueError("Invalid configuration choice")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_TOML, encoding="utf-8")
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    root_lines: list[str] = []
    section_lines: list[str] = []
    in_section = False
    for line in lines:
        if line.lstrip().startswith("["):
            in_section = True
        (section_lines if in_section else root_lines).append(line)
    root = "".join(root_lines)
    pattern = re.compile(rf'(?m)^([ \t]*{key}[ \t]*=[ \t]*)"[^"]*"')
    if pattern.search(root):
        root = pattern.sub(rf'\g<1>"{value}"', root, count=1)
    else:
        root = f'{key} = "{value}"\n' + root
    path.write_text(root + "".join(section_lines), encoding="utf-8")
    return path


def save_style_choice(style: str, path: Path | None = None) -> Path:
    """Persist a built-in output preset without discarding other settings."""
    if style not in {"default", "detailed", "classic", "minimal"}:
        raise ValueError("Style must be default, detailed, classic, or minimal")
    return write_root_choice(path or config_path(), "style", style)


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

    for key in ("theme", "style", "layout", "color", "separator"):
        if not isinstance(values.get(key, DEFAULT_CONFIG.get(key, "")), str):
            raise ValueError(f"'{key}' must be a string")
    if values.get("style", "default") not in {"default", "detailed", "classic", "minimal"}:
        raise ValueError("'style' must be default, detailed, classic, or minimal")
    if values.get("layout", "auto") not in {"auto", "side-by-side", "top"}:
        raise ValueError("'layout' must be auto, side-by-side, or top")
    if values.get("color", "auto") not in {"auto", "always", "never"}:
        raise ValueError("'color' must be auto, always, or never")
    if len(values.get("separator", "  ")) > 10:
        raise ValueError("'separator' must be 10 characters or fewer")
    key_width = values.get("key_width", 14)
    if isinstance(key_width, bool) or not isinstance(key_width, int) or not 4 <= key_width <= 40:
        raise ValueError("'key_width' must be between 4 and 40")
    modules = values.get("modules", [])
    allowed_modules = {
        "title", "separator", "os", "os_age", "kernel", "packages", "host", "uptime", "shell", "terminal",
        "wm", "de", "display_server", "architecture", "cpu", "cores", "frequency", "gpu", "gpu_driver",
        "screen", "memory", "swap", "disk", "colors",
    }
    if not isinstance(modules, list) or any(not isinstance(module, str) or module not in allowed_modules for module in modules):
        raise ValueError("'modules' must be a list of supported module names")
    for key in ("auto_update", "startup_status", "show_logo"):
        if not isinstance(values.get(key, DEFAULT_CONFIG[key]), bool):
            raise ValueError(f"'{key}' must be true or false")
    display = values.get("display", {})
    if not isinstance(display, dict) or any(not isinstance(value, bool) for value in display.values()):
        raise ValueError("'display' must contain true/false values")
    logo = values.get("logo", {})
    if not isinstance(logo, dict) or not isinstance(logo.get("name", "auto"), str) or not isinstance(logo.get("path", ""), str):
        raise ValueError("'logo.name' and 'logo.path' must be strings")
    padding = logo.get("padding", {})
    if not isinstance(padding, dict) or any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 40 for v in padding.values()):
        raise ValueError("'logo.padding' must contain integer values from 0 to 40")
    merged = {**DEFAULT_CONFIG, **values}
    merged["display"] = {**DEFAULT_CONFIG["display"], **display}
    merged["logo"] = {**DEFAULT_CONFIG["logo"], **logo}
    merged["logo"]["padding"] = {**DEFAULT_CONFIG["logo"]["padding"], **padding}
    interval = merged.get("refresh_interval", 1.0)
    if isinstance(interval, bool) or not isinstance(interval, (int, float)) or not 0.2 <= interval <= 30:
        raise ValueError("'refresh_interval' must be between 0.2 and 30 seconds")
    return merged

