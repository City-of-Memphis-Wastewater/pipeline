from __future__ import annotations
import os
import sys
import platform
from pathlib import Path
import subprocess

from pipeline.environment import is_windows
from pipeline.version_info import get_package_name 

# Importing winreg is necessary for proper Windows registry access.
# We wrap it in a try-except block for environments where it might not exist (e.g., development on Linux).
try:
    import winreg
except ImportError:
    winreg = None
    
# Constants
APP_NAME = get_package_name()
PACKAGE_NAME = get_package_name() # Used for executable name and AppData folder

def get_executable_path() -> Path | None:
    """
    Returns the path to the running executable (e.g., the PyInstaller .exe).
    
    Returns None if the application is running as a Python script (e.g., via 
    'python -m' or 'poetry run') to prevent setup from running with a source path.
    """
    if not is_windows():
        return None
    try:
        # sys.argv[0] is the path to the currently running entry point
        running_path = Path(sys.argv[0]).resolve()
        suffix = running_path.suffix.lower()

        # If the path ends in .py, assume it's running from source code.
        if suffix == '.py':
            return None
        
        # Only allow paths that explicitly look like deployed executables:
        # .exe (PyInstaller, or pipx shim) or .pyz (Shiv)
        if suffix in ['.exe', '.pyz']:
            return running_path
        
        # Reject anything else
        return None
    except IndexError:
        return None

def setup_windows_install():
    """
    Main dispatcher for all Windows-specific setup tasks.
    
    This function should be called during the first run of the application 
    on a Windows system.
    """
    if not is_windows():
        return

    exe_path = get_executable_path()
    if not exe_path:
        print("Error: Could not determine running executable path. Aborting Windows setup.")
        return

    print(f"Starting Windows setup for executable: {exe_path}")
    setup_appdata_dir()
    create_desktop_launcher(exe_path)
    register_context_menu(exe_path)
    # register_powertoys_integration(exe_path) # See function note below

def setup_appdata_dir() -> Path:
    """
    Ensures the application's configuration and data directory exists in AppData\Local.
    
    Returns the path to the configuration directory.
    """
    # Use environment variable for robustness
    local_appdata = os.environ.get('LOCALAPPDATA')
    if not local_appdata:
        # Fallback using Path.home()
        config_dir = Path.home() / "AppData" / "Local" / PACKAGE_NAME
    else:
        config_dir = Path(local_appdata) / PACKAGE_NAME
        
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        print(f"AppData configuration directory ensured: {config_dir}")
    except Exception as e:
        print(f"Warning: Failed to create AppData directory {config_dir}: {e}")
        
    return config_dir

def create_desktop_launcher(exe_path: Path):
    """
    Creates a simple BAT file on the user's desktop to launch the application.
    This is useful if the executable is buried deep in a build folder.
    """
    desktop_dir = Path.home() / "Desktop"
    bat_filename = f"Launch {APP_NAME}.bat"
    bat_path = desktop_dir / bat_filename

    # Simple BAT file content to execute the application
    # The '@echo off' prevents echoing the command. The double quotes handle spaces in paths.
    bat_content = f"""@echo off
REM Launcher for {APP_NAME}
"{exe_path}" %*
pause
"""
    try:
        bat_path.write_text(bat_content, encoding='utf-8')
        print(f"Desktop launcher created: {bat_path}")
    except Exception as e:
        print(f"Warning: Failed to create desktop launcher {bat_path}: {e}")

def register_context_menu_defunct(exe_path: Path):
    """
    Registers a context menu entry ("Open with EDS Plotter") when right-clicking 
    any file in Windows Explorer.
    """
    if winreg is None:
        print("Warning: 'winreg' module not available. Skipping context menu setup.")
        return

    # Registry path for adding an entry to all files (*)
    key_path = fr"Software\Classes\*\shell\{APP_NAME}"
    command_key_path = fr"Software\Classes\*\shell\{APP_NAME}\command"
    
    # The command to execute: 'C:\path\to\app.exe "%1"'
    # %1 represents the path of the file that was right-clicked.
    command_to_run = f'"{exe_path}" "%1"'

    try:
        # 1. Create the main key
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"Open with {APP_NAME}")
        winreg.CloseKey(key)

        # 2. Create the command key and set the execution string
        command_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, command_key_path)
        winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, command_to_run)
        winreg.CloseKey(command_key)
        
        print(f"Successfully registered context menu for all files: '{APP_NAME}'")
        print(f"Command: {command_to_run}")

    except Exception as e:
        print(f"Error registering context menu: {e}")


