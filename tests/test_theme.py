from pathlib import Path

import pytest

import flair.theme as theme


def test_all_builtin_palettes_have_required_colors() -> None:
    for name in theme.THEMES:
        colors = theme.load_theme(name)
        assert set(theme.REQUIRED_COLORS).issubset(colors)
        assert colors["title_host"].startswith("#")


def test_invalid_custom_theme_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(theme, "themes_dir", lambda: tmp_path)
    (tmp_path / "broken.toml").write_text('[colors]\nprimary = "blue"\n')
    with pytest.raises(ValueError, match="invalid"):
        theme.load_theme("broken")


def test_theme_selection_preserves_other_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text('startup_status = false\n\n[display]\nshow_cpu = false\n')
    path = theme.save_theme_choice("nord", config_file)
    contents = path.read_text()
    assert 'theme = "nord"' in contents
    assert "startup_status = false" in contents
    assert "show_cpu = false" in contents
