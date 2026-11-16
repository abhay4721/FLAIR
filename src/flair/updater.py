"""Check the upstream branch and install newer FLAIR revisions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from rich.console import Console

from flair.config import config_dir

REPOSITORY = "https://github.com/abhay4721/FLAIR.git"
BRANCH = "main"
CHECKOUT = Path(__file__).resolve().parents[2]
STATE_FILE = "update-state.json"
PACKAGE_MANAGER_MARKER = Path("/usr/share/flair/package-managed")


class UpdateError(RuntimeError):
    """Raised when the upstream version cannot be installed safely."""


def _run(command: list[str], *, cwd: Path | None = None, timeout: int = 15) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise UpdateError(str(exc)) from exc


def _state_path() -> Path:
    return config_dir() / STATE_FILE


def _read_installed_revision(path: Path) -> str:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        revision = state.get("revision", "")
        return revision if isinstance(revision, str) else ""
    except (OSError, ValueError, AttributeError):
        return ""


def _write_installed_revision(path: Path, revision: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"revision": revision}) + "\n", encoding="utf-8")
    temporary.replace(path)


def _remote_revision() -> str:
    result = _run(["git", "ls-remote", REPOSITORY, f"refs/heads/{BRANCH}"], timeout=12)
    if result.returncode:
        raise UpdateError("Could not contact the upstream repository")
    revision = result.stdout.split(maxsplit=1)[0] if result.stdout.strip() else ""
    if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision.lower()):
        raise UpdateError("The upstream repository returned an invalid revision")
    return revision


def _checkout_revision() -> str | None:
    if not (CHECKOUT / ".git").exists():
        return None
    branch = _run(["git", "branch", "--show-current"], cwd=CHECKOUT)
    if branch.returncode or branch.stdout.strip() != BRANCH:
        return "protected"
    status = _run(["git", "status", "--porcelain"], cwd=CHECKOUT)
    if status.returncode or status.stdout.strip():
        return "protected"
    revision = _run(["git", "rev-parse", "HEAD"], cwd=CHECKOUT)
    if revision.returncode:
        raise UpdateError("Could not read the local checkout revision")
    return revision.stdout.strip()


def _install(source: str, *, cwd: Path | None = None) -> None:
    result = _run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "--no-deps", "--force-reinstall", source],
        cwd=cwd,
        timeout=300,
    )
    if result.returncode:
        details = (result.stderr or result.stdout).strip().splitlines()
        reason = details[-1] if details else "package installation failed"
        raise UpdateError(reason)


def check_and_update(console: Console | None = None) -> bool:
    """Install the latest main revision, returning whether a restart is needed.

    A local checkout is updated only when it is clean, on ``main``, and can be
    fast-forwarded. Installed copies use pip's Git support to build the wheel.
    """
    # Native package managers own upgrades for system packages.
    if PACKAGE_MANAGER_MARKER.is_file():
        return False
    console = console or Console()
    state_path = _state_path()
    local_revision = _checkout_revision()
    if local_revision == "protected":
        return False

    if local_revision is not None:
        fetched = _run(["git", "fetch", "--quiet", REPOSITORY, BRANCH], cwd=CHECKOUT, timeout=12)
        if fetched.returncode:
            raise UpdateError("Could not fetch the latest project revision")
        remote = _run(["git", "rev-parse", "FETCH_HEAD"], cwd=CHECKOUT)
        if remote.returncode:
            raise UpdateError("Could not read the upstream revision")
        remote_revision = remote.stdout.strip()
        if local_revision == remote_revision:
            if _read_installed_revision(state_path) != remote_revision:
                _write_installed_revision(state_path, remote_revision)
            return False
        ancestry = _run(
            ["git", "merge-base", "--is-ancestor", local_revision, remote_revision],
            cwd=CHECKOUT,
        )
        if ancestry.returncode:
            # Keep local commits and diverged histories intact.
            return False
        merged = _run(["git", "merge", "--ff-only", "FETCH_HEAD"], cwd=CHECKOUT)
        if merged.returncode:
            raise UpdateError("Could not safely fast-forward the local checkout")
        _install(str(CHECKOUT), cwd=CHECKOUT)
    else:
        remote_revision = _remote_revision()
        if _read_installed_revision(state_path) == remote_revision:
            return False
        source = f"git+{REPOSITORY}@{remote_revision}"
        _install(source)

    _write_installed_revision(state_path, remote_revision)
    console.print(f"[green]FLAIR updated to {remote_revision[:12]}; restarting…[/]")
    return True
