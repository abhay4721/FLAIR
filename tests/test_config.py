from pathlib import Path

import pytest

from flair.config import DEFAULT_TOML, load_config


def test_config_is_created_with_defaults(tmp_path: Path) -> None:
    path = tmp_path / "flair" / "config.toml"
    config = load_config(path)

    assert path.read_text() == DEFAULT_TOML
    assert config["theme"] == "arch-blue"
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