def register_context_menu(exe_path: Path):
    """
    Registers a context menu entry on folder background right-click that launches 
    a PowerShell script detailing installation and usage information.
    """
    if winreg is None:
        print("Warning: 'winreg' module not available. Skipping context menu setup.")
        return

    # 1. Determine AppData path and create PS1 file
    config_dir = setup_appdata_dir() # Use the existing function to get the AppData path
    ps1_filename = f"setup_info_{PACKAGE_NAME}.ps1"
    ps1_path = config_dir / ps1_filename

    # Content of the PowerShell script, including pipx info and example command
    ps1_content = f"""Write-Host "--- {APP_NAME} Installation and Usage Information ---"
Write-Host ""
Write-Host "To install the application system-wide for easy access (if pipx is installed):"
Write-Host "  pipx install {PACKAGE_NAME}"
Write-Host "Then you can run the application directly from any terminal:"
Write-Host "  {PACKAGE_NAME} trend --default-idcs"
Write-Host ""
Write-Host "Current Executable Path:"
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
        print(f"Generated PowerShell script: {ps1_path}")
    except Exception as e:
        print(f"Error generating PowerShell script: {e}")
        return

    # 2. Define Registry paths and command
    # Targeting the folder background context menu (right-click in empty space in a folder)
    key_path = fr"Software\Classes\Directory\Background\shell\{APP_NAME} Setup"
    command_key_path = fr"Software\Classes\Directory\Background\shell\{APP_NAME} Setup\command"
    
    # The command executes the PS1 script using PowerShell with execution policy bypassed
    command_to_run = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{ps1_path}"'

    try:
        # 3. Create the main key
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"[{APP_NAME}] Installation & Info")
        winreg.CloseKey(key)

        # 4. Create the command key and set the execution string
        command_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, command_key_path)
        winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, command_to_run)
        winreg.CloseKey(command_key)
        
        print(f"Successfully registered context menu for folder backgrounds: '{APP_NAME} Setup'")
        print(f"Command: {command_to_run}")

    except Exception as e:
        print(f"Error registering context menu: {e}")

def register_powertoys_integration(exe_path: Path):
    """
    Placeholder for more advanced OS-level integration (e.g., Clipboard/PowerToys).
    
    True PowerToys integration is complex and usually requires custom modules or
    monitoring external events, which is outside the scope of a simple install script.
    
    A simpler OS-level access point could be:
    1. Registering a custom URI scheme (e.g., 'edsplot://data?...')
    2. Registering a custom Keyboard Shortcut handler (less common for apps)
    
    For a desktop app, the best approach for "text copied to the clipboard" 
    is usually an **optional internal clipboard monitor** running in the background, 
    not a registry change. We leave this function as a placeholder.
    """
    print("\n--- PowerToys/Advanced Integration Note ---")
    print("Advanced clipboard monitoring or PowerToys integration must be handled within the application.")
    print("Consider registering a custom URI scheme (e.g., 'edsplot://') in the registry for deep links.")
    

def cleanup_desktop_launcher():
    """Removes the desktop BAT file launcher."""
    desktop_dir = Path.home() / "Desktop"
    bat_filename = f"Launch {APP_NAME}.bat"
    bat_path = desktop_dir / bat_filename
    
    if bat_path.exists():
        try:
            bat_path.unlink()
            print(f"Cleaned up desktop launcher: {bat_path}")
        except Exception as e:
            print(f"Warning: Failed to delete desktop launcher {bat_path}: {e}")

def cleanup_appdata_script():
    """Removes the PowerShell setup information script from AppData."""
    config_dir = setup_appdata_dir()
    ps1_filename = f"setup_info_{PACKAGE_NAME}.ps1"
    ps1_path = config_dir / ps1_filename

    if ps1_path.exists():
        try:
            # We only delete the script, leaving the main AppData folder in place
            ps1_path.unlink()
            print(f"Cleaned up AppData script: {ps1_path}")
        except Exception as e:
            print(f"Warning: Failed to delete AppData script {ps1_path}: {e}")
            
def cleanup_context_menu_registry():
    """Removes the context menu entries from the Windows Registry."""
    if winreg is None:
        return
        
    key_path = fr"Software\Classes\Directory\Background\shell\{APP_NAME} Setup"
    
    try:
        # Must delete the subkey (command) before the main key
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path + r"\command")
        print(f"Cleaned up registry command subkey.")
    except FileNotFoundError:
        pass # Subkey already gone
    except Exception as e:
        print(f"Error cleaning up registry command subkey: {e}")
        
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        print(f"Cleaned up registry main key: {key_path}")
    except FileNotFoundError:
        pass # Main key already gone
    except Exception as e:
        print(f"Error cleaning up registry main key: {e}")

def cleanup_windows_install():
    """
    Performs full uninstallation cleanup of all artifacts created by 
    setup_windows_install.
    
    This function should be called when the application is uninstalled or 
    to remove corrupted setup artifacts.
    """
    if not is_windows():
        return
        
    print(f"Starting Windows uninstallation cleanup for {APP_NAME}...")
    cleanup_desktop_launcher()
    cleanup_appdata_script()
    cleanup_context_menu_registry()
    print("Windows cleanup complete.")

# Example of how this might be executed during application startup:
# if __name__ == "__main__":
#     setup_windows_install()