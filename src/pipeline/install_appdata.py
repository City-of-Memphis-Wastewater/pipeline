# install_appdata.py
import typer
from pathlib import Path
import sys
import os
import shutil

app = typer.Typer(help="Manage mulch-like pipeline workspace installation")

def setup():
    platform = sys.platform
    if platform.startswith("win"):
        from mulch import reg_winreg
        # Always build LocalAppData mulch folder first

        # Copy files
        source_dir = Path(__file__).parent  # this is src/mulch/scripts/install
        target_dir = Path(os.environ['LOCALAPPDATA']) / "pipeline"
        target_dir.mkdir(parents=True, exist_ok=True)

        copy_mulch_installation_files(source_dir, target_dir)

        # Registry
        reg_winreg.call()
        reg_winreg.verify_registry()  # deterministic check

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

def copy_mulch_installation_files(source_dir, target_dir):
    required_files = [
        "call-mulch-workspace.ps1",
        "mulch-workspace.ps1",
        "call-mulch-seed.ps1",
        "mulch-seed.ps1",
        "mulch-icon.ico",
        ".mulchvision"
    ]
    missing_files = []
    for f in required_files:
        src = source_dir / f
        if src.exists():
            shutil.copy2(src, target_dir)
            print(f"Copied {f} to {target_dir}")
        else:
            missing_files.append(f)

    if missing_files:
        raise FileNotFoundError(
            f"Missing required files in {source_dir}: {', '.join(missing_files)}"
        )
    
@app.command()
def install_appdata():
    """Install the mulch workspace and mulch seed right-click context menu items."""
    setup()

if __name__ == "__main__":
    app()
