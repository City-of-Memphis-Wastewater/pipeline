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
PACKAGE_NAME_ELF = f"{get_package_name()}-elf"

# Shortcut filenames for cleanup
ELF_SHORTCUT_NAME = f"{PACKAGE_NAME}-elf.sh"
PIPX_SHORTCUT_NAME = f"{PACKAGE_NAME}-pipx.sh"
UPGRADE_SHORTCUT_NAME = f"{PACKAGE_NAME}-upgrade.sh" # New script for pipx upgrades

TERMUX_SHORTCUT_DIR = ".shortcuts"
BASHRC_PATH = Path.home() / ".bashrc"

# Alias marker comments for easy cleanup
ALIAS_START_MARKER = f"# >>> Start {APP_NAME} Alias >>>"
ALIAS_END_MARKER = f"# <<< End {APP_NAME} Alias <<<"

def setup_termux_install(force=False):
    """
    Main dispatcher for Termux shortcut setup.
    """
    if not is_termux():
        return

    # Check the type of file being run, whether a pipx binary in PIPX_BIN_DIR or an ELF file or a PYZ, etc
    if is_elf():
        setup_termux_widget_elf_shortcut(force)
        register_shell_alias_elf_to_basrc(force)
    elif is_pipx():
        setup_termux_widget_pipx_shortcut(force)
        setup_termux_widget_pipx_upgrade_shortcut(force)


def is_pipx() -> bool:
    """Checks if the executable is running from a pipx managed environment."""
    try:
        # pipx installs symlinks typically in PIPX_BIN_DIR/ or Termux system bin.
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
    
def _get_termux_shortcut_path() -> Path:
    """Returns the absolute path to the Termux widget shortcut directory."""
    return Path.home() / TERMUX_SHORTCUT_DIR

    
def setup_termux_widget_pipx_shortcut(force=False):
    """
    Creates the Termux widget shortcut script if running in Termux and the 
    shortcut does not already exist.
    """
    if not is_termux():
        return

    # Termux shortcut directory and file path
    home_dir = Path.home()
    shortcut_dir = home_dir / ".shortcuts"
    shortcut_file = shortcut_dir / PIPX_SHORTCUT_NAME

    if shortcut_file.exists() and not force:
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
# With this line, shotcuts will be treated the same as runnig from shell.
source $HOME/.bashrc 2>/dev/null || true

# Termux Widget/Shortcut Script for EDS Plotter
# This shortcut was automatically generated during first run.
PIPX_BIN_DIR/{PACKAGE_NAME} --version 
PIPX_BIN_DIR/eds trend --default-idcs
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

def setup_termux_widget_pipx_upgrade_shortcut(force):
    """
    Generate the Termux Widgets Shortcut to upgrade the pipx-installed package.
    This script is addded to $HOME/.shortcuts/
    Runs the package afterwards to demonstrate success.
    """

    # --- 2. Upgrade and Run Shortcut  ---
    upgrade_shortcut_file = _get_termux_shortcut_path() / UPGRADE_SHORTCUT_NAME
    
    if upgrade_shortcut_file.exists() and not force: # force is True allows override of old version of the shortcut script, meant for the CLI `install --upgrade` command, and not when the program runs every time on start up
        return
        
    upgrade_script_content = f"""#!/data/data/com.termux/files/usr/bin/bash
# With this line, shortcuts will be treated the same as runnig from shell.
source $HOME/.bashrc 2>/dev/null || true

# Termux Widget/Shortcut Script for {APP_NAME} (Upgrade and Run)
# Updates core packages and the pipx installation before running the app.

echo "--- Starting Termux Environment Update ---"
# Update core system packages
pkg upgrade -y

echo " --- Updating {PACKAGE_NAME} with pipx ---"
echo "which {PACKAGE_NAME}"
which {PACKAGE_NAME}
# If installed via pipx, update the app
if command -v {PACKAGE_NAME} &> /dev/null; then
    echo "Upgrading {PACKAGE_NAME} via pipx..."
    pipx upgrade {PACKAGE_NAME}
    echo "{PACKAGE_NAME} upgrade complete."

    echo "Upgrading shortcut script {UPGRADE_SHORTCUT_NAME}..."
    # The 'install' command with the --upgrade flag
    # forces the Python code to re-generate both shortcut scripts.
    PIPX_BIN_DIR/{PACKAGE_NAME} install --upgrade
    echo "{PACKAGE_NAME} upgrade complete. This should impact all Termux widget shortcut scripts relevant to a pipx installation."
    # Things might get weird here if the {PACKAGE_NAME} package name alias is pointed at a binary rather than at the pipx CLI installation.
else
    echo "{PACKAGE_NAME} not found via pipx (or command failed). Skipping app upgrade."
fi

echo "--- Launching {APP_NAME} ---"
# Execute the application
PIPX_BIN_DIR/{PACKAGE_NAME} trend --default-idcs
"""
    try:
        upgrade_shortcut_file.write_text(upgrade_script_content, encoding='utf-8')
        os.chmod(upgrade_shortcut_file, 0o755)
        print(f"Successfully created Termux upgrade shortcut for pipx at: {upgrade_shortcut_file}")
    except Exception as e:
        print(f"Warning: Failed to set up Termux pipx upgrade shortcut: {e}")


def setup_termux_widget_elf_shortcut(force=False):
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
    shortcut_file = shortcut_dir / ELF_SHORTCUT_NAME

    if shortcut_file.exists() and not force:
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
# With this line, shotcuts will be treated the same as runnig from shell.
source $HOME/.bashrc 2>/dev/null || true

