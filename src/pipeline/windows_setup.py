from __future__ import annotations
import os
import sys
import platform
from pathlib import Path
import subprocess
import datetime

from pipeline.environment import is_windows
from pipeline.version_info import get_package_name, get_package_version

# Importing winreg is necessary for proper Windows registry access.
# We wrap it in a try-except block for environments where it might not exist (e.g., development on Linux).
try:
    import winreg
except ImportError:
    winreg = None
    
# Constants
APP_NAME = get_package_name()
PACKAGE_NAME = get_package_name() # Used for executable name and AppData folder
INSTALL_VERSION = get_package_version()
PACKAGE_ALIAS_EXE = f"{get_package_name()}-exe" # alias for non-pipx binary
PACKAGE_ALIAS_PYZ = f"{get_package_name()}-pyz"
INSTALL_VERSION_FILE = "install_version.txt"
LOG_FILE = "install_log.txt" # New constant for logging

# --- Logging Helpers ---

def _get_log_path() -> Path:
    """Returns the full path to the installation log file."""
    return setup_appdata_dir() / LOG_FILE

def log_message(message: str, is_error: bool = False):
    """Writes a timestamped message to the installation log file."""
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_line = f"{timestamp} {'[ERROR]' if is_error else '[INFO]'}: {message}"
    
    # We must try to get the log path, but cannot rely on setup_appdata_dir being
    # fully successful or being called before setup_appdata_dir is complete.
    try:
        log_path = _get_log_path()
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    except Exception:
        # Fallback to console print if logging to file fails (e.g., permissions)
        if is_error:
            # Print errors to the console, even during silent operation
            print(f"FATAL LOGGING ERROR: {log_line}", file=sys.stderr)
        else:
            # We skip printing non-error messages to the console here to ensure silence
            pass

# --- Environment and Path Functions ---

def is_windows() -> bool:
    """Checks if the current operating system is Windows."""
    return platform.system() == "Windows"

def get_executable_path() -> Path | None:
    """
    Returns the path to the running executable (e.g., the PyInstaller .exe or shiv .pyz).
    
    Returns None if the application is running as a Python script (e.g., via 
    'python -m' or 'poetry run') to prevent setup from running with a source path.
    """
    if not is_windows():
        return None
    try:
        # sys.argv[0] is the path to the currently running entry point
        running_path = Path(sys.argv[0]).resolve()
        
        suffix = running_path.suffix.lower()
        
        # Only allow paths that explicitly look like deployed executables:
        # .exe (PyInstaller, or pipx shim) or .pyz (Shiv)
        if suffix in ['.exe', '.pyz']:
            return running_path
            
        # Reject anything else, including .py files or generic interpreter paths.
        return None
    except IndexError:
        return None

def setup_appdata_dir() -> Path:
    """
    Ensures the application's configuration and data directory exists in AppData\Local.
    
    Returns the path to the configuration directory.
    """
    # Use environment variable for robustness
    if not is_windows():
        return
    local_appdata = os.environ.get('LOCALAPPDATA')
    if not local_appdata:
        # Fallback using Path.home()
        config_dir = Path.home() / "AppData" / "Local" / PACKAGE_NAME
    else:
        config_dir = Path(local_appdata) / PACKAGE_NAME
        
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        # We don't log success here, as this function is called repeatedly.
    except Exception as e:
        # Use simple print as logging system relies on this dir existing
        print(f"Warning: Failed to create AppData directory {config_dir}: {e}", file=sys.stderr)
        
    return config_dir

def check_if_installed(exe_path: Path) -> bool:
    """
    Checks if the current application version has already performed setup.
    Installation is tied to the unique executable path.
    """
    config_dir = setup_appdata_dir()
    version_file = config_dir / INSTALL_VERSION_FILE
    
    if not version_file.exists():
        log_message(f"Version file {INSTALL_VERSION_FILE} not found. Proceeding with installation.")
        return False

    try:
        content = version_file.read_text().splitlines()
        
        if len(content) < 2:
            log_message("Version file is corrupt/incomplete. Reinstalling artifacts.", is_error=True)
            return False

        current_installed_version = content[0].strip()
        installed_exe_path = content[1].strip()
        
        is_same_version = current_installed_version == INSTALL_VERSION
        is_same_executable = installed_exe_path == str(exe_path)
        
        if not is_same_version:
            log_message(f"Found version {current_installed_version}, expected {INSTALL_VERSION}. Proceeding with update.", is_error=False)

        if not is_same_executable:
            log_message(f"Installed EXE path {installed_exe_path} does not match current path {exe_path}. Proceeding with update.", is_error=False)

        # We only consider it installed if both version and executable path match.
        return is_same_version and is_same_executable
        
    except Exception as e:
        log_message(f"Error reading installation version file: {e}. Reinstalling artifacts.", is_error=True)
        return False

