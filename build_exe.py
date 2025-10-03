import toml
import os
import sys
from pathlib import Path
from subprocess import run

# --- Configuration ---
# Your main application entry point (the file that contains your Typer app)
CLI_MAIN_FILE = Path('src/pipeline/cli.py')
# The name you want the final executable to have
EXE_NAME = 'pipeline-eds-cli'
# The generated resource file location
RC_FILE = Path('version.rc')
# The template file location
RC_TEMPLATE = Path('version.rc.template')
# --- End Configuration ---

def generate_rc_file():
    """Reads project version from pyproject.toml and generates the .rc file."""
    
    # 1. Read version from pyproject.toml
    try:
        data = toml.load('pyproject.toml')
        version = data['tool']['poetry']['version']
    except Exception as e:
        print(f"Error reading version from pyproject.toml: {e}")
        # Fallback version if TOML fails
        version = '0.0.0'
        
    version_tuple = tuple(map(int, version.split('.')))
    # Add a 0 for the 4th spot if the version is only major.minor.patch
    if len(version_tuple) == 3:
        version_tuple = version_tuple + (0,)
        
    print(f"Detected project version: {version}")
    
    # 2. Prepare substitution values
    substitutions = {
        'VERSION': version,
        'VERSION_TUPLE': ', '.join(map(str, version_tuple)),
    }
    
    # 3. Read template and write .rc file
    try:
        template_content = RC_TEMPLATE.read_text(encoding='utf-8')
        rc_content = template_content % substitutions
        
        RC_FILE.write_text(rc_content, encoding='utf-8')
        print(f"Generated resource file: {RC_FILE}")
    except Exception as e:
        print(f"Error generating {RC_FILE} from template: {e}")
        sys.exit(1)

def run_pyinstaller():
    """Runs the PyInstaller command using the generated .rc file."""
    
    # We use a list for subprocess to handle spaces correctly
    command = [
        'pyinstaller',
        '--onefile',
        f'--name={EXE_NAME}',
        f'--version-file={RC_FILE.name}',
        str(CLI_MAIN_FILE)
    ]
    
    # Use poetry run to ensure we use the poetry-managed pyinstaller
    print(f"Executing: poetry run {' '.join(command)}")
    
    # Use the 'run' function from subprocess (Python 3.7+ required)
    result = run(['poetry', 'run'] + command, check=False)

    if result.returncode != 0:
        print(f"PyInstaller failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    print("\n--- PyInstaller Build Complete ---")
    print(f"Executable is located at: dist\\{EXE_NAME}.exe")
    
    # Cleanup the generated file (optional)
    try:
        RC_FILE.unlink()
        print(f"Cleaned up generated file: {RC_FILE}")
    except OSError:
        pass


if __name__ == '__main__':
    generate_rc_file()
    run_pyinstaller()