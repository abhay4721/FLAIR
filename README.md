# FLAIR

**Your machine. Your style. Your terminal.**

FLAIR is a configurable system summary and live monitor. Choose from default, detailed, classic, and minimal layouts, then adjust the modules, colors, artwork, and spacing to suit your terminal. Hardware values come from the running machine; unavailable fields are left unknown instead of guessed.

FLAIR began as a personal project to provide its author with a system information summary tailored to their own machines and terminal preferences. It is inspired by the wider tradition of terminal-based system information tools, while its features and configuration are developed specifically for FLAIR.

## Platforms

FLAIR is built with Python and psutil, so it runs on mainstream Linux distributions, Termux, Windows, and macOS. Linux distribution names are read from `os-release`; Termux is identified as an Android environment. Hardware and desktop details vary by platform: FLAIR uses native tools where available and does not require root or administrator access.

| Platform | Detection notes |
| --- | --- |
| Linux | Reads distribution and kernel details; checks common package managers and Wayland/X11 display tools. |
| Termux | Uses Android properties when available and reports the Termux environment. Some phone GPU and display details may not be exposed. |
| Windows | Uses Windows system APIs for screen size and PowerShell for processor and graphics details when available. |
| macOS | Uses `system_profiler` and `sysctl` for display, graphics and processor details. |

No terminal application can guarantee every hardware field on every OS. Unsupported readings stay marked as unavailable instead of being guessed.

## Native Linux packages

On Debian or Ubuntu releases whose repositories provide the listed Python dependency versions, install the build tools and create a local `.deb` package:

```sh
sudo apt install dpkg-dev python3-build python3-hatchling
./packaging/debian/build-deb.sh
sudo apt install ./dist/flair-terminal_0.1.0_all.deb
```

On Arch Linux, create and install a pacman package from the checkout:

```sh
cd packaging/arch
makepkg -si
```

Both packages declare their runtime dependencies and mark FLAIR as system-managed. Updates then come through `apt` or `pacman`; FLAIR's own updater stays out of the way.

## Install

Install Python 3.10 or newer, clone the project, then run the commands for your platform. `pip install .` builds and installs FLAIR from the checkout.

```sh
git clone https://github.com/abhay4721/FLAIR.git
cd FLAIR
```

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

The platform instructions above install FLAIR as a built package; they do not run it directly from the checkout. For development, `python -m pip install -e '.[dev]'` creates an editable install that follows source changes. To run without installing, use `python -m flair` from the project environment.

### Build distributable packages

```sh
python -m pip install build
python -m build
```

This creates a wheel and source archive in `dist/`. Install the wheel with `python -m pip install dist/flair_terminal-<version>-py3-none-any.whl` or `pipx install dist/flair_terminal-<version>-py3-none-any.whl`.

## Commands

```text
flair                         Show the system summary
flair --quiet-start            Hide the brief startup status
flair --no-update              Skip the automatic update check for this run
flair --style detailed         Use the detailed module order
flair --style classic          Use the classic module order
flair --style minimal          Use the compact module order
flair style list               List layout presets
flair style set detailed       Save a preset as the default
flair --show architecture,host Add modules to the current preset
flair --hide packages,gpu      Hide modules for this run
flair --logo ubuntu            Choose a built-in logo
flair --logo-file ./logo.txt   Use a logo file directly
flair --no-logo                Hide the logo
flair --theme nord             Override the theme for this run
flair --layout top             Put the logo above the information
flair --layout side-by-side    Keep logo and information on one row
flair --separator " : "        Change the key/value separator
flair --key-width 18           Set the module label width
flair --color never            Disable terminal colors
flair --json                   Print a JSON system snapshot
flair --list-modules           List modules for --show/--hide and config
flair --config ./work.toml     Read an alternate config file
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

Imported text files are saved under the platform's FLAIR config folder in `art/`. Existing artwork is never overwritten by `art import`.

## Themes and configuration

FLAIR creates a per-user `config.toml` on first launch. It uses `$XDG_CONFIG_HOME/flair` when set, `%APPDATA%\flair` on Windows, and `~/Library/Application Support/flair` on macOS.

```toml
theme = "arch-blue"
style = "default"
auto_update = true
startup_status = true
show_logo = true
refresh_interval = 1.0
separator = "  "
layout = "auto"
color = "auto"
key_width = 14
modules = []

[logo]
name = "auto"
path = ""

[logo.padding]
top = 2
left = 2
right = 4

[display]
show_cpu = true
show_gpu = true
show_memory = true
show_disk = true
show_network = true
show_uptime = true
```

`modules` can hold an ordered list such as `modules = ["title", "separator", "os", "kernel", "cpu", "memory", "disk"]`. An empty list uses the selected `style` preset. Per-run `--show` and `--hide` options layer on top without editing the file. `layout = "auto"` switches to a top-down logo on narrow terminals. `logo.path` can point to a text logo; `logo.name` selects a built-in or imported logo when no file is set.

Available modules are `title`, `separator`, `os`, `os_age`, `kernel`, `packages`, `host`, `uptime`, `shell`, `terminal`, `wm`, `de`, `display_server`, `architecture`, `cpu`, `cores`, `frequency`, `gpu`, `gpu_driver`, `screen`, `memory`, `swap`, `disk`, and `colors`. For example: `flair --style detailed --show architecture,terminal --hide colors`.

Configuration can also control `auto_update`, `startup_status`, refresh interval, terminal color mode, key width, key/value separator, logo visibility, built-in or custom artwork, logo padding, per-hardware display toggles, and an ordered module list. FLAIR checks the project’s main branch when its summary starts. If a newer revision is available, it builds and installs it, then restarts to display the summary using that revision. Git is needed for automatic updates. Set `auto_update = false` or pass `--no-update` to skip the check. The `--config` option selects a separate TOML file, while `--show` and `--hide` make one-run adjustments.

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

