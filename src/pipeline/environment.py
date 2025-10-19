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
import subprocess

from pipeline.helpers import check_if_zip

# Global cache for tkinter availability
_TKINTER_AVAILABILITY: bool | None = None


def matplotlib_enabled():
    """Check if matplotlib is available, excluding Termux environment."""
    if is_termux():
        return False
    else:
        try:
            import matplotlib
            return True
        except ImportError:
            return False


def is_termux() -> bool:
    """Detect if running in Termux environment on Android, based on Termux-specific environmental variables."""
    
    if platform.system() != 'Linux':
        return False
    
    termux_path_prefix = '/data/data/com.termux'
    
    # Termux-specific environment variable ($PREFIX)
    # The actual prefix is /data/data/com.termux/files/usr
    if os.environ.get('PREFIX', default='').startswith(termux_path_prefix + '/usr'):
        return True
    
    # Termux-specific environment variable ($HOME)
    # The actual home is /data/data/com.termux/files/home
    if os.environ.get('HOME', default='').startswith(termux_path_prefix + '/home'):
        return True

    # Code insight: The os.environ.get command returns the default if the key is not found. None is retured if a default is not speficied.
    
    # Termux-specific environment variable ($TERMUX_VERSION)
    if 'TERMUX_VERSION' in os.environ:
        return True
    
    return False

def is_freebsd() -> bool:
    """Detect if running on FreeBSD."""
    return platform.system() == 'FreeBSD'

def is_linux():
    """Detect if running on Linux."""
    return platform.system() == 'Linux' 

def is_android() -> bool:
    """
    Detect if running on Android.
    
    Note: The is_termux() function is more robust and safe for Termux.
    Checking for Termux does not require checking for Android.

    is_android() will be True on:
        - Sandboxed IDE's:
            - Pydroid3
            - QPython
        - `proot` user-space containters:
            - Termux
            - Andronix
            - UserLand

    Virtual Machines: Full VMs like VirtualBox or VMware run a fully virtualized kernel 
    (e.g., standard Linux kernel), 
    completely isolating the Python script from the Android host, 
    correctly causing this check to return False.
    
    """
    # Explicitly check for Linux kernel name first
    if platform.system() != 'Linux':
        return False
    return "android" in platform.platform().lower()

def is_windows() -> bool:
    """Detect if running on Windows."""
    return platform.system() == 'Windows'

def is_apple() -> bool:
    """Detect if running on Apple."""
    return platform.system() == 'Darwin'

def is_ish_alpine() -> bool:
    """Detect if running in iSH Alpine environment on iOS."""
    # platform.system() usually returns 'Linux' in iSH

    # iSH runs on iOS but reports 'Linux' via platform.system()
    if platform.system() != 'Linux':
        return False
    
    # On iSH, /etc/apk/ will exist. However, this is not unique to iSH as standard Alpine Linux also has this directory.
    # Therefore, we need an additional check to differentiate iSH from standard Alpine.
    # HIGHLY SPECIFIC iSH CHECK: Look for the unique /proc/ish/ directory.
    # This directory is created by the iSH pseudo-kernel and does not exist 
    # on standard Alpine or other Linux distributions.
    if os.path.isdir('/etc/apk/') and os.path.isdir('/proc/ish'):
        # This combination is highly specific to iSH Alpine.
        return True
    
    return False
    
def pyinstaller():
    """Detects if the Python script is running as a 'frozen' in the course of generating a PyInstaller binary executable."""
    # If the app is frozen AND has the PyInstaller-specific temporary folder path
    return is_frozen() and hasattr(sys, '_MEIPASS')

# The standard way to check for a frozen state:
def is_frozen():
    """
    Detects if the Python script is running as a 'frozen' (standalone) 
    executable created by a tool like PyInstaller, cx_Freeze, or Nuitka.

    This check is crucial for handling file paths, finding resources, 
    and general environment assumptions, as a frozen executable's 
    structure differs significantly from a standard script execution 
    or a virtual environment.

    The check is based on examining the 'frozen' attribute of the sys module.

    Returns:
        bool: True if the application is running as a frozen executable; 
              False otherwise.
    """
    return getattr(sys, 'frozen', False)

def operatingsystem():
    """Returns the name of the operating system."""
    return platform.system() #determine OS

def open_text_file_in_default_app(filepath):
    """Opens a file with its default application based on the OS."""
    if is_windows():
        os.startfile(filepath)
    elif is_termux():
        subprocess.run(['nano', filepath])
    elif is_ish_alpine():
        subprocess.run(['apk','add', 'nano'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['nano', filepath])
    elif is_linux():
        subprocess.run(['xdg-open', filepath])
    elif is_apple():
        subprocess.run(['open', filepath])
    else:
        print("Unsupported operating system.")

def is_interactive_terminal():
    """
    Check if the script is running in an interactive terminal. 
    Assumpton: 
        If is_interactive_terminal() returns True, 
        then typer.prompt() will work reliably.
    """
    # Check if a tty is attached to stdin
    return sys.stdin.isatty() and sys.stdout.isatty()

def tkinter_is_available() -> bool:
    """Check if tkinter is available and can successfully connect to a display."""
    global _TKINTER_AVAILABILITY
    
    # 1. Return cached result if already calculated
    if _TKINTER_AVAILABILITY is not None:
        return _TKINTER_AVAILABILITY

    # 2. Perform the full, definitive check
    try:
        import tkinter as tk
        
        # Perform the actual GUI backend test for absolute certainty.
        # This only runs once per script execution.
        root = tk.Tk()
        root.withdraw()
        root.update()
        root.destroy()
        
        _TKINTER_AVAILABILITY = True
        return True
    except Exception:
        # Fails if: tkinter module is missing OR the display backend is unavailable
        _TKINTER_AVAILABILITY = False
        return False
    
# --- Browser Check Helper ---
def web_browser_is_available() -> bool:
    """ Check if a web browser can be launched in the current environment."""
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
        # Normalize paths for comparison
        norm_exec_path = normalize_path(exec_path)
        norm_interp_path = normalize_path(interpreter_path)

        if debug:
            # --- DEBUGGING OUTPUT ---
            print(f"DEBUG: EXEC_PATH:      {exec_path}")
            print(f"DEBUG: INTERP_PATH:    {interpreter_path}")
            print(f"DEBUG: PIPX_BIN_PATH:  {pipx_bin_path}")
            print(f"DEBUG: PIPX_VENV_BASE: {pipx_venv_base_path}")
            print(f"DEBUG: Check B result: {normalize_path(interpreter_path).startswith(normalize_path(pipx_venv_base_path))}")
        # ------------------------
        
        # 1. Signature Check (Most Robust): Look for the unique 'pipx/venvs' string.
        # This is a strong check for both the executable path (your discovery) 
        # and the interpreter path (canonical venv location).
        if "pipx/venvs" in norm_exec_path or "pipx/venvs" in norm_interp_path:
            if debug: print("is_pipx: True (Signature Check)")
            return True

        # 2. Targeted Venv Check: The interpreter's path starts with the PIPX venv base.
        # This is a canonical check if the signature check is somehow missed.
        if norm_interp_path.startswith(normalize_path(pipx_venv_base_path)):
            if debug: print("is_pipx: True (Interpreter Base Check)")
            return True
        
        # 3. Targeted Executable Check: The executable's resolved path starts with the PIPX venv base.
        # This is your key Termux discovery, confirming the shim resolves into the venv.
        if norm_exec_path.startswith(normalize_path(pipx_venv_base_path)):
             if debug: print("is_pipx: True (Executable Base Check)")
             return True

        if debug: print("is_pipx: False")
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
