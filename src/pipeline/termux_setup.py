# pipeline/install_termux.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import os
from pathlib import Path
import sys

from pipeline.environment import is_termux
from pipeline.version_info import get_package_name
    
# Constants
APP_NAME = get_package_name()
PACKAGE_NAME = get_package_name() # Used for executable name and AppData folder
PIPX_UPGRADE_SCRIPTNAME = "upgrade_and_run_eds.sh"
PIPX_RUN_SCRIPTNAME = "pipx_eds_plot.sh"
ELF_RUN_SCRIPTNAME = "eds trend -d.sh"

def setup_termux_shortcut():
    if not is_termux():
        return
    # Check the type of file being run, whether a pipx binary in .local/bin or an ELF file or a PYZ, etc
    if is_elf():
        setup_termux_elf_shortcut()
    elif is_pipx():
        setup_termux_pipx_shortcut()

def is_pipx() -> bool:
    """Checks if the executable is running from a pipx managed environment."""
    try:
        # pipx installs symlinks typically in $HOME/.local/bin/ or Termux system bin.
        exec_path = Path(sys.argv[0]).resolve()
        # Check for common pipx/system bin path substrings
        return "local/bin" in str(exec_path) or exec_path.parent.name == 'bin'
    except Exception:
        # Fallback for unexpected path errors
        return False

def is_elf() -> bool:
    """Checks if the currently running executable (sys.argv[0]) is a standalone PyInstaller-built ELF binary."""
    # If it's a pipx installation, it is not the monolithic binary we are concerned with here.
    if is_pipx():
        return False
        
    exec_path = Path(sys.argv[0]).resolve()
    
    # Check if the file exists and is readable
    if not exec_path.is_file():
        return False
        
    try:
        # Check the magic number: The first four bytes of an ELF file are 0x7f, 'E', 'L', 'F' (b'\x7fELF').
        # This is the most reliable way to determine if the executable is a native binary wrapper (like PyInstaller's).
        with open(exec_path, 'rb') as f:
            magic_bytes = f.read(4)
        
        return magic_bytes == b'\x7fELF'
    except Exception:
        # Handle exceptions like PermissionError, IsADirectoryError, etc.
        return False
    
def setup_termux_pipx_shortcut():
    """
    Creates the Termux widget shortcut script if running in Termux and the 
    shortcut does not already exist.
    """
    if not is_termux():
        return

    # Termux shortcut directory and file path
    home_dir = Path.home()
    shortcut_dir = home_dir / ".shortcuts"
    shortcut_file = shortcut_dir / PIPX_RUN_SCRIPTNAME

    if shortcut_file.exists():
        # Shortcut is already set up, nothing to do
        return

    # Ensure the .shortcuts directory exists
    try:
        shortcut_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Failed to create Termux shortcut directory {shortcut_dir}: {e}")
        return

    # 2Define the content of the script
    # We use the pipx executable name directly as it is on the PATH.
    script_content = f"""#!/data/data/com.termux/files/usr/bin/bash

# Termux Widget/Shortcut Script for EDS Plotter
# This shortcut was automatically generated during first run.
$HOME/.local/bin/eds --version 
$HOME/.local/bin/eds trend --default-idcs
"""

    # Write the script to the file
    try:
        shortcut_file.write_text(script_content, encoding='utf-8')
    except Exception as e:
        print(f"Warning: Failed to write Termux shortcut file {shortcut_file}: {e}")
        return

    # Make the script executable (chmod +x)
    try:
        os.chmod(shortcut_file, 0o755)
        print(f"Successfully created Termux shortcut at: {shortcut_file}")
        print("Please restart the Termux app or wait a moment for the widget to update.")
    except Exception as e:
        print(f"Warning: Failed to set executable permissions on {shortcut_file}: {e}")

    # --- 2. Upgrade and Run Shortcut  ---
    upgrade_shortcut_file = shortcut_dir / PIPX_UPGRADE_SCRIPTNAME
    
    if not upgrade_shortcut_file.exists():
        upgrade_script_content = f"""#!/data/data/com.termux/files/usr/bin/bash

# Termux Widget/Shortcut Script for {APP_NAME} (Upgrade and Run)
# Updates core packages and the pipx installation before running the app.

echo "--- Starting Termux Environment Update ---"

# Update core system packages
pkg upgrade -y

# If installed via pipx, update the app
if command -v {PACKAGE_NAME} &> /dev/null; then
    echo "Upgrading {PACKAGE_NAME} via pipx..."
    pipx upgrade {PACKAGE_NAME}
    echo "{PACKAGE_NAME} upgrade complete."
else
    echo "{PACKAGE_NAME} not found via pipx (or command failed). Skipping app upgrade."
fi

echo "--- Launching {APP_NAME} ---"
# Execute the application
$HOME/.local/bin/{PACKAGE_NAME} trend --default-idcs
"""
        try:
            upgrade_shortcut_file.write_text(upgrade_script_content, encoding='utf-8')
            os.chmod(upgrade_shortcut_file, 0o755)
            print(f"Successfully created Termux upgrade shortcut for pipx at: {upgrade_shortcut_file}")
        except Exception as e:
            print(f"Warning: Failed to set up Termux pipx upgrade shortcut: {e}")


