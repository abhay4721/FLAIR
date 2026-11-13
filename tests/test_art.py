from pathlib import Path

import pytest

import flair.art as art


def test_builtin_collection_has_multiple_platforms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(art, "art_dir", lambda: tmp_path / "art")
    names = art.available_art()
    assert {"arch", "ubuntu", "fedora", "endeavouros", "mint", "termux", "windows", "macos"}.issubset(names)
    assert art.get_art("pop") == art.get_art("pop-os")
    assert art.get_art("raspbian") == art.get_art("raspberry-pi")


def test_custom_art_import_and_no_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "logo.txt"
    source.write_text("  /\\\n /__\\\n")
    monkeypatch.setattr(art, "art_dir", lambda: tmp_path / "art")

    destination = art.import_art(source, "my-logo")
    assert art.get_art("my-logo") == source.read_text().rstrip("\n")
    with pytest.raises(FileExistsError):
        art.import_art(source, "my-logo")
    assert destination.exists()


def test_builtin_art_cannot_be_removed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(art, "art_dir", lambda: tmp_path / "art")
    with pytest.raises(ValueError, match="No imported logo"):
        art.remove_art("arch")
