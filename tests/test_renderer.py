from io import StringIO

from rich.console import Console

from flair.renderer import render_showcase
from flair.system import SystemInfo


def sample_info() -> SystemInfo:
    return SystemInfo(
        distribution="Example Linux",
        os_version="1",
        os_age="Unknown",
        packages="Unknown",
        kernel="test-kernel",
        architecture="x86_64",
        hostname="test-host",
        username="tester",
        uptime_seconds=3600,
        desktop="Desktop",
        window_manager="WM",
        display_server="Wayland",
        shell="zsh",
        terminal="kitty",
        resolution="1920x1080 @ 60Hz",
        cpu="Test CPU",
        physical_cores=4,
        logical_threads=8,
        cpu_frequency_mhz=2400,
        gpu="Test GPU",
        gpu_driver="Unknown",
        memory_total=16 * 1024**3,
        memory_used=8 * 1024**3,
        memory_percent=50,
        swap_total=2 * 1024**3,
        swap_used=0,
        disk_total=100 * 1024**3,
        disk_used=25 * 1024**3,
        disk_percent=25,
        extra_disks=(),
    )


def test_showcase_uses_configured_theme_and_runtime_values() -> None:
    output = StringIO()
    render_showcase(sample_info(), Console(file=output, width=120), show_logo=False)

    rendered = output.getvalue()
    assert "tester@test-host" in rendered
    assert "Example Linux" in rendered
    assert "Test CPU @2.4GHz" in rendered
    assert "Test GPU" in rendered
    assert "1920x1080 @ 60Hz" in rendered


def test_display_settings_hide_selected_hardware_rows() -> None:
    output = StringIO()
    render_showcase(sample_info(), Console(file=output, width=120), show_logo=False, display={"show_cpu": False, "show_gpu": False})

    rendered = output.getvalue()
    assert "CPU" not in rendered
    assert "Test GPU" not in rendered
