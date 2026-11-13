from unittest.mock import patch

from flair.system import _resolution, format_bytes, format_uptime


def test_format_bytes() -> None:
    assert format_bytes(0) == "0 B"
    assert format_bytes(1024) == "1.0 KiB"


def test_format_uptime() -> None:
    assert format_uptime(59) == "0m"
    assert format_uptime(90061) == "1d 1h 1m"


def test_hyprland_resolution_includes_refresh_rate() -> None:
    with patch("flair.system._run", return_value='[{"focused": true, "width": 1920, "height": 1080, "refreshRate": 144.0}]'):
        assert _resolution() == "1920x1080 @ 144Hz"


def test_wlroots_resolution_includes_refresh_rate() -> None:
    def fake_run(command: list[str]) -> str:
        if command[0] == "wlr-randr":
            return "DP-1\n  2560x1440 px, 165.000000 Hz (current, preferred)"
        return ""

    with patch("flair.system._run", side_effect=fake_run):
        assert _resolution() == "2560x1440 @ 165.000000Hz"


def test_xrandr_resolution_includes_active_refresh_rate() -> None:
    def fake_run(command: list[str]) -> str:
        if command[0] == "hyprctl" or command[0] == "wlr-randr":
            return ""
        return "eDP-1 connected primary 1920x1080+0+0 60.00*+ 48.00\n"

    with patch("flair.system._run", side_effect=fake_run):
        assert _resolution() == "1920x1080 @ 60.00Hz"

