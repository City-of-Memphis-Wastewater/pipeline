#!/usr/bin/env bash
set -euo pipefail

PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
PY_VERSION="py${PY_MAJOR}${PY_MINOR}"

EXTRAS=()
for arg in "$@"; do
  case "$arg" in
    (*windows*)  EXTRAS+=("windows") ;;
    (*mpl*)      EXTRAS+=("mpl") ;;
    (*zoneinfo*) EXTRAS+=("zoneinfo") ;;
  esac
done

EXTRAS_STR=""
if [ ${#EXTRAS[@]} -gt 0 ]; then
  EXTRAS_STR="-"$(IFS=- ; echo "${EXTRAS[*]}")
fi

DIST_DIR="dist"
mkdir -p "$DIST_DIR"

# Use poetry-run versions everywhere
POETRY_PEX="poetry run pex"

# Ensure pex exists inside poetry env
if ! poetry run which pex >/dev/null 2>&1; then
  echo "Error: no pex inside Poetry environment. Run:"
  echo "   poetry add --group dev pex"
  exit 1
fi

echo "--- Building fresh wheel ---"
rm -f "$DIST_DIR"/*.whl

if command -v poetry >/dev/null 2>&1; then
  poetry build -f wheel
else
  python3 -m build --wheel --outdir "$DIST_DIR"
fi

latest_wheel=$(ls -t "$DIST_DIR"/*.whl | head -n 1 || true)

if [ -z "$latest_wheel" ]; then
  echo "Error: wheel not generated."
  exit 1
fi

echo "Generated wheel: $latest_wheel"

TMPDIR=$(mktemp -d)
trap 'rm -rf -- "$TMPDIR"' EXIT

unzip -qq "$latest_wheel" -d "$TMPDIR"
META=$(find "$TMPDIR" -name METADATA -print -quit || true)

if [ ! -f "$META" ]; then
  echo "Error reading wheel METADATA."
  exit 1
fi

PKG_NAME=$(awk -F': ' '/^Name:/{print $2}' "$META")
PKG_VERSION=$(awk -F': ' '/^Version:/{print $2}' "$META")

PYZ_PATH="$DIST_DIR/${PKG_NAME}-${PKG_VERSION}-${PY_VERSION}${EXTRAS_STR}.pex"
BAT_PATH="${PYZ_PATH%.pex}-pex.bat"

echo "Output will be: $PYZ_PATH"

echo "--- Building PEX ---"
if $POETRY_PEX "$latest_wheel" \
      --entry-point pipeline.cli:app \
      -o "$PYZ_PATH" \
      --python-shebang "/usr/bin/env python3"
then
  echo "PEX created: $PYZ_PATH"

  echo "@echo off" > "$BAT_PATH"
  echo "set PY_EXE=python.exe" >> "$BAT_PATH"
  echo "set PYZ_FILE=\"$(basename "$PYZ_PATH")\"" >> "$BAT_PATH"
  echo "PUSHD \"%%~dp0\"" >> "$BAT_PATH"
  echo "\"%%PY_EXE%%\" \"%%PYZ_FILE%%\" %%*" >> "$BAT_PATH"
  echo "POPD" >> "$BAT_PATH"
  echo "pause" >> "$BAT_PATH"

  echo "Windows launcher generated: $BAT_PATH"

else
  echo "PEX build failed."
  exit 1
fi
