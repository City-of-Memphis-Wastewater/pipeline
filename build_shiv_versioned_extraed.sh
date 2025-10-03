#!/bin/bash

# --- Determine dynamic .pyz filename ---
PKG_NAME=$(grep '^name =' pyproject.toml | sed 's/name = "\(.*\)"/\1/' | tr -cd '[:alnum:]._-' )
PKG_VERSION=$(grep '^version =' pyproject.toml | sed 's/version = "\(.*\)"/\1/' | tr -cd '[:alnum:]._-')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
PY_VERSION="py${PY_MAJOR}${PY_MINOR}"

# Keep only major.minor.patch (first three numeric groups)
PKG_VERSION=$(echo "$PKG_VERSION" | grep -oE '^[0-9]+\.[0-9]+\.[0-9]+')

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

# --- Sanitize .pyz filename to remove shiv version ---
# Example: pipeline-eds-0.2.1100.2.1-py312.pyz -> pipeline-eds-0.2.110-py312.pyz

# --- Get the shiv version ---
SHIV_VERSION=$(shiv --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')

# --- Sanitize PKG_VERSION to remove any accidental shiv version concatenation ---
if [[ "$PKG_VERSION" == *"$SHIV_VERSION"* ]]; then
    PKG_VERSION="${PKG_VERSION/$SHIV_VERSION/}"  # remove first occurrence
fi

# --- Compose .pyz and .bat filenames ---
INCLUDE_SHIV_VERSION=false

if [ "$INCLUDE_SHIV_VERSION" = true ]; then
    PYZ_PATH="$DIST_DIR/${PKG_NAME}-${PKG_VERSION}-shiv${SHIV_VERSION}-py${PY_MAJOR}${PY_MINOR}.pyz"
else
    PYZ_PATH="$DIST_DIR/${PKG_NAME}-${PKG_VERSION}-py${PY_MAJOR}${PY_MINOR}.pyz"
fi
BAT_PATH="${PYZ_PATH%.pyz}.bat"

echo "Output .pyz will be: $PYZ_PATH"
echo "Output launcher .bat will be: $BAT_PATH"

# --- Build .pyz ---
latest_wheel=$(ls -t dist/*.whl 2>/dev/null | head -n 1)

if [ -n "$latest_wheel" ]; then
    echo "Building .pyz from wheel: $latest_wheel"
    shiv "$latest_wheel" -e pipeline.cli:app -o "$PYZ_PATH" -p "/usr/bin/env python3"
    exit_code=$?
else
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
