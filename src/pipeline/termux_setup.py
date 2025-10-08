# pipeline/install_termux.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import os
from pathlib import Path
import sys

from pipeline.environment import is_termux, is_pipx, is_pyz, is_elf
from pipeline.version_info import get_package_name
    
# Constants
APP_NAME = get_package_name()
PACKAGE_NAME = get_package_name() # Used for executable name and AppData folder
# it is necessary to give the pacakge a separate alias name for different installations to avoid conflict with the pipx installation
PACKAGE_ALIAS_ELF = f"{get_package_name()}-elf"
PACKAGE_ALIAS_PYZ = f"{get_package_name()}-pyz"

# Shortcut filenames for cleanup
SHORTCUT_NAME_ELF = f"{PACKAGE_NAME}-elf.sh"
SHORTCUT_NAME_PYZ = f"{PACKAGE_NAME}-pyz.sh"
SHORTCUT_NAME_PIPX = f"{PACKAGE_NAME}-pipx.sh"
UPGRADE_SHORTCUT_NAME = f"{PACKAGE_NAME}-upgrade-pipx.sh" # New script for pipx upgrades

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
    exec_path = Path(sys.argv[0]).resolve()
    # Check the type of file being run, whether a pipx binary in PIPX_BIN_DIR or an ELF file or a PYZ, etc
    if is_elf():
        setup_termux_widget_executable_shortcut(force, shortcut_name = SHORTCUT_NAME_ELF)
        register_shell_alias_executable_to_basrc(force, package_alias = PACKAGE_ALIAS_ELF)
        setup_linux_app_data_directory(force)
    elif is_pyz(exec_path=exec_path):
        setup_termux_widget_executable_shortcut(force, shortcut_name = SHORTCUT_NAME_PYZ)
        register_shell_alias_executable_to_basrc(force, package_alias = PACKAGE_ALIAS_PYZ)
        setup_linux_app_data_directory(force)
    elif is_pipx():
        setup_termux_widget_pipx_shortcut(force)
        setup_termux_widget_pipx_upgrade_shortcut(force)


def _get_termux_shortcut_path() -> Path:
    """Returns the absolute path to the Termux widget shortcut directory."""
    return Path.home() / TERMUX_SHORTCUT_DIR

def setup_linux_app_data_directory():
    pass

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
    shortcut_file = shortcut_dir / SHORTCUT_NAME_PIPX

    if shortcut_file.exists() and not force:
        # Shortcut is already set up, nothing to do
        return

    # Ensure the .shortcuts directory exists
    try:
        shortcut_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Failed to create Termux shortcut directory {shortcut_dir}: {e}")
        return
    
    print(f"Creating Termux widget shortcut for pipx-installed {PACKAGE_NAME} at {shortcut_file}...")

    # 2Define the content of the script
    # We use the pipx executable name directly as it is on the PATH.
    script_content = f"""#!/usr/bin/env bash
# With this line, shortcuts will be treated the same as runnig from shell.
source $HOME/.bashrc 2>/dev/null || true

# Termux Widget/Shortcut Script
# This shortcut was automatically generated during first run.
{PACKAGE_NAME} --version 
{PACKAGE_NAME} trend --default-idcs
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
        
    upgrade_script_content = f"""#!/usr/bin/env bash
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
    echo "pipx upgrade {PACKAGE_NAME} ..."
    pipx upgrade {PACKAGE_NAME}
    echo "{PACKAGE_NAME} upgrade complete."
    
    echo "Upgrading shortcut script {UPGRADE_SHORTCUT_NAME}..."
    # The 'install' command with the --upgrade flag
    # forces the Python code to re-generate both shortcut scripts.
    {PACKAGE_NAME} install --upgrade
    echo "{PACKAGE_NAME} upgrade complete. This should impact all Termux widget shortcut scripts relevant to a pipx installation."
    # Things might get weird here if the {PACKAGE_NAME} package name alias is pointed at a binary rather than at the pipx CLI installation.
else
    echo "{PACKAGE_NAME} not found via pipx (or command failed). Skipping app upgrade."
fi

