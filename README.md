# FLAIR

**Your machine. Your style. Your terminal.**

FLAIR prints a quick, colorful system summary and can keep a live view of resource use open in the terminal. It uses the machine it is running on for hardware values and leaves fields as unavailable when the operating system does not expose them.

## Platforms

FLAIR is built with Python and psutil, so it runs on mainstream Linux distributions, Termux, Windows, and macOS. Linux distribution names are read from `os-release`; Termux is identified as an Android environment. Hardware and desktop details vary by platform: FLAIR uses native tools where available and does not require root or administrator access.

| Platform | Detection notes |
| --- | --- |
| Linux | Reads distribution and kernel details; checks common package managers and Wayland/X11 display tools. |
| Termux | Uses Android properties when available and reports the Termux environment. Some phone GPU and display details may not be exposed. |
| Windows | Uses Windows system APIs for screen size and PowerShell for processor and graphics details when available. |
| macOS | Uses `system_profiler` and `sysctl` for display, graphics and processor details. |

No terminal application can guarantee every hardware field on every OS. Unsupported readings stay marked as unavailable instead of being guessed.

## Install

Install Python 3.10 or newer, then run the commands for your platform from a FLAIR checkout.

### Arch Linux

```sh
sudo pacman -S --needed python python-pipx
pipx ensurepath
pipx install .
```

### Other Linux distributions

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

### Termux

```sh
pkg install python python-psutil
python -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install .
```

Termux provides its Android-compatible `psutil` build as a package; the venv inherits that package while pip installs FLAIR's pure-Python dependencies.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install .
```

### macOS

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

The editable install for development is `python -m pip install -e '.[dev]'`. To run without installing, use `python -m flair` from the project environment.

## Commands

```text
flair                         Show the system summary
flair --no-animation          Skip the startup reveal
flair live                    Open the live resource monitor
flair live --interval 2       Refresh every two seconds
flair system                  Show the summary
flair system cpu               Show processor details
flair system gpu               Show graphics details
flair system memory            Show RAM and swap
flair system disk              Show mounted disk use
flair art                     List built-in and imported logos
flair art list                List logo names
flair art show fedora         Preview a logo
flair art import ./logo.txt   Add a personal logo
flair art remove my-logo      Remove a personal logo
flair themes                  List available themes
flair theme preview nord      Preview a palette
flair theme set nord          Select a palette
flair config                  Print the active configuration
flair config edit             Open it in $EDITOR (Notepad on Windows)
flair config reset            Back it up and restore defaults
flair doctor                  Check the local setup
flair --help                  Show command help
flair --version               Show the installed version
```

The live view exits cleanly with Ctrl+C. NVIDIA utilization, temperature and memory are shown when `nvidia-smi` is available. Other GPU live metrics depend on the driver and are shown as unavailable when FLAIR cannot read them.

## Artwork

The built-in collection includes Arch, EndeavourOS, Ubuntu, Linux Mint, Pop!_OS, Debian, Kali, Fedora, Manjaro, openSUSE, NixOS, Gentoo, Alpine, Void, Solus, elementary OS, Raspberry Pi OS, Termux, Windows and macOS logos. FLAIR picks a logo based on the detected operating system by default. Set a different default in the config file with `logo.name = "fedora"`.

Imported text files are saved under the platform's FLAIR config folder in `art/`. Existing artwork is never overwritten by `art import`. For Arch, an existing `~/.config/fastfetch/arch.txt` is used as the default logo unless a FLAIR custom logo named `arch` is present.

## Themes and configuration

FLAIR creates a per-user `config.toml` on first launch. It uses `$XDG_CONFIG_HOME/flair` when set, `%APPDATA%\flair` on Windows, and `~/Library/Application Support/flair` on macOS.

```toml
theme = "arch-blue"
animation = true
show_logo = true
refresh_interval = 1.0

[logo]
name = "auto"

[display]
show_cpu = true
show_gpu = true
show_memory = true
show_disk = true
show_network = true
show_uptime = true
```

Built-in themes are Arch Blue, Cyberpunk, Matrix, Dracula, Minimal Dark and Nord. To add a theme, create `themes/<name>.toml` inside the FLAIR config folder:

```toml
[colors]
primary = "#56B6FF"
secondary = "#BE8CFF"
accent = "#FF9E64"
text = "#FFFFFF"
muted = "#666666"
success = "#66E880"
warning = "#F7C77E"
error = "#FF8282"
cpu = "#45E3CD"
gpu = "#E485F6"
memory = "#FF75A0"
disk = "#94F0AD"
screen = "#7A9CFF"
wm = "#E5D142"
```

Use six-digit hex colors. `flair theme preview <name>` validates and previews the palette before you select it.

## Development

```sh
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
pytest
```

Tests use mocks for platform and hardware-dependent behavior. They do not require a specific processor or graphics card. FLAIR does not need elevated permissions. No AUR package has been published.

## License

MIT. See [LICENSE](LICENSE).

