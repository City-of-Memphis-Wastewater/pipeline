# pipeline/install_termux.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import os
from pathlib import Path

from pipeline.environment import is_termux
from pipeline.version_info import get_package_name
    
# Constants
APP_NAME = get_package_name()
PACKAGE_NAME = get_package_name() # Used for executable name and AppData folder

TERMUX_SHORTCUT_DIR = ".shortcuts"
BASHRC_PATH = Path.home() / ".bashrc"

# Shortcut filenames for cleanup
ELF_SHORTCUT_NAME = f"{PACKAGE_NAME}.sh"
PIPX_SHORTCUT_NAME = f"{PACKAGE_NAME}-pipx.sh"
UPGRADE_SHORTCUT_NAME = f"{PACKAGE_NAME}-upgrade.sh" # New script for pipx upgrades

# Alias marker comments for easy cleanup
ALIAS_START_MARKER = f"# >>> Start {APP_NAME} Alias >>>"
ALIAS_END_MARKER = f"# <<< End {APP_NAME} Alias <<<"

# --- Utility Functions ---

def is_termux() -> bool:
    """Checks if the application is running in the Termux environment."""
    return 'TERMUX_VERSION' in os.environ

def is_pipx() -> bool:
    """Checks if the application appears to be running from a pipx installation."""
    # Heuristic: Check if the executable name contains 'pipx' or resides in .local/bin/
    exe_path = Path(os.environ.get('_', ''))
    return 'pipx' in exe_path.parts or (exe_path.parent.name == 'bin' and '.local' in exe_path.parts)

# --- Setup Functions ---

def _get_termux_shortcut_path() -> Path:
    """Returns the absolute path to the Termux widget shortcut directory."""
    return Path.home() / TERMUX_SHORTCUT_DIR

def _create_shortcut(path: Path, content: str):
    """Writes the shortcut script and sets execute permissions."""
    try:
        # 1. Ensure the directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 2. Write the script content
        path.write_text(content, encoding='utf-8')
        
        # 3. Set execute permissions (crucial for shell scripts)
        os.chmod(path, 0o755)
        print(f"Termux shortcut created/updated: {path}")
    except Exception as e:
        print(f"Error creating Termux shortcut {path}: {e}")

def register_shell_alias(exe_path: Path):
    """
    Registers a permanent shell alias for the ELF binary in ~/.bashrc.
    This allows the user to run the app using the package name.
    """
    if not BASHRC_PATH.exists():
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
alias {PACKAGE_NAME}='"{exe_path}"'
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


def setup_termux_elf_shortcut(exe_path: Path):
    """
    Creates the main shortcut script for the Termux ELF binary and registers the alias.
    """
    # 1. Create the Widget Shortcut
    elf_path_str = str(exe_path)
    SCRIPT_CONTENT = f"""#!/data/data/com.termux/files/usr/bin/bash
# {APP_NAME} ELF Binary Shortcut
# Executes the standalone Termux ELF binary
cd $(dirname "$0")
"{elf_path_str}" $@
"""
    _create_shortcut(_get_termux_shortcut_path() / ELF_SHORTCUT_NAME, SCRIPT_CONTENT)
    
    # 2. Register the Shell Alias (New Step)
    register_shell_alias(exe_path)


def setup_termux_pipx_shortcut(exe_path: Path):
    """
    Creates the main shortcut script for a pipx-installed binary or a generic PYZ.
    This script executes the command by name (e.g., 'eds').
    """
    SCRIPT_CONTENT = f"""#!/data/data/com.termux/files/usr/bin/bash
# {APP_NAME} Pipx/General Shortcut
# Executes the application via the system PATH (e.g., pipx installation)
cd $(dirname "$0")
{PACKAGE_NAME} $@
"""
    _create_shortcut(_get_termux_shortcut_path() / PIPX_SHORTCUT_NAME, SCRIPT_CONTENT)


def setup_termux_pipx_upgrade_shortcut():
    """
    Creates a dedicated shortcut that upgrades the pipx installation before running.
    """
    SCRIPT_CONTENT = f"""#!/data/data/com.termux/files/usr/bin/bash
# {APP_NAME} Upgrade and Run Shortcut
echo "Updating system packages..."
pkg upgrade -y

echo "Upgrading {PACKAGE_NAME} via pipx..."
if command -v pipx &> /dev/null; then
    pipx upgrade {PACKAGE_NAME}
    echo "Upgrade complete. Running application..."
    # Run the main command
    {PACKAGE_NAME} trend --default-idcs
else
    echo "pipx command not found. Cannot auto-upgrade."
fi
"""
    _create_shortcut(_get_termux_shortcut_path() / UPGRADE_SHORTCUT_NAME, SCRIPT_CONTENT)


def setup_termux_install():
    """
    Main dispatcher for Termux shortcut setup.
    """
    if not is_termux():
        return
    
    # Termux setup needs to know which type of executable is running to create the best shortcut
    exe_path = Path(os.environ.get('_', ''))
    
    # Case 1: Running as a specific ELF binary
    # The heuristic for ELF is simplified here, assuming if it's NOT pipx and NOT a simple name, it's the ELF
    if not is_pipx() and ("aarch64" in str(exe_path) or "x86_64" in str(exe_path)):
        print(f"Termux setup detected ELF binary: {exe_path.name}")
        setup_termux_elf_shortcut(exe_path)
        # We assume if it's a standalone ELF, the user doesn't need the pipx upgrade script.
    
    # Case 2: Running from pipx or general installation (most common scenario)
    else:
        print(f"Termux setup detected pipx or general installation.")
        setup_termux_pipx_shortcut(exe_path)
        setup_termux_pipx_upgrade_shortcut()


# --- Cleanup Functions ---

def _remove_file_if_exists(path: Path, description: str):
    """Helper to safely remove a file and print confirmation."""
    if path.exists():
        try:
            path.unlink()
            print(f"Cleaned up {description}: {path.name}")
        except Exception as e:
            print(f"Warning: Failed to delete {description} {path.name}: {e}")
            
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
