from flair.system import format_bytes, format_uptime


def test_format_bytes() -> None:
    assert format_bytes(0) == "0 B"
    assert format_bytes(1024) == "1.0 KiB"


def test_format_uptime() -> None:
    assert format_uptime(59) == "0m"
    assert format_uptime(90061) == "1d 1h 1m"

