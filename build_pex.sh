#!/usr/bin/env bash
#===============================================================================
# build_pex.sh
#
# Builds a .pex executable from the current Python package.
#  - Generates a fresh wheel via Poetry or python -m build
#  - Extracts metadata (name/version)
#  - Builds a .pex using that wheel
#  - Generates a Windows .bat launcher for convenience
#===============================================================================

set -euo pipefail

#--------------------------------------
# Python version
#--------------------------------------
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
PY_VERSION="py${PY_MAJOR}${PY_MINOR}"

#--------------------------------------
# Parse extras from command-line args
#--------------------------------------
EXTRAS=()
for arg in "$@"; do
  case "$arg" in
    *windows*)  EXTRAS+=("windows") ;;
    *mpl*)      EXTRAS+=("mpl") ;;
    *zoneinfo*) EXTRAS+=("zoneinfo") ;;
  esac
done

EXTRAS_STR=""
if [ ${#EXTRAS[@]} -gt 0 ]; then
  EXTRAS_STR="-"$(IFS=- ; echo "${EXTRAS[*]}")
fi

#--------------------------------------
# Setup
#--------------------------------------
DIST_DIR="dist"
mkdir -p "$DIST_DIR"

#--------------------------------------
# Ensure PEX is available
#--------------------------------------
if ! command -v pex >/dev/null 2>&1; then
  echo "Error: 'pex' not found. Install with 'pip install pex'." >&2
  exit 1
fi

#--------------------------------------
# Build the wheel
#--------------------------------------
echo "--- Forcing generation of new wheel from pyproject.toml ---"
rm -f "$DIST_DIR"/*.whl

if command -v poetry >/dev/null 2>&1; then
  echo "Poetry detected. Building wheel with Poetry..."
  poetry build -f wheel
else
  echo "Poetry not found. Building wheel with 'python3 -m build --wheel'..."
  python3 -m build --wheel --outdir "$DIST_DIR"
fi

latest_wheel=$(ls -t "$DIST_DIR"/*.whl 2>/dev/null | head -n 1 || true)
if [ -z "$latest_wheel" ]; then
  echo "Error: Failed to create a wheel. Aborting."
  exit 1
fi

echo "Generated wheel: $latest_wheel"

#--------------------------------------
# Extract package metadata
#--------------------------------------
TMPDIR=$(mktemp -d)
trap 'rm -rf -- "$TMPDIR"' EXIT

unzip -qq "$latest_wheel" -d "$TMPDIR"
METADATA_FILE=$(find "$TMPDIR" -name 'METADATA' -print -quit || true)
if [ -z "$METADATA_FILE" ] || [ ! -f "$METADATA_FILE" ]; then
  echo "Error: METADATA file not found inside the wheel archive. Aborting."
  exit 1
fi

PKG_NAME=$(awk -F': ' '/^Name:/{print $2; exit}' "$METADATA_FILE")
PKG_VERSION=$(awk -F': ' '/^Version:/{print $2; exit}' "$METADATA_FILE")
METADATA_VERSION=$(awk -F': ' '/^Metadata-Version:/{print $2; exit}' "$METADATA_FILE")

echo "PKG_NAME: $PKG_NAME"
echo "PKG_VERSION: $PKG_VERSION"
echo "METADATA_VERSION: $METADATA_VERSION"

#--------------------------------------
# Get PEX version (for info only)
#--------------------------------------
PEX_VERSION=$(pex --version 2>/dev/null | grep -Eo '[0-9]+(\.[0-9]+)*' || echo "unknown")
echo "PEX_VERSION: $PEX_VERSION"

#--------------------------------------
# Define output paths
#--------------------------------------
PYZ_PATH="$DIST_DIR/${PKG_NAME}-${PKG_VERSION}-${PY_VERSION}${EXTRAS_STR}.pex"
BAT_PATH="${PYZ_PATH%.pex}-pex.bat"

echo "Output .pex will be: $PYZ_PATH"
echo "Output launcher .bat will be: $BAT_PATH"

#--------------------------------------
# Build PEX
#--------------------------------------
echo "Building .pex from wheel: $latest_wheel"
if pex "$latest_wheel" \
    --entry-point pipeline.cli:app \
    -o "$PYZ_PATH" \
    --python-shebang "/usr/bin/env python3"; then

  echo "Successfully created $PYZ_PATH"

  #--------------------------------------
  # Generate Windows launcher (.bat)
  #--------------------------------------
  echo "@echo off" > "$BAT_PATH"
  echo "REM Windows launcher for $(basename "$PYZ_PATH")" >> "$BAT_PATH"
  echo "set PY_EXE=python.exe" >> "$BAT_PATH"
  echo "set PYZ_FILE=\"$(basename "$PYZ_PATH")\"" >> "$BAT_PATH"
  echo "PUSHD \"%%~dp0\"" >> "$BAT_PATH"
  echo "\"%%PY_EXE%%\" \"%%PYZ_FILE%%\" %%*" >> "$BAT_PATH"
  echo "POPD" >> "$BAT_PATH"
  echo "pause" >> "$BAT_PATH"

  echo "Generated Windows launcher: $BAT_PATH"

else
  echo "Error: pex build failed."
  exit 1
fi
