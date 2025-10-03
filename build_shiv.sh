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
        echo "No wheel file (.whl) found. Falling back to requirements.txt installation."
        echo "Attempting to build .pyz from requirements.txt..."
        echo "Note: Including 'src/' directory to ensure the 'pipeline' module is found in the 'src/' layout."

        # Build the .pyz using the source directory (src/) for the local package and requirements.txt for dependencies
        shiv src/ \
             -r requirements.txt \
             -e pipeline.cli:app \
             -o "$pyz_path" \
             -p "/usr/bin/env python3"

        exit_code=$?
    else
        # --- Path C: Failure ---
        echo "Error: No wheel file (.whl) found in the 'dist' directory."
        echo "Error: requirements.txt not found. Cannot build executable."
        echo "Please build a wheel file (e.g., using 'poetry build' or 'pip wheel') or create a requirements.txt file."
        exit 1
    fi
fi

# Check the exit code from the shiv command
if [ $exit_code -eq 0 ]; then
    echo "Successfully created $pyz_path"
else
    echo "Error: shiv failed to create $pyz_path (Exit Code: $exit_code). Review the output above for the cause."
    exit $exit_code
fi
