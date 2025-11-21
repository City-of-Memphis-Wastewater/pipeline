#!/usr/bin/env bash
# Termux setup leveraging 'build' and .whl metadata.
set -e

# --- 1. System-Level Setup ---
echo "⚙️ Installing system packages via pkg (numpy, cryptography)..." 
pkg install python-cryptography python-numpy -y

# --- 2. Venv and Build Setup ---
echo "🐍 Setting up virtual environment..."
python -m venv .venv --system-site-packages
source .venv/bin/activate

# Ensure 'build' is installed to create the wheel
echo "📦 Installing 'build' and 'packaging'..."
pip install build packaging

# Generate the wheel using python -m build. This respects pyproject.toml
echo "🏗️ Building the .whl package from pyproject.toml..."
# Clean up old build/dist files first
rm -rf dist build
python -m build --wheel

# Find the newly built wheel file (e.g., dist/pipeline_eds-0.1.0-py3-none-any.whl)
WHEEL_FILE=$(find dist -name "*.whl" | head -n 1)
if [ -z "$WHEEL_FILE" ]; then
    echo "ERROR: Wheel file not found in 'dist/'"
    exit 1
fi
echo "✅ Wheel built: $WHEEL_FILE"

# --- 3. Dependency Extraction and Filtering (Python Logic) ---
echo "🔬 Extracting and filtering dependencies from the wheel..."

# Embed Python script to read METADATA, filter, and output requirements
python3 - "$WHEEL_FILE" <<EOF
import zipfile
import re
import sys
from pathlib import Path

WHEEL_PATH = Path(sys.argv[1])
# Packages already installed via 'pkg' that must be excluded from pip install
EXCLUDED = {"cryptography", "numpy", "secretstorage"}

def extract_and_filter_dependencies(wheel_path: Path):
    """Opens the wheel, reads METADATA, filters, and prints the pip requirements."""
    
    # 1. Open the wheel file
    with zipfile.ZipFile(wheel_path, 'r') as zf:
        # 2. Find the METADATA file inside the dist-info directory
        metadata_name = next(f for f in zf.namelist() if f.endswith(".dist-info/METADATA"))
        content = zf.read(metadata_name).decode('utf-8')
        
        # 3. Process each line
        for line in content.splitlines():
            # Check for 'Requires-Dist' lines, which contain dependencies
            if line.startswith("Requires-Dist:"):
                # Extract the dependency specification (e.g., 'typer (>=0.7.0)')
                spec = line.split(":", 1)[1].strip()
                
                # Check if the package is one of our excluded packages
                # This pattern matches package names at the start of the spec string.
                package_match = re.match(r"^([\w-]+)", spec)
                if package_match:
                    package_name = package_match.group(1).lower().replace('_', '-')
                    
                    if package_name in EXCLUDED:
                        # Skip this package
                        continue
                        
                # 4. If not excluded, print the requirement spec (pip format)
                print(spec)

# Run the extraction and filter script and pipe output to requirements-termux.txt
# The print() statements are captured by the shell.
extract_and_filter_dependencies(WHEEL_PATH)
EOF
# The output of the Python script (the filtered dependency list)
# is redirected to a temporary file.
> requirements-termux.txt

# --- 4. Pip Installation ---
echo "💻 Installing filtered Python packages from requirements-termux.txt..."

# Note: We must run the Python script *before* the redirection,
# but using a pipe with a here document can be tricky.
# We will use a temporary file to hold the requirements from the script's output.
# (The Python script above simply prints to stdout; the shell needs to capture it.)

# Re-run Python logic, capturing output to the file:
python3 - "$WHEEL_FILE" > requirements-termux.txt <<EOF
$(cat <<EOD
$(grep Requires-Dist: $WHEEL_FILE)
EOD
)
EOF

# Using the previous output structure (simplified pipe for clarity):
# Since piping a here-doc's stdout can get complex, a simple solution is to
# ensure the Python script above runs and its output is redirected in the shell flow.
# Let's adjust the Python block to redirect directly for simplicity:

# Rerunning the final, cleaner approach:
python3 - "$WHEEL_FILE" > requirements-termux.txt <<'EOD'
import zipfile
import re
import sys
from pathlib import Path
# ... (rest of the Python code as above) ...
EOD

# Let's assume the first run printed the requirements to stdout.
# The `>` redirection needs to be outside the EOF block for the shell to handle it.

# **Fix for Redirection:**
# We use a temporary file inside the shell to capture the output of the Python script.
TEMP_REQS=$(mktemp)
python3 - "$WHEEL_FILE" > "$TEMP_REQS" <<'EOF_PYTHON'
import zipfile
import re
import sys
from pathlib import Path

WHEEL_PATH = Path(sys.argv[1])
EXCLUDED = {"cryptography", "numpy", "secretstorage"}

def extract_and_filter_dependencies(wheel_path: Path):
    with zipfile.ZipFile(wheel_path, 'r') as zf:
        metadata_name = next(f for f in zf.namelist() if f.endswith(".dist-info/METADATA"))
        content = zf.read(metadata_name).decode('utf-8')
        
        for line in content.splitlines():
            if line.startswith("Requires-Dist:"):
                spec = line.split(":", 1)[1].strip()
                
                package_match = re.match(r"^([\w-]+)", spec)
                if package_match:
                    package_name = package_match.group(1).lower().replace('_', '-')
                    
                    if package_name in EXCLUDED:
                        continue
                        
                # Output the filtered requirement to stdout
                print(spec)

extract_and_filter_dependencies(WHEEL_PATH)
EOF_PYTHON

# Now we have the filtered list in $TEMP_REQS
mv "$TEMP_REQS" requirements-termux.txt

# Install the dependencies using the new requirements file
pip install \
    --no-cache-dir \
    --prefer-binary \
    -r requirements-termux.txt

# --- 5. Final Cleanup and Setup ---
echo "🧹 Cleaning up temp files..."
rm -f requirements-termux.txt
rm -rf dist build # Clean up artifacts
# The wheel file itself is still in the dist folder, or can be removed if desired.

source .venv/bin/activate
export PYTHONPATH=$(pwd)/src

echo "✅ Termux setup complete. Venv active, dependencies filtered by .whl metadata."
