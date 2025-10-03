# build_executible.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import toml
import os
import sys
from pathlib import Path
from subprocess import run

"""
Builds an EXE when run on Windows 
Builds an ELF binary when run on Linunx
How to run:
    poetry run python build_executible.py
"""

# --- Configuration ---
# Global flag to check if we are building for Windows (assuming this is defined elsewhere)
IS_WINDOWS_BUILD = sys.platform.startswith('win')
# Configuration variables (assuming these are defined elsewhere)
RC_TEMPLATE = Path('version.rc.template')
RC_FILE = Path('version.rc')
CLI_MAIN_FILE = Path('src/pipeline/cli.py')
EXE_NAME = 'pipeline-eds-cli' # Will be made dynamic later

# --- NEW FUNCTION: Version Retrieval ---
def get_project_version() -> str:
    """Reads project version from pyproject.toml."""
    try:
        data = toml.load('pyproject.toml')
        version = data['tool']['poetry']['version']
    except Exception as e:
        print(f"Error reading version from pyproject.toml: {e}", file=sys.stderr)
        # Fallback version if TOML fails
        version = '0.0.0'
        
    print(f"Detected project version: {version}")
    return version

# --- Refactored RC File Generation ---
def generate_rc_file(version: str):
    """Generates the .rc file using the provided version string."""
    if not IS_WINDOWS_BUILD:
        print("Skipping .rc file generation (Not building on Windows).")
        return
        
    version_tuple = tuple(map(int, version.split('.')))
    # Add a 0 for the 4th spot if the version is only major.minor.patch
    if len(version_tuple) == 3:
        version_tuple = version_tuple + (0,)
        
    # 1. Prepare substitution values
    substitutions = {
        'VERSION': version,
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

# --- (Example for your future dynamic naming function) ---
def get_dynamic_exe_name(version: str) -> str:
    # 1. Read package name from pyproject.toml
    try:
        data = toml.load('pyproject.toml')
        pkg_name = data['tool']['poetry']['name']
    except:
        pkg_name = 'pipeline-eds' # Fallback
        
    py_major = sys.version_info.major
    py_minor = sys.version_info.minor
    py_version = f"py{py_major}{py_minor}"
    
    # Use hyphens for the CLI/EXE name
    return f"{pkg_name}-{version}-{py_version}"

# --- Refactored Main Execution Block ---
# Assuming run_pyinstaller has been updated to take the dynamic name
def run_pyinstaller(dynamic_exe_name: str):
    # ... (Your previous PyInstaller logic goes here, using dynamic_exe_name) ...
    # This is placeholder logic to show how the name is used:
    
    command = [
        'pyinstaller',
        '--onefile',
        f'--name={dynamic_exe_name}',
        # ... rest of the command logic ...
        str(CLI_MAIN_FILE)
    ]
    
    if IS_WINDOWS_BUILD:
        command.insert(3, f'--version-file={RC_FILE.name}')
    
    print(f"Executing: poetry run {' '.join(command)}")
    result = run(['poetry', 'run'] + command, check=False)

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
    project_version = get_project_version()
    
    # 1. Generate RC file (conditionally)
    generate_rc_file(project_version)
    
    # 2. Determine the executable name
    dynamic_name = get_dynamic_exe_name(project_version)
    
    # 3. Run the installer
    run_pyinstaller(dynamic_name)