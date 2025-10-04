import sys
import shutil
from subprocess import run

"""
Automates the generation of a requirements-dev.txt file from pyproject.toml
using the standard 'poetry export' command.

This script ensures that both main and development dependencies are included,
as is standard for development environments.

How to run:
    python generate_requirements.py
"""

REQUIREMENTS_DEV_FILE = "requirements-dev.txt"

def generate_dev_requirements():
    """
    Executes 'poetry export' to generate the requirements-dev.txt file.
    
    Checks for Poetry availability first and includes both main and dev groups.
    """
    if not shutil.which('poetry'):
        print("Error: 'poetry' executable not found in PATH.")
        print("Cannot generate the requirements file without Poetry installed.")
        sys.exit(1)
    
    # We use '--with dev' to include the development group alongside the main dependencies.
    # '--without-hashes' is recommended for compatibility when sharing/installing the file.
    command = [
        'poetry',
        'export',
        '--with',
        'dev',
        '--output',
        REQUIREMENTS_DEV_FILE,
        '--without-hashes' 
    ]
    
    print(f"Executing: {' '.join(command)}")
    
    # Run the command
    result = run(command, check=False)

    if result.returncode == 0:
        print(f"\nSuccessfully generated {REQUIREMENTS_DEV_FILE}")
        print("This file contains all main dependencies and all dev dependencies.")
    else:
        print(f"\nError: Poetry export failed with exit code {result.returncode}", file=sys.stderr)
        print("Please ensure your Poetry environment is locked (run 'poetry lock') before exporting.")
        sys.exit(result.returncode)


if __name__ == '__main__':
    generate_dev_requirements()