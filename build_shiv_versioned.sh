#!/bin/bash

# --- Determine dynamic .pyz filename ---
# Read project name and version from pyproject.toml using grep + sed
PKG_NAME=$(grep '^name =' pyproject.toml | sed 's/name = "\(.*\)"/\1/')
PKG_VERSION=$(grep '^version =' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
PY_VERSION="py${PY_MAJOR}${PY_MINOR}"

DIST_DIR="dist"
mkdir -p "$DIST_DIR"

PYZ_PATH="$DIST_DIR/${PKG_NAME}-${PKG_VERSION}-${PY_VERSION}.pyz"
BAT_PATH="$DIST_DIR/${PKG_NAME}.bat"

echo "Output .pyz will be: $PYZ_PATH"
echo "Output launcher .bat will be: $BAT_PATH"

# --- Existing logic ---
# Build from wheel or source as before, but write to $PYZ_PATH
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

    # Generate Windows launcher with correct pyz path
    echo "@echo off" > "$BAT_PATH"
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

