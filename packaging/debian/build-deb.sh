#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
VERSION=$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$ROOT/pyproject.toml" | head -n 1)
if [[ -z "$VERSION" ]]; then
    echo "Could not read the project version from pyproject.toml" >&2
    exit 1
fi
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python -m build --wheel --no-isolation --outdir "$WORK/dist" "$ROOT"

PACKAGE_ROOT="$WORK/package"
SITE="$PACKAGE_ROOT/usr/lib/python3/dist-packages"
mkdir -p "$SITE" "$PACKAGE_ROOT/DEBIAN"
python - "$WORK/dist"/*.whl "$SITE" <<'PY'
from pathlib import Path
import sys
from zipfile import ZipFile

wheel, destination = Path(sys.argv[1]), Path(sys.argv[2])
with ZipFile(wheel) as archive:
    archive.extractall(destination)
PY

install -Dm755 /dev/stdin "$PACKAGE_ROOT/usr/bin/flair" <<'EOF'
#!/usr/bin/python3
from flair.cli import app

app()
EOF
install -Dm644 "$ROOT/LICENSE" "$PACKAGE_ROOT/usr/share/doc/flair-terminal/copyright"
install -Dm644 /dev/stdin "$PACKAGE_ROOT/usr/share/flair/package-managed" <<'EOF'
Managed by the system package manager.
EOF

cat > "$PACKAGE_ROOT/DEBIAN/control" <<EOF
Package: flair-terminal
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Maintainer: FLAIR Project <noreply@github.com>
Depends: python3 (>= 3.10), python3-rich (>= 13.7), python3-typer (>= 0.12), python3-psutil (>= 5.9), python3-tomli
Homepage: https://github.com/abhay4721/FLAIR
Description: Configurable cross-platform system summary and monitor
 FLAIR displays operating system, hardware, desktop, and resource
 information in the terminal, with configurable layouts and artwork.
EOF

mkdir -p "$ROOT/dist"
DEB="$ROOT/dist/flair-terminal_${VERSION}_all.deb"
if command -v dpkg-deb >/dev/null 2>&1; then
    dpkg-deb --build --root-owner-group "$PACKAGE_ROOT" "$DEB"
else
    for tool in ar tar; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            echo "Install dpkg-deb or provide ar and tar to build the Debian package." >&2
            exit 1
        fi
    done
    printf '2.0\n' > "$WORK/debian-binary"
    tar --xz -cf "$WORK/control.tar.xz" -C "$PACKAGE_ROOT/DEBIAN" .
    tar --xz -cf "$WORK/data.tar.xz" --exclude='./DEBIAN' -C "$PACKAGE_ROOT" .
    ar rcs "$DEB" "$WORK/debian-binary" "$WORK/control.tar.xz" "$WORK/data.tar.xz"
fi
echo "Built $ROOT/dist/flair-terminal_${VERSION}_all.deb"
