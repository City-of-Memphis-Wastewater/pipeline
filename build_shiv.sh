#!/bin/bash

# --- Logic to find the most recently created .whl file ---

# Find the newest .whl file in the dist directory using 'ls -t' (sort by time, newest first)
# and 'head -n 1' to take only the first line.
# '2>/dev/null' suppresses any error message if no files are found.
latest_wheel=$(ls -t dist/*.whl 2>/dev/null | head -n 1)
exit_code=0

# Check if a wheel file was found
if [ -z "$latest_wheel" ]; then
    echo "Error: No wheel file (.whl) found in the 'dist' directory."
    echo "Please run 'poetry build' first."
    exit 1
fi

wheel_path="$latest_wheel"
echo "Building .pyz from wheel: $wheel_path"

# Setting bootstrap cache is omitted as it caused an error in the original script.

# --- Execute shiv command ---

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