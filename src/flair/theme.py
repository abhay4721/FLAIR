"""Built-in palettes and validated TOML themes."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from flair.config import config_dir, config_path, write_root_choice

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

THEMES: dict[str, dict[str, str]] = {
    "arch-blue": {"primary": "#56B6FF", "secondary": "#BE8CFF", "accent": "#FF9E64", "text": "#FFFFFF", "muted": "#666666", "success": "#66E880", "warning": "#F7C77E", "error": "#FF8282", "title_host": "#FFACF3", "cpu": "#45E3CD", "gpu": "#E485F6", "memory": "#FF75A0", "disk": "#94F0AD", "screen": "#7A9CFF", "wm": "#E5D142"},
    "cyberpunk": {"primary": "#FF00D4", "secondary": "#00E5FF", "accent": "#FFFF00", "text": "#F7F4FF", "muted": "#A29AB8", "success": "#00FF9C", "warning": "#FFC857", "error": "#FF4D6D", "cpu": "#00E5FF", "gpu": "#FF00D4", "memory": "#FF4D6D", "disk": "#00FF9C", "screen": "#FFFF00", "wm": "#A855F7"},
    "matrix": {"primary": "#00FF41", "secondary": "#008F11", "accent": "#7CFF7C", "text": "#E4FFE9", "muted": "#4D8F5A", "success": "#00FF41", "warning": "#C8FF00", "error": "#FF5252", "cpu": "#00FF41", "gpu": "#7CFF7C", "memory": "#B5FF6B", "disk": "#00C853", "screen": "#69F0AE", "wm": "#AEEA00"},
    "dracula": {"primary": "#BD93F9", "secondary": "#8BE9FD", "accent": "#FF79C6", "text": "#F8F8F2", "muted": "#6272A4", "success": "#50FA7B", "warning": "#F1FA8C", "error": "#FF5555", "cpu": "#8BE9FD", "gpu": "#FF79C6", "memory": "#FF5555", "disk": "#50FA7B", "screen": "#BD93F9", "wm": "#F1FA8C"},
    "minimal-dark": {"primary": "#D8DEE9", "secondary": "#A3AAB8", "accent": "#88C0D0", "text": "#ECEFF4", "muted": "#7B8494", "success": "#A3BE8C", "warning": "#EBCB8B", "error": "#BF616A", "cpu": "#88C0D0", "gpu": "#B48EAD", "memory": "#D08770", "disk": "#A3BE8C", "screen": "#81A1C1", "wm": "#EBCB8B"},
    "nord": {"primary": "#88C0D0", "secondary": "#81A1C1", "accent": "#B48EAD", "text": "#ECEFF4", "muted": "#7B8494", "success": "#A3BE8C", "warning": "#EBCB8B", "error": "#BF616A", "cpu": "#88C0D0", "gpu": "#B48EAD", "memory": "#D08770", "disk": "#A3BE8C", "screen": "#81A1C1", "wm": "#EBCB8B"},
}

REQUIRED_COLORS = ("primary", "secondary", "accent", "text", "muted", "success", "warning", "error", "cpu", "gpu", "memory", "disk", "screen", "wm")
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def themes_dir() -> Path:
    """Return the per-user theme directory."""
    return config_dir() / "themes"


def list_themes() -> list[str]:
    """Return built-in and installed user theme names."""
    custom = [path.stem for path in themes_dir().glob("*.toml")] if themes_dir().exists() else []
    return sorted(set(THEMES) | set(custom))


def load_theme(name: str) -> dict[str, str]:
    """Load a built-in palette or a validated user TOML theme."""
    key = name.casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", key):
        raise ValueError("Theme names may contain letters, numbers, dashes and underscores")
    if key in THEMES:
        result = dict(THEMES[key])
        result.setdefault("title_host", result["secondary"])
        return result
    path = themes_dir() / f"{key}.toml"
    try:
        with path.open("rb") as theme_file:
            values: dict[str, Any] = tomllib.load(theme_file)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"Unknown or invalid theme '{name}': {exc}") from exc
    colors = values.get("colors", values)
    if not isinstance(colors, dict):
        raise ValueError(f"Theme '{name}' must define its colors as a TOML table")
    missing = [field for field in REQUIRED_COLORS if field not in colors]
    invalid = [field for field in REQUIRED_COLORS if not isinstance(colors.get(field), str) or not COLOR_PATTERN.fullmatch(colors[field])]
    if "title_host" in colors and (not isinstance(colors["title_host"], str) or not COLOR_PATTERN.fullmatch(colors["title_host"])):
        invalid.append("title_host")
    if missing or invalid:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if invalid:
            details.append("invalid hex colors: " + ", ".join(invalid))
        raise ValueError(f"Theme '{name}' is invalid ({'; '.join(details)})")
    result = {field: colors[field] for field in REQUIRED_COLORS}
    result["title_host"] = colors.get("title_host", colors["secondary"])
    return result


def save_theme_choice(name: str, config_file: Path | None = None) -> Path:
    """Select a known theme while preserving the rest of the TOML file."""
    load_theme(name)
    path = config_file or config_path()
    return write_root_choice(path, "theme", name.casefold())
