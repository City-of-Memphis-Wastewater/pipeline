# src/pipeline/appdata_setup.py
# install_appdata.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import typer
from pathlib import Path
import sys
import os
import shutil


app = typer.Typer(help="Manage mulch-like pipeline workspace installation")

def setup():
    platform = sys.platform
    if platform.startswith("win"):

        # Copy files
        source_dir = Path(__file__).parent  # 
        target_dir = Path(os.environ['LOCALAPPDATA']) / "pipeline_eds" ## configuration-example
        target_dir.mkdir(parents=True, exist_ok=True)


        # Registry
        #reg_winreg.call()
        #reg_winreg.verify_registry()  # deterministic check

        print("Mulch context menu installed successfully.")

    elif platform.startswith("linux"):
        thunar_action_dir = Path.home() / ".local/share/file-manager/actions"
        thunar_action_dir.mkdir(parents=True, exist_ok=True)

        menu_items = [
            ("mulch-workspace.desktop", "mulch workspace"),
            ("mulch-seed.desktop", "mulch seed"),
        ]

        for filename, label in menu_items:
            src = Path(__file__).parent / filename
            dest = thunar_action_dir / filename
            if src.exists():
                # Use copy2 to preserve metadata
                shutil.copy2(src, dest)
                os.chmod(dest, 0o755)
                print(f"Installed `{label}` context menu item to {dest}")
            else:
                print(f"Skipping `{label}` context menu installation (no .desktop file found).")

    elif platform == "darwin":
        print("macOS detected: please implement context menu setup via Automator or Finder Service")
        # You can extend this with AppleScript or Automator commands here
    else:
        raise RuntimeError(f"Unsupported platform for setup: {platform}")

@app.command()
def install_appdata():
    """Install the mulch workspace and mulch seed right-click context menu items."""
    setup()

if __name__ == "__main__":
    app()