def finalize_install_version(exe_path: Path):
    """Writes the installation marker file after a successful setup."""
    config_dir = setup_appdata_dir()
    version_file = config_dir / INSTALL_VERSION_FILE
    
    content = f"{INSTALL_VERSION}\n{exe_path}"
    
    try:
        version_file.write_text(content, encoding='utf-8')
        log_message(f"Installation version {INSTALL_VERSION} marked as installed for executable: {exe_path}")
    except Exception as e:
        log_message(f"Error writing installation version file: {e}", is_error=True)

# --- Setup Dispatcher ---

def setup_windows_install():
    """
    Main dispatcher for all Windows-specific setup tasks.
    
    This function should be called during the first run of the application 
    on a Windows system. It now includes a version check to prevent running 
    on every startup, and logs verbose output instead of printing it.
    """
    if not is_windows():
        return

    # 1. Ensure AppData is set up first, so we have a log file location
    config_dir = setup_appdata_dir()
    
    # 2. Get the executable path
    exe_path = get_executable_path()
    if not exe_path:
        # Use simple print for this critical error, as installation won't proceed
        #print("Error: Could not determine running executable path (likely running from source). Aborting Windows setup.", file=sys.stderr)
        return
    else:
        print("pipeline.windows_setup.setup_windows_install() ...")
    
    short_path_ref = fr"%LOCALAPPDATA%\{PACKAGE_NAME}"

    # 3. Check if already installed
    if check_if_installed(exe_path):
        # Print a concise status message instead of the verbose setup prints
        print(f"[{APP_NAME}] {short_path_ref} is set up (v{INSTALL_VERSION}). Skipping setup.")
        return

    log_message(f"Starting NEW/UPDATE Windows setup for executable: {exe_path}")
    
    try:
        # Run setup tasks
        create_desktop_launcher(exe_path)
        register_context_menu(exe_path)
        register_powertoys_integration(exe_path)
        
        # Write version file only if all setup completed successfully
        finalize_install_version(exe_path)
        
        # 4. Success message to console
        print(f"[{APP_NAME}] {short_path_ref} is set up. Check log file at {config_dir / LOG_FILE} for details.")

    except Exception as e:
        log_message(f"FATAL ERROR during Windows setup: {e}", is_error=True)
        print(f"[{APP_NAME}] Setup failed. Check log file at {config_dir / LOG_FILE} for errors.", file=sys.stderr)


# --- Setup Sub-Functions (Modified to use logging) ---

def create_desktop_launcher(exe_path: Path):
    """
    Creates a simple BAT file on the user's desktop to launch the application.
    This is useful if the executable is buried deep in a build folder.
    """
    desktop_dir = Path.home() / "Desktop"
    bat_filename = f"Launch {APP_NAME}.bat"
    bat_path = desktop_dir / bat_filename

    # Simple BAT file content to execute the application
    bat_content = f"""@echo off
REM Launcher for {APP_NAME}
"{exe_path}" %*
pause
"""
    try:
        bat_path.write_text(bat_content, encoding='utf-8')
        log_message(f"Desktop launcher created: {bat_path}")
    except Exception as e:
        log_message(f"Warning: Failed to create desktop launcher {bat_path}: {e}", is_error=True)

def create_start_menu_shortcut(exe_path: Path):
    """
    Creates a simple BAT file in the user's Start Menu Programs folder.
    Windows will treat this BAT file as a Start Menu shortcut.
    """
    try:
        # Standard location for the user's Start Menu Programs folder
        start_menu_path = Path(os.environ['APPDATA']) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        start_menu_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        log_message(f"Warning: Failed to locate or create Start Menu path: {e}", is_error=True)
        return

    bat_filename = f"{APP_NAME} Launch.bat"
    bat_path = start_menu_path / bat_filename

    # Simple BAT file content to execute the application silently
    bat_content = f"""@echo off
REM Start Menu Launcher for {APP_NAME}
"{exe_path}" %*
""" # Note: removed pause for cleaner Start Menu launch

    try:
        bat_path.write_text(bat_content, encoding='utf-8')
        log_message(f"Start Menu shortcut created: {bat_path}")
    except Exception as e:
        log_message(f"Warning: Failed to create Start Menu shortcut {bat_path}: {e}", is_error=True)