echo "--- Version {APP_NAME} ---"
# Execute the application
{PACKAGE_NAME} --version
# {PACKAGE_NAME} trend --default-idcs
"""
    try:
        upgrade_shortcut_file.write_text(upgrade_script_content, encoding='utf-8')
        os.chmod(upgrade_shortcut_file, 0o755)
        print(f"Successfully created Termux upgrade shortcut for pipx at: {upgrade_shortcut_file}")
    except Exception as e:
        print(f"Warning: Failed to set up Termux pipx upgrade shortcut: {e}")
    input("Press Enter to exit...")


def setup_termux_widget_executable_shortcut(force=False, shortcut_name=None):
    """
    Creates the Termux widget shortcut script if running in Termux and the 
    shortcut does not already exist. It uses the filename of the currently 
    running ELF executable (wrapper) for the command.
    """
    if not is_termux():
        return
    if shortcut_name is None:
        print(f"shortcut_name not provided")
        return
    
    # 1. Determine the name of the running executable (the ELF or PYZ binary)
    try:
        # sys.argv[0] is the path to the currently running executable (e.g., pipeline-0.2.1-aarch64).
        running_exec_path = Path(sys.argv[0])
        exec_filename = running_exec_path.name

    except IndexError:
        print("Warning: Could not determine running executable name from sys.argv. Aborting shortcut creation.", file=sys.stderr)
        return

    # Termux shortcut directory and file path
    home_dir = Path.home()
    shortcut_dir = home_dir / ".shortcuts"
    shortcut_file = shortcut_dir / shortcut_name

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
    script_content = f"""#!/usr/bin/env bash
# With this line, shortcuts will be treated the same as runnig from shell.
source $HOME/.bashrc 2>/dev/null || true

# Termux Widget/Shortcut Script
# This shortcut was automatically generated during first run.
# It targets the executable named '{exec_filename}'.

# Execute the application (The ELF or PYZ binary)
# Allows shortcut to be built for wherever the executable is running from, rather than assuming it is in $HOME
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

def register_shell_alias_executable_to_basrc(force=False, package_alias = None):
    """
    Registers a permanent shell alias for the ELF or PYZ binary in ~/.bashrc.
    This allows the user to run the app using the package name.
    """
    if package_alias is None:
        print(f"package_alias not provided")
        return
    # Termux setup needs to know which type of executable is running to create the best shortcut
    try:
        # Resolve the path to handle symlinks (Termux execution might involve one)
        exe_path = Path(sys.argv[0]).resolve() 
    except IndexError:
        print("Warning: Could not determine running executable name from sys.argv. Aborting alias.", file=sys.stderr)
        return

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
    # and executed with the full path to ensure it finds the ELF or PYZ binary.
    alias_content = f"""
{ALIAS_START_MARKER}
# Alias to easily run the standalone ELF or PYZ binary from any shell session
alias {package_alias}='"{exe_path}"'
{ALIAS_END_MARKER}
"""
    
    # 3. Append the new block to the content
    new_content = current_content.rstrip() + "\n" + alias_content.strip() + "\n"
    
    try:
        BASHRC_PATH.write_text(new_content)
        print(f"Registered shell alias '{package_alias}' in {BASHRC_PATH.name}.")
        print("Note: You must restart Termux or run 'source ~/.bashrc' for the alias to take effect.")
    except Exception as e:
        print(f"Error writing to {BASHRC_PATH.name} for alias: {e}")

# --- CLEAN UP / UNINSTALL ---

def _cleanup_shell_alias(package_alias = None):
    """
    Removes the shell alias block from ~/.bashrc and removes alias from env vars if present.
    """
    import subprocess
    if package_alias:
        # Check if the alias is defined (e.g., in bash)
        check_result = subprocess.run(f'alias {package_alias} &> /dev/null', 
                                    shell=True, 
                                    executable='/bin/bash', 
                                    check=False) 
        if check_result.returncode == 0:
            # use check=False to avoid errors if the alias does not exist, though it should exist at this point, due to check_result being 0
            print(f"Removing shell alias '{package_alias}' from current environment.")
            subprocess.run(['unalias', package_alias],check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    if is_elf():
        _remove_file_if_exists(shortcut_dir / SHORTCUT_NAME_ELF, "ELF shortcut")
        _cleanup_shell_alias(PACKAGE_ALIAS_ELF)
    elif is_pyz():
        _remove_file_if_exists(shortcut_dir / SHORTCUT_NAME_PYZ, "PYZ shortcut")
        _cleanup_shell_alias(PACKAGE_ALIAS_PYZ)
    elif is_pipx():
        _remove_file_if_exists(shortcut_dir / SHORTCUT_NAME_PIPX, "pipx shortcut")
        _remove_file_if_exists(shortcut_dir / UPGRADE_SHORTCUT_NAME, "pipx upgrade shortcut")
        # No alias to clean for pipx installations, as it is not created.
    
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
