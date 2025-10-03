#!/bin/bash

# Strict mode for bash scripts, to fail early from malformed var names or non-zero status returns
set -euo pipefail

# --- Determine Python version for the dynamic .pyz filename ---
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
PY_VERSION="py${PY_MAJOR}${PY_MINOR}"

# Keep only major.minor.patch (first three numeric groups)
#PKG_VERSION=$(echo "$PKG_VERSION" | grep -oE '^[0-9]+\.[0-9]+\.[0-9]+')

# --- Detect extras to include in filename ---
EXTRAS=()
if [[ "$@" == *"windows"* ]]; then EXTRAS+=("windows"); fi
if [[ "$@" == *"mpl"* ]]; then EXTRAS+=("mpl"); fi
if [[ "$@" == *"zoneinfo"* ]]; then EXTRAS+=("zoneinfo"); fi

EXTRAS_STR=""
if [ ${#EXTRAS[@]} -gt 0 ]; then
    EXTRAS_STR="-"$(IFS=- ; echo "${EXTRAS[*]}")
fi

DIST_DIR="dist"
mkdir -p "$DIST_DIR"
# Initialize exit code in case something goes wrong
exit_code=1

# --- Assess if the wheel exists yet, and if so, identfy it  ---
latest_wheel=$(ls -t dist/*.whl 2>/dev/null | head -n 1)

# --- Sane fallbacks to build .whl if it does not exist yet ---
# If no wheel exists, build one from, trying poetry first, and then build --wheel if poetry is fails

# Try using poetry for the build if no .whl exists in ./dist/if [ -z "$latest_wheel" ]; then
if [ -z "$latest_wheel" ]; then
    echo "No wheel found. Trying Poetry..."
    if command -v poetry >/dev/null 2>&1; then
        poetry build -f wheel
        latest_wheel=$(ls -t dist/*.whl | head -n 1)
    fi
fi

# This will hit if running on Termux or another non-poetry situation.
if [ -z "$latest_wheel" ]; then
    echo "No wheel found. Building wheel with 'python3 -m build --wheel'..."
    python3 -m build --wheel --outdir dist
    latest_wheel=$(ls -t dist/*.whl | head -n 1)
fi

# This infers that a wheel is completely necessary to build. 
# Shiv can build a zippapp .pyz  with just the requirements.txt,
#  but building the wheel is necessary for assessing the metada version,
#  which is necessary to strip the extra version name from the export file.
if [ -z "$latest_wheel" ]; then
    echo "Error: could not create a wheel. Aborting."
    exit 1
fi

# ------ End Fallback .whl Generation

# --- Assess the latest_wheel for the Metadata version, Package version, and Package name
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
unzip "$latest_wheel" -d "$TMPDIR"
METADATA_FILE=$(find "$TMPDIR" -name 'METADATA' -print -quit)
METADATA_VERSION=$(grep '^Metadata-Version:' "$METADATA_FILE" | awk '{print $2}')
PKG_VERSION=$(grep '^Version:' "$METADATA_FILE" | awk '{print $2}')
PKG_NAME=$(grep '^Name:' "$METADATA_FILE" | awk '{print $2}')

echo "PKG_NAME: $PKG_NAME"       # <--- Added this for verification
echo "METADATA_VERSION: $METADATA_VERSION"
echo "PKG_VERSION: $PKG_VERSION"

# --- Get the shiv version ---
SHIV_VERSION=$(shiv --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
echo "SHIV_VERSION: $SHIV_VERSION"

## --- Sanitize PKG_VERSION to remove any accidental metadata version concatenation ---
## Example: pipeline-eds-0.2.1100.2.1-py312.pyz -> pipeline-eds-0.2.110-py312.pyz
#if [[ "$PKG_VERSION" == *"$METADATA_VERSION"* ]]; then
#    PKG_VERSION="${PKG_VERSION/$METADATA_VERSION/}"  # remove first occurrence
#fi

# --- Compose .pyz and .bat filenames --
# dash is prepended to EXTRAS_STR only if non-empty, and otherwise is an empty str
PYZ_PATH="$DIST_DIR/${PKG_NAME}-${PKG_VERSION}-py${PY_MAJOR}${PY_MINOR}${EXTRAS_STR}.pyz"
BAT_PATH="${PYZ_PATH%.pyz}.bat"

echo "Output .pyz will be: $PYZ_PATH"
echo "Output launcher .bat will be: $BAT_PATH"


# --
if [ -n "$latest_wheel" ]; then
    echo "Building .pyz from wheel: $latest_wheel"
    shiv "$latest_wheel" -e pipeline.cli:app -o "$PYZ_PATH" -p "/usr/bin/env python3"
    exit_code=$?
else
    # Artifact, should never hit.
    if [ -f "requirements.txt" ]; then
        echo "No wheel found, building from source with requirements.txt..."
        shiv . -r requirements.txt -e pipeline.cli:app -o "$PYZ_PATH" -p "/usr/bin/env python3"
        exit_code=$?
    else
        echo "Error: No wheel or requirements.txt found."
        exit 1
    fi
fi

# --- Generate Windows launcher ---
if [ $exit_code -eq 0 ]; then
    echo "Successfully created $PYZ_PATH"

    echo "@echo off" > "$BAT_PATH"
    echo "REM Windows launcher for $PYZ_PATH" >> "$BAT_PATH"
    echo "set PY_EXE=python.exe" >> "$BAT_PATH"
    echo "set PYZ_FILE=$(basename "$PYZ_PATH")" >> "$BAT_PATH"
    echo "PUSHD \"%~dp0\"" >> "$BAT_PATH"
    echo "\"%PY_EXE%\" \"%PYZ_FILE%\" %*" >> "$BAT_PATH"
    echo "POPD" >> "$BAT_PATH"
    echo "pause" >> "$BAT_PATH"

    echo "Generated Windows launcher: $BAT_PATH"
else
    echo "shiv failed with exit code $exit_code"
    exit $exit_code
fi