def setup_termux_elf_shortcut():
    """
    Creates the Termux widget shortcut script if running in Termux and the 
    shortcut does not already exist. It uses the filename of the currently 
    running ELF executable (wrapper) for the command.
    """
    if not is_termux():
        return

    # 1. Determine the name of the running executable (the ELF binary)
    try:
        # sys.argv[0] is the path to the currently running executable (e.g., pipeline-0.2.1-aarch64).
        running_exec_path = Path(sys.argv[0])
        exec_filename = running_exec_path.name
        
        # NOTE: No checks for .pyz extension are needed, as we assume the executable
        # is the Termux-native ELF wrapper when running in this environment.

    except IndexError:
        print("Warning: Could not determine running executable name from sys.argv. Aborting shortcut creation.", file=sys.stderr)
        return

    # Termux shortcut directory and file path
    home_dir = Path.home()
    shortcut_dir = home_dir / ".shortcuts"
    shortcut_file = shortcut_dir / ELF_RUN_SCRIPTNAME

    if shortcut_file.exists():
        # Shortcut is already set up, nothing to do
        return

    # 2. Ensure the .shortcuts directory exists
    try:
        shortcut_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Failed to create Termux shortcut directory {shortcut_dir}: {e}")
        return

    # 3. Define the content of the script
    # We use the specific filename determined above. We also add 'cd $HOME'
    # as Termux widgets sometimes execute from an arbitrary path.
    script_content = f"""#!/data/data/com.termux/files/usr/bin/bash

# Termux Widget/Shortcut Script for EDS Plotter
# This shortcut was automatically generated during first run.
# It targets the executable named '{exec_filename}'.
# ASSUMPTION: The user has copied the Termux ELF binary to $HOME.

# Change directory to $HOME where the executable should reside for relative execution
cd "$HOME" || exit 1 

# Execute the application (The ELF binary)
./{exec_filename} --version 
./{exec_filename} trend --default-idcs
"""

    # 4. Write the script to the file
    try:
        shortcut_file.write_text(script_content, encoding='utf-8')
    except Exception as e:
        print(f"Warning: Failed to write Termux shortcut file {shortcut_file}: {e}")
        return

    # 5. Make the script executable (chmod +x)
    try:
        os.chmod(shortcut_file, 0o755)
        print(f"Successfully created Termux shortcut at: {shortcut_file}")
        print("Please restart the Termux app or wait a moment for the widget to update.")
    except Exception as e:
        print(f"Warning: Failed to set executable permissions on {shortcut_file}: {e}")

def cleanup_termux_pipx_shortcut():
    """Removes the pipx-based Termux shortcut file."""
    if not is_termux():
        return
        
    home_dir = Path.home()
    shortcut_file = home_dir / ".shortcuts" / PIPX_RUN_SCRIPTNAME

    if shortcut_file.exists():
        try:
            shortcut_file.unlink()
            print(f"Cleaned up Termux pipx shortcut: {shortcut_file.name}")
        except Exception as e:
            print(f"Warning: Failed to delete Termux shortcut {shortcut_file}: {e}")


def cleanup_termux_upgrade_shortcut():
    """Removes the pipx-based Termux upgrade and run shortcut file."""
    if not is_termux():
        return
        
    home_dir = Path.home()
    shortcut_file = home_dir / ".shortcuts" / PIPX_UPGRADE_SCRIPTNAME

    if shortcut_file.exists():
        try:
            shortcut_file.unlink()
            print(f"Cleaned up Termux pipx upgrade shortcut: {shortcut_file.name}")
        except Exception as e:
            print(f"Warning: Failed to delete Termux shortcut {shortcut_file}: {e}")

def cleanup_termux_elf_shortcut():
    """Removes the ELF-based Termux shortcut file."""
    if not is_termux():
        return
        
    home_dir = Path.home()
    shortcut_file = home_dir / ".shortcuts" / "eds trend -d.sh"

    if shortcut_file.exists():
        try:
            shortcut_file.unlink()
            print(f"Cleaned up Termux ELF shortcut: {shortcut_file.name}")
        except Exception as e:
            print(f"Warning: Failed to delete Termux shortcut {shortcut_file}: {e}")

def cleanup_termux_shortcut():
    """
    Performs full uninstallation cleanup of Termux shortcut files.
    Tries to remove both possible filenames for robustness.
    """
    if not is_termux():
        return
        
    print(f"Starting Termux uninstallation cleanup for {APP_NAME}...")
    
    # Attempt to clean up both known shortcut names
    cleanup_termux_pipx_shortcut()
    cleanup_termux_elf_shortcut()
    
    print("Termux cleanup complete.")