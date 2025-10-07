'''
Title: environment.py
Author: Clayton Bennett
Created: 23 July 2024
'''
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import platform
import sys
import os
import webbrowser
import shutil
from pathlib import Path

from pipeline.helpers import check_if_zip


def vercel():
    #return not(is_windows()) # conflated, when using any linux that is not a webserver
    # the important questions is actually "are we running on a webserver?"
    return False # hard code this

def matplotlib_enabled():
    #print(f"is_termux() = {is_termux()}")
    if is_termux():
        return False
    else:
        try:
            import matplotlib
            return True
        except ImportError:
            return False
        
def fbx_enabled():
    if is_termux():
        return False
    else:
        return True 
def is_linux():
    if 'linux' in platform.platform().lower():
        linux=True
    else:
        linux=False
    return linux

def is_termux():
    # There might be other android versions that can work with the rise od Debian on android in 2025, but for now, assume all android is termux.
    # I wonder how things would go on pydroid3
    return is_android()

def is_android():
    return "android" in platform.platform().lower()

def is_windows():
    if 'win' in platform.platform().lower():
        windows=True
    else:
        windows=False
    return windows
def is_apple():
    if 'darwin' in platform.platform().lower():
        apple=True
    else:
        apple=False
    return apple
    
def pyinstaller():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        pyinstaller = True
    else:
        pyinstaller = False
    return pyinstaller

def frozen():
    if getattr(sys, 'frozen', True):
        frozen = True
    else:
        frozen = False
    return frozen

def operatingsystem():
    return platform.system() #determine OS


def open_text_file_in_default_app(filepath):
    import subprocess
    """Opens a file with its default application based on the OS."""
    if is_windows():
        os.startfile(filepath)
    elif is_termux():
        subprocess.run(['nano', filepath])
    elif is_linux():
        subprocess.run(['xdg-open', filepath])
    elif is_apple():
        subprocess.run(['open', filepath])
    else:
        print("Unsupported operating system.")

def is_interactive_terminal():
    """Check if the script is running in an interactive terminal."""
    # Check if a tty is attached to stdin
    return sys.stdin.isatty() and sys.stdout.isatty()

def tkinter_is_available():
    """Check if tkinter is available and can be used."""
    try:
        import tkinter as tk
        #root = tk.Tk()
        #root.withdraw()  # Hide the main window
        #root.update()
        #root.destroy()
        return True
    except Exception:
        return False
    
# --- Browser Check Helper ---
def web_browser_is_available() -> bool:
    try:
        # 1. Standard Python check
        webbrowser.get()
        return True
    except webbrowser.Error:
        # Fallback needed. Check for external launchers.
        # 2. Termux specific check
        if shutil.which("termux-open-url"):
            return True
        # 3. General Linux check
        if shutil.which("xdg-open"):
            return True
        return False
    

def get_pipx_paths():
    """Returns the configured/default pipx binary and home directories."""
    # 1. PIPX_BIN_DIR (where the symlinks live, e.g., ~/.local/bin)
    pipx_bin_dir_str = os.environ.get('PIPX_BIN_DIR')
    if pipx_bin_dir_str:
        pipx_bin_path = Path(pipx_bin_dir_str).resolve()
    else:
        # Default binary path (common across platforms for user installs)
        pipx_bin_path = Path.home() / '.local' / 'bin'

    # 2. PIPX_HOME (where the isolated venvs live, e.g., ~/.local/pipx/venvs)
    pipx_home_str = os.environ.get('PIPX_HOME')
    if pipx_home_str:
        # PIPX_HOME is the base, venvs are in PIPX_HOME/venvs
        pipx_venv_base = Path(pipx_home_str).resolve() / 'venvs'
    else:
        # Fallback to the modern default for PIPX_HOME (XDG standard)
        # Note: pipx is smart and may check the older ~/.local/pipx too
        # but the XDG one is the current standard.
        pipx_venv_base = Path.home() / '.local' / 'share' / 'pipx' / 'venvs'

    return pipx_bin_path, pipx_venv_base.resolve()

def is_pipx(debug=False) -> bool:
    """Checks if the executable is running from a pipx managed environment."""
    try:
        # Helper for case-insensitivity on Windows
        def normalize_path(p: Path) -> str:
            return str(p).lower()

        exec_path = Path(sys.argv[0]).resolve()
        
        # This is the path to the interpreter running the script (e.g., venv/bin/python)
        # In a pipx-managed execution, this is the venv python.
        interpreter_path = Path(sys.executable).resolve()
        pipx_bin_path, pipx_venv_base_path = get_pipx_paths()

        if debug:
            # --- DEBUGGING OUTPUT ---
            print(f"DEBUG: EXEC_PATH:      {exec_path}")
            print(f"DEBUG: INTERP_PATH:    {interpreter_path}")
            print(f"DEBUG: PIPX_BIN_PATH:  {pipx_bin_path}")
            print(f"DEBUG: PIPX_VENV_BASE: {pipx_venv_base_path}")
            print(f"DEBUG: Check B result: {normalize_path(interpreter_path).startswith(normalize_path(pipx_venv_base_path))}")
        # ------------------------
        
        # Quick and dirty and probably sufficient check for if the executible is a pip intalled binary:
        if 'pipx/venvs' in normalize_path(exec_path) or 'pipx\\venvs' in normalize_path(exec_path):
            return True
        
        if exec_path != interpreter_path and normalize_path(exec_path).startswith(normalize_path(pipx_venv_base_path)):
            return True
        
        return False

    except Exception:
        # Fallback for unexpected path errors
        return False
    

def is_elf(exec_path : Path = None, debug=False) -> bool:
    """Checks if the currently running executable (sys.argv[0]) is a standalone PyInstaller-built ELF binary."""
    # If it's a pipx installation, it is not the monolithic binary we are concerned with here.
    
    if exec_path is None:    
        exec_path = Path(sys.argv[0]).resolve()
    if debug:
        print(f"exec_path = {exec_path}")
    if is_pipx():
        return False
    
    # Check if the file exists and is readable
    if not exec_path.is_file():
        return False
        
    try:
        # Check the magic number: The first four bytes of an ELF file are 0x7f, 'E', 'L', 'F' (b'\x7fELF').
        # This is the most reliable way to determine if the executable is a native binary wrapper (like PyInstaller's).
        with open(exec_path, 'rb') as f:
            magic_bytes = f.read(4)
        
        return magic_bytes == b'\x7fELF'
    except Exception:
        # Handle exceptions like PermissionError, IsADirectoryError, etc.
        return False
    
def is_pyz(exec_path: Path=None, debug=False) -> bool:
    """Checks if the currently running executable (sys.argv[0]) is a PYZ zipapp ."""
    # If it's a pipx installation, it is not the monolithic binary we are concerned with here.
    if exec_path is None:    
        exec_path = Path(sys.argv[0]).resolve()
    if debug:
        print(f"exec_path = {exec_path}")
    
    if is_pipx():
        return False
    
    # Check if the extension is PYZ
    if not str(exec_path).endswith(".pyz"):
        return False
    
    if not check_if_zip():
        return False