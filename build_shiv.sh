#!/bin/bash

# --- Logic to find the most recently created .whl file ---

# Find the newest .whl file in the dist directory using 'ls -t' (sort by time, newest first)
# and 'head -n 1' to take only the first line.
# '2>/dev/null' suppresses any error message if no files are found.
latest_wheel=$(ls -t dist/*.whl 2>/dev/null | head -n 1)
exit_code=0

# Check if a wheel file was found
if [ -z "$latest_wheel" ]; then
    echo "Warning: No pre-built wheel file (.whl) found in the 'dist' directory."

    # --- Fallback: Attempt to build directly from requirements.txt ---
    if [ -f "requirements.txt" ]; then
        echo "Attempting fallback: Building .pyz directly from requirements.txt..."

        # Execute shiv command using the requirements file
        shiv -r requirements.txt \
             -e pipeline.cli:app \
             -o dist/pipeline.pyz \
             -p "/usr/bin/env python3"

        # Capture the exit code of the fallback shiv command
        exit_code=$?

        # Check exit code and report success or failure
        if [ $exit_code -eq 0 ]; then
            echo "Successfully created dist/pipeline.pyz using requirements.txt"
            exit 0 # Exit successfully after the fallback build
        else
            echo "Error: Fallback shiv build failed! (Exit Code: $exit_code). Please ensure your 'requirements.txt' is valid and all dependencies are available."
            exit 1 # Exit with failure
        fi
    else
        # If no wheel AND no requirements.txt, then fail.
        echo "Error: Cannot find pre-built wheel file, and no 'requirements.txt' found for fallback build."
        echo "Please ensure you have run a build command (e.g., 'python -m build') or have a 'requirements.txt' file present."
        exit 1
    fi
fi

# --- Primary Path (Only executes if $latest_wheel was found) ---

wheel_path="$latest_wheel"
echo "Building .pyz from wheel: $wheel_path"

# Setting bootstrap cache is omitted as it caused an error in the original script.

# --- Execute shiv command with the wheel file ---

echo "Attempting to build .pyz..."

shiv "$wheel_path" \
     -e pipeline.cli:app \
     -o dist/pipeline.pyz \
     -p "/usr/bin/env python3"

# Capture the exit code of the last command (shiv)
exit_code=$?

# --- Check exit code and report success or failure ---
if [ $exit_code -eq 0 ]; then
    echo "Successfully created dist/pipeline.pyz"
else
    echo "Error: shiv failed to create pipeline.pyz (Exit Code: $exit_code). Review the output above for the cause."
    exit 1
fi
