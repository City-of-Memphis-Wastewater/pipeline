# build_executable.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import os
from pathlib import Path
import shutil
from subprocess import run
import sys
import toml
from pipeline_eds.version_info import get_package_name, get_package_version, get_python_version, form_dynamic_binary_name
from pipeline_eds.system_info import SystemInfo

"""
Builds an EXE when run on Windows 
Builds an ELF binary when run on Linunx
How to run:
    poetry run python build_executable.py
"""

# --- Configuration ---
# Global flag to check if we are building for Windows (assuming this is defined elsewhere)
IS_WINDOWS_BUILD = sys.platform.startswith('win')
# Configuration variables (assuming these are defined elsewhere)
RC_TEMPLATE = Path('version.rc.template')
RC_FILE = Path('version.rc')
CLI_MAIN_FILE = Path('src/pipeline/cli.py')
EXE_NAME = 'pipeline-eds-cli' # Will be made dynamic later

# --- RC File Generation ---
def generate_rc_file(package_version: str):
    """Generates the .rc file using the provided version string."""
    if not IS_WINDOWS_BUILD:
        print("Skipping .rc file generation (Not building on Windows).")
        return
        
    version_tuple = tuple(map(int, package_version.split('.')))
    # Add a 0 for the 4th spot if the version is only major.minor.patch
    if len(version_tuple) == 3:
        version_tuple = version_tuple + (0,)
        
    # 1. Prepare substitution values
    substitutions = {
        'VERSION': package_version,
        'VERSION_TUPLE': ', '.join(map(str, version_tuple)),
    }
    
    # 2. Read template and write .rc file
    try:
        template_content = RC_TEMPLATE.read_text(encoding='utf-8')
        # Use simple string formatting (as you did)
        rc_content = template_content % substitutions
        
        RC_FILE.write_text(rc_content, encoding='utf-8')
        print(f"Generated resource file: {RC_FILE}")
    except Exception as e:
        print(f"Error generating {RC_FILE} from template: {e}", file=sys.stderr)
        sys.exit(1)


# --- Main Execution Block ---
# Assuming run_pyinstaller has been updated to take the dynamic name
def run_pyinstaller(dynamic_exe_name: str):
    
    # 1. Build the base PyInstaller command
    base_command = [
        'pyinstaller',
        '--onefile',
        f'--name={dynamic_exe_name}',
        # ... rest of the command logic ...
        str(CLI_MAIN_FILE)
    ]
    if IS_WINDOWS_BUILD:
        base_command.insert(3, f'--version-file={RC_FILE.name}')
    
    # 2. Determine the full command using shutil.which for availability check
    if shutil.which('poetry'):
        # Poetry is available, prepend 'poetry run'
        full_command = ['poetry', 'run'] + base_command
        print(f"Attempting with Poetry: {' '.join(full_command)}")
    else:
        # Poetry is not available, run PyInstaller directly
        full_command = base_command
        print("Poetry executable not found. Running PyInstaller directly.")
        print(f"Executing: {' '.join(full_command)}")
    
    # 3. Execute the command
    result = run(full_command, check=False)
    
    if result.returncode != 0:
        print(f"PyInstaller failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

    print("\n--- PyInstaller Build Complete ---")
    ext = '.exe' if IS_WINDOWS_BUILD else ''
    print(f"Executable is located at: dist/{dynamic_exe_name}{ext}")
    
    if IS_WINDOWS_BUILD:
        try:
            RC_FILE.unlink()
            print(f"Cleaned up generated file: {RC_FILE}")
        except OSError:
            pass


if __name__ == '__main__':
    package_name = get_package_name()
    package_version = get_package_version() 
    py_version = get_python_version()
    
    sysinfo = SystemInfo()
    os_tag = sysinfo.get_os_tag()
    architecture = sysinfo.get_arch()

    # 1. Generate RC file (conditionally, on Windows)
    generate_rc_file(package_version)
    
    # 2. Determine the executable name (without the extension)
    executable_descriptor = form_dynamic_binary_name(package_name, package_version, py_version, os_tag, architecture)
    
    # 3. Run the installer
    run_pyinstaller(executable_descriptor)