def register_context_menu(exe_path: Path):
    """
    Registers a context menu entry on folder background right-click that launches 
    a PowerShell script detailing installation and usage information.
    """
    if winreg is None:
        log_message("Warning: 'winreg' module not available. Skipping context menu setup.", is_error=True)
        return

    # 1. Determine AppData path and create PS1 file
    config_dir = setup_appdata_dir()
    ps1_filename = f"setup_info_{PACKAGE_NAME}.ps1"
    ps1_path = config_dir / ps1_filename
    
    # Determine the executable type for clarity in the PS script (e.g., EXE, PYZ)
    exe_type = exe_path.suffix.upper().lstrip('.') if exe_path.suffix else "UNKNOWN"

    # Content of the PowerShell script, including pipx info and example command
    ps1_content = f"""Write-Host "--- {APP_NAME} Installation and Usage Information ---"
Write-Host ""
Write-Host "This utility can be downloaded as a standalone PYZ, EXE, or ELF file from the GitHub Releases page:"
Write-Host "  https://github.com/City-of-Memphis-Wastewater/pipeline/releases"
Write-Host ""
Write-Host "To install the application system-wide for easy access (if pipx is installed):"
Write-Host "  pipx install {PACKAGE_NAME}"
Write-Host "Then you can run the application directly from any terminal:"
Write-Host "  {PACKAGE_NAME} trend --default-idcs"
Write-Host ""
Write-Host "Current Executable Path (Type: {exe_type}):"
Write-Host "  {exe_path}"
Write-Host "Example Execution using current file:"
Write-Host "  & '{exe_path}' trend --default-idcs"
Write-Host ""
Write-Host "The app data folder is located at: {config_dir}"
Write-Host ""
Pause
"""

    try:
        ps1_path.write_text(ps1_content, encoding='utf-8')
        log_message(f"Generated PowerShell script: {ps1_path}")
    except Exception as e:
        log_message(f"Error generating PowerShell script: {e}", is_error=True)
        return

    # 2. Define Registry paths and command
    key_path = fr"Software\Classes\Directory\Background\shell\{APP_NAME} Setup"
    command_key_path = fr"Software\Classes\Directory\Background\shell\{APP_NAME} Setup\command"
    
    command_to_run = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{ps1_path}"'

    try:
        # 3. Create the main key
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"[{APP_NAME}] Info")
        winreg.CloseKey(key)

        # 4. Create the command key and set the execution string
        command_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, command_key_path)
        winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, command_to_run)
        winreg.CloseKey(command_key)
        
        log_message(f"Successfully registered context menu for folder backgrounds: '{APP_NAME} Setup'")
        log_message(f"Command: {command_to_run}")

    except Exception as e:
        log_message(f"Error registering context menu: {e}", is_error=True)



def register_powertoys_integration(exe_path: Path):
    """
    Placeholder for more advanced OS-level integration (e.g., Clipboard/PowerToys).
    """
    log_message("\n--- PowerToys/Advanced Integration Note ---")
    log_message("Advanced clipboard monitoring or PowerToys integration must be handled within the application.")
    log_message("Consider registering a custom URI scheme (e.g., 'edsplot://') in the registry for deep links.")
    

# --- Cleanup Sub-Functions (Modified to use logging) ---

def cleanup_desktop_launcher():
    """Removes the desktop BAT file launcher."""
    desktop_dir = Path.home() / "Desktop"
    bat_filename = f"Launch {APP_NAME}.bat"
    bat_path = desktop_dir / bat_filename
    
    if bat_path.exists():
        try:
            bat_path.unlink()
            log_message(f"Cleaned up desktop launcher: {bat_path}")
        except Exception as e:
            log_message(f"Warning: Failed to delete desktop launcher {bat_path}: {e}", is_error=True)

