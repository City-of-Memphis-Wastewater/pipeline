# pipeline/install_termux.py
import os
from pathlib import Path
from pipeline.environment import is_termux

def setup_termux_shortcut():
    """
    Creates the Termux widget shortcut script if running in Termux and the 
    shortcut does not already exist.
    """
    if not is_termux():
        return

    # Termux shortcut directory and file path
    home_dir = Path.home()
    shortcut_dir = home_dir / ".shortcuts"
    shortcut_file = shortcut_dir / "run_eds_plot.sh"

    if shortcut_file.exists():
        # Shortcut is already set up, nothing to do
        return

    # 1. Ensure the .shortcuts directory exists
    try:
        shortcut_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Failed to create Termux shortcut directory {shortcut_dir}: {e}")
        return

    # 2. Define the content of the script
    # We use the pipx executable name directly as it is on the PATH.
    script_content = f"""#!/data/data/com.termux/files/usr/bin/bash

# Termux Widget/Shortcut Script for EDS Plotter
# This shortcut was automatically generated during first run.
$HOME/.local/bin/eds --version 
$HOME/.local/bin/eds trend --default-idcs
"""

    # 3. Write the script to the file
    try:
        shortcut_file.write_text(script_content, encoding='utf-8')
    except Exception as e:
        print(f"Warning: Failed to write Termux shortcut file {shortcut_file}: {e}")
        return

    # 4. Make the script executable (chmod +x)
    try:
        os.chmod(shortcut_file, 0o755)
        print(f"Successfully created Termux shortcut at: {shortcut_file}")
        print("Please restart the Termux app or wait a moment for the widget to update.")
    except Exception as e:
        print(f"Warning: Failed to set executable permissions on {shortcut_file}: {e}")