# Termux Widget/Shortcut Script for EDS Plotter
# This shortcut was automatically generated during first run.
# It targets the executable named '{exec_filename}'.
# ASSUMPTION: The user has copied the Termux ELF binary to $HOME.

# Change directory to $HOME where the executable should reside for relative execution
cd "$HOME" || exit 1 

# Execute the application (The ELF binary)
# Allows shortcut to be built for wherever the executible is running from, rather than assuming it is in $HOME
{running_exec_path} --version 
{running_exec_path} trend --default-idcs


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

def register_shell_alias_elf_to_basrc(force=False):
    """
    Registers a permanent shell alias for the ELF binary in ~/.bashrc.
    This allows the user to run the app using the package name.
    """

    # Termux setup needs to know which type of executable is running to create the best shortcut
    exe_path = Path(os.environ.get('_', ''))

    if not BASHRC_PATH.exists() or force:
        # Create it if it doesn't exist
        try:
            BASHRC_PATH.touch()
            print(f"Created new bash profile file: {BASHRC_PATH.name}")
        except Exception as e:
            print(f"Warning: Could not create {BASHRC_PATH.name} for alias: {e}")
            return
            
    try:
        current_content = BASHRC_PATH.read_text()
    except Exception as e:
        print(f"Error reading {BASHRC_PATH.name}: {e}")
        return

    # 1. Remove any existing block before writing a new one (handles updates)
    start_index = current_content.find(ALIAS_START_MARKER)
    end_index = current_content.find(ALIAS_END_MARKER)
    
    if start_index != -1 and end_index != -1:
        # Find the content *before* the start marker
        pre_content = current_content[:start_index]
        # Find the content *after* the end marker (and the newline following it)
        post_content = current_content[end_index + len(ALIAS_END_MARKER):]
        # Combine them to remove the old block
        current_content = pre_content.rstrip() + post_content
        print("Removed existing shell alias block for update.")

    # 2. Define the new alias block
    # The alias definition must be wrapped in double quotes in the script to handle spaces
    # and executed with the full path to ensure it finds the ELF binary.
    alias_content = f"""
{ALIAS_START_MARKER}
# Alias to easily run the standalone ELF binary from any shell session
alias {PACKAGE_NAME_ELF}='"{exe_path}"'
{ALIAS_END_MARKER}
"""
    
    # 3. Append the new block to the content
    new_content = current_content.rstrip() + "\n" + alias_content.strip() + "\n"
    
    try:
        BASHRC_PATH.write_text(new_content)
        print(f"Registered shell alias '{PACKAGE_NAME}' in {BASHRC_PATH.name}.")
        print("Note: You must restart Termux or run 'source ~/.bashrc' for the alias to take effect.")
    except Exception as e:
        print(f"Error writing to {BASHRC_PATH.name} for alias: {e}")

# --- CLEAN UP / UNINSTALL ---

def cleanup_shell_alias():
    """
    Removes the shell alias block from ~/.bashrc.
    """
    if not BASHRC_PATH.exists():
        return
        
    try:
        current_content = BASHRC_PATH.read_text()
    except Exception as e:
        print(f"Error reading {BASHRC_PATH.name} during cleanup: {e}")
        return

    start_index = current_content.find(ALIAS_START_MARKER)
    end_index = current_content.find(ALIAS_END_MARKER)
    
    if start_index != -1 and end_index != -1:
        try:
            # Content before the block
            pre_content = current_content[:start_index]
            # Content after the block (skip the end marker and subsequent newline)
            post_content = current_content[end_index + len(ALIAS_END_MARKER):]
            
            # Write the file back without the alias block
            new_content = pre_content.rstrip() + post_content.lstrip('\n')
            
            BASHRC_PATH.write_text(new_content.strip() + "\n")
            print(f"Cleaned up shell alias from {BASHRC_PATH.name}.")
        except Exception as e:
            print(f"Error writing to {BASHRC_PATH.name} during alias cleanup: {e}")

def _remove_file_if_exists(path: Path, description: str):
    """Helper to safely remove a file and print confirmation."""
    if path.exists():
        try:
            path.unlink()
            print(f"Cleaned up {description}: {path.name}")
        except Exception as e:
            print(f"Warning: Failed to delete {description} {path.name}: {e}")


def cleanup_termux_install():
    """
    Removes all Termux widget shortcut scripts and the shell alias.
    """
    if not is_termux():
        return
        
    shortcut_dir = _get_termux_shortcut_path()
    print(f"Starting Termux uninstallation cleanup in {shortcut_dir}...")
    
    # Clean up artifacts
    _remove_file_if_exists(shortcut_dir / ELF_SHORTCUT_NAME, "ELF shortcut")
    _remove_file_if_exists(shortcut_dir / PIPX_SHORTCUT_NAME, "pipx shortcut")
    _remove_file_if_exists(shortcut_dir / UPGRADE_SHORTCUT_NAME, "pipx upgrade shortcut")
    cleanup_shell_alias() # New cleanup step
    
    # Attempt to remove the shortcut directory if it is now empty
    try:
        if not os.listdir(shortcut_dir):
            shortcut_dir.rmdir()
            print(f"Removed empty shortcut directory: {shortcut_dir.name}")
        else:
            print("Shortcut directory is not empty. Leaving remaining files in place.")
    except FileNotFoundError:
        pass # Already gone
    except OSError as e:
        print(f"Warning: Could not remove shortcut directory {shortcut_dir}: {e}")
        
    print("Termux cleanup complete.")
