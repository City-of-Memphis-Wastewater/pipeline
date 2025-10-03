#!/bin/bash

# Check if shiv is installed and install it if not found (using pipx for isolated installation)
if ! command -v shiv &> /dev/null
then
    echo "shiv not found. Attempting to install via pipx..."
    # Attempt to install pipx if not present
    if ! command -v pipx &> /dev/null; then
        echo "pipx not found. Installing pipx..."
        # We rely on 'python3 -m pip' being available and compatible
        python3 -m pip install pipx || { echo "Failed to install pipx. Exiting."; exit 1; }
    fi
    pipx install shiv || { echo "Failed to install shiv. Exiting."; exit 1; }
    # Ensure shiv is accessible in the current shell session
    pipx ensurepath
    echo "shiv installed successfully. You may need to restart your shell for pipx path changes to take effect."
fi

# Ensure the output directory exists
mkdir -p dist

# Define the output file path
pyz_path="dist/pipeline.pyz"
bat_path="dist/pipeline.bat"

# Function to generate the Windows Batch launcher
generate_windows_launcher() {
    echo "@echo off" > "$bat_path"
    echo "REM --- Windows Launcher for pipeline.pyz ---" >> "$bat_path"
    echo "REM NOTE: This executable was built on a Unix environment (LF line endings)." >> "$bat_path"
    echo "REM This script ensures the executable runs correctly on Windows and pauses the window afterward." >> "$bat_path"
    echo "" >> "$bat_path"
    echo "set PY_EXE=python.exe" >> "$bat_path"
    echo "set PYZ_FILE=pipeline.pyz" >> "$bat_path"
    echo "" >> "$bat_path"
    echo "echo Running %PYZ_FILE%..." >> "$bat_path"
    echo "REM Call the system's python.exe to execute the self-contained archive" >> "$bat_path"
    echo "REM %* passes any command line arguments (like --help or run-command) to the python call." >> "$bat_path"
    echo "\"%PY_EXE%\" \"%%~dp0%PYZ_FILE%\" %*" >> "$bat_path"
    echo "" >> "$bat_path"
    echo "REM Keep the console window open after execution, mainly for double-click launches." >> "$bat_path"
    echo "pause" >> "$bat_path"
    echo "Generated Windows launcher: $bat_path"
}

# 1. Try to find the most recently created .whl file in the dist directory
latest_wheel=$(ls -t dist/*.whl 2>/dev/null | head -n 1)

if [ -n "$latest_wheel" ]; then
    # --- Path A: Build from existing Wheel (.whl) ---
    echo "Building .pyz from wheel: $latest_wheel"
    echo "Attempting to build .pyz..."

    # Build the .pyz using the wheel path as a positional argument
    shiv "$latest_wheel" \
         -e pipeline.cli:app \
         -o "$pyz_path" \
         -p "/usr/bin/env python3"

    exit_code=$?
else
    # 2. If no wheel is found, check for requirements.txt and fallback
    if [ -f "requirements.txt" ]; then
        # --- Path B: Fallback to Requirements.txt ---
        echo "No wheel file (.whl) found. Falling back to source installation using requirements.txt."
        echo "Attempting to build .pyz from requirements.txt..."
        echo "Note: Using the current directory (./) as the source package."
        echo "      This requires a pyproject.toml or setup.py in the root to be installable. (pyproject.toml is sufficient)"

        # Build the .pyz using the current directory (.) as the local package source
        # and requirements.txt for dependencies.
        shiv . \
             -r requirements.txt \
             -e pipeline.cli:app \
             -o "$pyz_path" \
             -p "/usr/bin/env python3"

        exit_code=$?
    else
        # --- Path C: Failure ---
        echo "Error: No wheel file (.whl) found in the 'dist' directory."
        echo "Error: requirements.txt not found. Cannot build executable."
        echo "Please build a wheel file (e.g., using 'pip wheel') or ensure an installable source is available."
        exit 1
    fi
fi

# Check the exit code from the shiv command and generate the launcher on success
if [ $exit_code -eq 0 ]; then
    echo "Successfully created $pyz_path"
    generate_windows_launcher # NEW: Generate the batch file
else
    echo "Error: shiv failed to create $pyz_path (Exit Code: $exit_code). Review the output above for the cause."
    exit $exit_code
fi