def cleanup_start_menu_shortcut():
    """Removes the Start Menu BAT file launcher."""
    try:
        start_menu_path = Path(os.environ['APPDATA']) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    except KeyError:
        log_message("Warning: APPDATA environment variable not set. Skipping Start Menu cleanup.", is_error=True)
        return

    bat_filename = f"{APP_NAME} Launch.bat"
    bat_path = start_menu_path / bat_filename
    
    if bat_path.exists():
        try:
            bat_path.unlink()
            log_message(f"Cleaned up Start Menu shortcut: {bat_path}")
        except Exception as e:
            log_message(f"Warning: Failed to delete Start Menu shortcut {bat_path}: {e}", is_error=True)

def cleanup_credential_manager_keyring_entries():
    """
    Placeholder for remocing key ring items from Windows Credential Manager.
    A consistent username relevant to pipeline can be used for easy removal."
    """
    # We must define all added credentials discern which are relevant to pipeline.
    from keyring.errors import PasswordDeleteError
    try:
        keyring.delete_password("service_name_placeholder", "username_placeholder")
    except PasswordDeleteError:
        pass
def cleanup_appdata_script():
    """Removes the PowerShell setup information script from AppData."""
    config_dir = setup_appdata_dir()
    ps1_filename = f"setup_info_{PACKAGE_NAME}.ps1"
    ps1_path = config_dir / ps1_filename

    if ps1_path.exists():
        try:
            # We only delete the script, leaving the main AppData folder in place
            ps1_path.unlink()
            log_message(f"Cleaned up AppData script: {ps1_path}")
        except Exception as e:
            log_message(f"Warning: Failed to delete AppData script {ps1_path}: {e}", is_error=True)

def cleanup_install_version_file():
    """Removes the installation version marker file."""
    config_dir = setup_appdata_dir()
    version_file = config_dir / INSTALL_VERSION_FILE
    
    if version_file.exists():
        try:
            version_file.unlink()
            log_message(f"Cleaned up installation version file: {version_file.name}")
        except Exception as e:
            log_message(f"Warning: Failed to delete version file {version_file}: {e}", is_error=True)
            
def cleanup_appdata_dir_if_empty():
    """
    Removes the main AppData folder if it is empty after artifact cleanup.
    """
    config_dir = setup_appdata_dir()
    try:
        # Check if the directory is empty.
        if not os.listdir(config_dir):
            config_dir.rmdir()
            log_message(f"Cleaned up empty AppData directory: {config_dir}")
        else:
            log_message(f"AppData directory {config_dir} is not empty. Leaving it in place to protect user data.")
    except FileNotFoundError:
        log_message(f"AppData directory {config_dir} not found during cleanup.", is_error=False)
    except OSError as e:
        # OSError is raised if rmdir fails because the directory is not empty or locked
        log_message(f"Warning: Could not remove AppData directory {config_dir}: {e}", is_error=True)
    except Exception as e:
        log_message(f"Warning: Failed to clean up AppData directory {config_dir}: {e}", is_error=True)
            
def cleanup_context_menu_registry():
    """Removes the context menu entries from the Windows Registry."""
    if winreg is None:
        return
        
    key_path = fr"Software\Classes\Directory\Background\shell\{APP_NAME} Setup"
    
    try:
        # Must delete the subkey (command) before the main key
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path + r"\command")
        log_message(f"Cleaned up registry command subkey.")
    except FileNotFoundError:
        log_message(f"Registry command subkey not found during cleanup.")
    except Exception as e:
        log_message(f"Error cleaning up registry command subkey: {e}", is_error=True)
        
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        log_message(f"Cleaned up registry main key: {key_path}")
    except FileNotFoundError:
        log_message(f"Registry main key not found during cleanup.")
    except Exception as e:
        log_message(f"Error cleaning up registry main key: {e}", is_error=True)

def cleanup_windows_install():
    """
    Performs full uninstallation cleanup of all artifacts created by 
    setup_windows_install.
    """
    if not is_windows():
        return
        
    # We must print the start of cleanup since the main loop needs to know
    print(f"Starting Windows uninstallation cleanup for {APP_NAME}...") 
    
    cleanup_desktop_launcher()
    cleanup_start_menu_shortcut() 
    cleanup_context_menu_registry()
    cleanup_install_version_file() # Ensure this goes before attempting to remove the directory
    cleanup_appdata_script()
    cleanup_appdata_dir_if_empty()
    cleanup_credential_manager_keyring_entries()
    
    print("Windows cleanup complete.")

# Example of how this might be executed during application startup:
# if __name__ == "__main__":
#     setup_windows_install()
