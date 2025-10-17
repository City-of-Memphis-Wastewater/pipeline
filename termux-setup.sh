#!/usr/bin/env bash
# This line (shebang) specifies that the script should be run using the bash interpreter.

# Exit immediately if any command fails.
set -e

# --- System-Level Setup ---

# Use Termux's package manager 'pkg' to install system-wide Python libraries.
# - 'python-cryptography' and 'python-numpy' are installed at the OS level.
# - '-y' automatically answers 'yes' to any confirmation prompts.
pkg install python-cryptography python-numpy -y

# --- Python Virtual Environment Setup ---

# Create a Python virtual environment named '.venv' in the current directory.
# --system-site-packages: This is a crucial flag. It allows the .venv
# to see and use packages installed system-wide (like the numpy and cryptography
# we just installed), preventing the need to reinstall them inside the venv.
python -m venv .venv --system-site-packages

# Activate the newly created virtual environment.
# This modifies the shell's $PATH to prioritize the .venv/bin directory,
# so commands like 'python' and 'pip' now refer to the ones inside the venv.
source .venv/bin/activate

# --- Python Dependency Installation ---

# This comment assumes a 'requirements.txt' file already exists,
# likely created by a tool like Poetry.
# Assume the requirements.txt has been properly updated using: poetry export -f requirements.txt --without-hashes --output requirements.txt

# Define a shell variable containing a regular expression.
# This pattern will match lines that start with 'cryptography', 'secretstorage', or 'numpy'.
# We want to exclude these because:
#   - 'cryptography' & 'numpy': Already installed via 'pkg'.
#   - 'secretstorage': Often relies on desktop components (like D-Bus)
#     that don't exist in Termux, so it's excluded to prevent errors.
EXCLUDE_PATTERN='^(cryptography|secretstorage|numpy)$'

# Create a new, filtered requirements file.
# grep: Searches the 'requirements.txt' file.
#   -E: Use extended regular expressions (to understand the pattern).
#   -v: Invert match, meaning it prints lines that *do not* match the pattern.
# > requirements-termux.txt: Redirects the output (the filtered list)
#   to a new file named 'requirements-termux.txt'.
grep -Ev "$EXCLUDE_PATTERN" requirements.txt > requirements-termux.txt

# $excludePattern = '^(cryptography|secretstorage|numpy)$'
# Get-Content requirements.txt | Where-Object { $_ -notmatch $excludePattern } | Set-Content requirements-termux.txt # powershell version

# Install the filtered list of Python packages using pip.
# --no-deps: Do not install dependencies for these packages. This is safe
#   *only* because we assume 'requirements.txt' is a "frozen" list with
#   *all* dependencies already listed.
# --no-cache-dir: Disable the pip cache to save space, useful in constrained
#   mobile environments.
# --prefer-binary: Prefer downloading pre-compiled binary "wheels" over
#   source distributions, which is much faster as it avoids compilation.
# -r requirements-termux.txt: Install from the specified file.
pip install --no-deps --no-cache-dir --prefer-binary -r requirements-termux.txt
