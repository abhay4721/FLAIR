from pathlib import Path

import pytest

from flair.config import DEFAULT_TOML, load_config, save_style_choice
import flair.config as config_module


def test_config_is_created_with_defaults(tmp_path: Path) -> None:
    path = tmp_path / "flair" / "config.toml"
    config = load_config(path)

    assert path.read_text() == DEFAULT_TOML
    assert config["theme"] == "arch-blue"
    assert config["style"] == "fastfetch"
    assert config["logo"]["padding"]["right"] == 4
    assert config["display"]["show_cpu"] is True


def test_existing_config_is_preserved(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('theme = "custom"\nshow_logo = false\n')

    config = load_config(path)

    assert config["theme"] == "custom"
    assert config["show_logo"] is False
    assert path.read_text() == 'theme = "custom"\nshow_logo = false\n'


def test_invalid_value_has_useful_error(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("animation = 5\n")

    with pytest.raises(ValueError, match="animation"):
        load_config(path)


def test_config_path_uses_windows_roaming_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.platform, "system", lambda: "Windows")
    monkeypatch.setenv("APPDATA", "C:/Users/test/AppData/Roaming")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert str(config_module.config_path()).endswith("flair/config.toml")


def test_config_path_uses_macos_application_support(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.platform, "system", lambda: "Darwin")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert config_module.config_path().parts[-3:] == ("Application Support", "flair", "config.toml")


def test_invalid_module_name_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('modules = ["made-up"]\n')
    with pytest.raises(ValueError, match="supported module"):
        load_config(path)


def test_saving_style_preserves_existing_settings(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('animation = false\nseparator = " | "\n')
    save_style_choice("neofetch", path)
    saved = path.read_text()
    assert 'style = "neofetch"' in saved
    assert "animation = false" in saved
    assert 'separator = " | "' in saved

