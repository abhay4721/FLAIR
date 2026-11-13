from io import StringIO

from rich.console import Console

from flair.renderer import modules_for, render_showcase
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
        host_model="Test workstation",
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


def test_neofetch_and_screenfetch_presets_are_available() -> None:
    assert "host" in modules_for("neofetch")
    assert "de" in modules_for("screenfetch")
    assert modules_for("minimal") == ["title", "os", "cpu", "memory", "disk", "uptime"]


def test_custom_module_order_and_separator() -> None:
    output = StringIO()
    render_showcase(
        sample_info(),
        Console(file=output, width=120),
        show_logo=False,
        modules=["title", "os", "cpu"],
        separator=" : ",
    )
    rendered = output.getvalue()
    assert "Example Linux" in rendered
    assert " : Test CPU @2.4GHz" in rendered
    assert "test-kernel" not in rendered


def test_custom_module_order_is_preserved() -> None:
    output = StringIO()
    render_showcase(
        sample_info(),
        Console(file=output, width=120),
        show_logo=False,
        modules=["os", "title", "separator", "kernel"],
    )
    rendered = output.getvalue()
    assert rendered.index("Example Linux") < rendered.index("tester@test-host")
    assert rendered.index("tester@test-host") < rendered.index("────────") < rendered.index("test-kernel")
