#!/usr/bin/env bash

# 1. Update system and install essential tools
echo "--- 1. Updating Termux packages and installing Python ---"
pkg update -y
pkg upgrade -y
pkg install python -y

# 2. Install pipx and ensure PATH is set
echo "--- 2. Installing pipx and configuring shell environment ---"
python3 -m pip install pipx
pipx ensurepath

# Apply the PATH changes immediately for this session
# NOTE: The file is usually .bashrc, but Termux sometimes defaults to zsh.
# .bashrc is the most likely target if the user hasn't changed shells.
source $HOME/.bashrc 2>/dev/null || true 

# 3. Install the application
echo "--- 3. Installing pipeline-eds via pipx ---"
pipx install pipeline-eds

# 4. Set up storage access (critical for file access)
echo "--- 4. Setting up Termux storage access ---"
termux-setup-storage

# 5. Final Confirmation
echo "--- 5. Installation Complete ---"
echo "Verifying installation:"
pipx list
pipeline-eds --version
echo "Success! You can now run 'pipeline-eds' directly from any Termux session."