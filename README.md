# FLAIR

**Your machine. Your style. Your terminal.**

FLAIR is a small Linux terminal showcase for the details you usually look up in several places: the OS, desktop session, processor, graphics adapter, memory and root disk. It reads the current machine at startup, so hardware values are never baked into the output.

The first release focuses on a quick system summary. Live monitoring, themes and artwork management are planned for later releases and are not available yet.

## What it shows

- Distribution, kernel, architecture, host and uptime
- Desktop session, window manager, display server, shell and terminal
- CPU model, core and thread counts, and current frequency when available
- GPU name and NVIDIA driver version when detectable
- Memory, swap and root filesystem use
- An Arch inspired logo and a short startup reveal

Missing details are shown as unavailable. FLAIR does not need root access; NVIDIA details use `nvidia-smi` when it is installed, while other GPU names are detected from sysfs or `lspci`.

## Install

On Arch Linux, install Python and pipx, then install FLAIR from a checkout:

```sh
sudo pacman -S --needed python python-pipx
pipx ensurepath
pipx install .
```

Open a new shell if `flair` is not on your `PATH` yet. For development, use an isolated environment:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Use

```sh
flair                 # animated system showcase
flair --no-animation  # same view without the reveal
flair system          # system view without the reveal
flair --version
flair --help
```

The animation is automatically skipped when output is redirected:

```sh
flair > system.txt
```

## Configuration

On first launch, FLAIR creates `~/.config/flair/config.toml` (or `$XDG_CONFIG_HOME/flair/config.toml`). It will not replace an existing file.

```toml
theme = "arch-blue"
animation = true
show_logo = true

[display]
show_cpu = true
show_memory = true
show_disk = true
```

The current release uses the animation and logo settings. Theme selection and individual display toggles are reserved for the customization phase.

## Development

```sh
pip install -e '.[dev]'
pytest
```

FLAIR targets Python 3.10 and newer and is being developed primarily on Arch Linux, including Hyprland sessions. The system summary also uses portable Linux interfaces where possible. There is no published AUR package yet.

## License

MIT. See [LICENSE](LICENSE).

