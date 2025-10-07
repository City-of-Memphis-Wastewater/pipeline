# pipeline/source_check.oy

import os
import sys
from pathlib import Path
from pipeline.helpers import check_if_zip

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

def is_pipx() -> bool:
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

        # --- A. Check the Symlink Location (Original, still valuable check) ---
        # The symlink that was executed to launch the script (sys.argv[0]) 
        # is in the pipx binary directory.
        if exec_path != interpreter_path and normalize_path(exec_path).startswith(normalize_path(pipx_bin_path)):
            return True

        # --- B. Check the Venv Location (The definitive, non-ambiguous check) ---
        # The actual interpreter running the code is located inside the 
        # *internal* pipx venv structure. This is the ultimate "pipx signature."
        if normalize_path(interpreter_path).startswith(normalize_path(pipx_venv_base_path)):
            return True
        
        # --- C. Check for pip install --user case (The Ambiguity Filter) ---
        # If running from a venv, but not a pipx one, this should be False.
        # If running from ~/.local/bin via `pip install --user`, this also returns False, 
        # as that interpreter is not nested in `.../pipx/venvs`.

        return False

    except Exception:
        # Fallback for unexpected path errors
        return False
    

def is_elf() -> bool:
    """Checks if the currently running executable (sys.argv[0]) is a standalone PyInstaller-built ELF binary."""
    # If it's a pipx installation, it is not the monolithic binary we are concerned with here.
    if is_pipx():
        return False
        
    exec_path = Path(sys.argv[0]).resolve()
    
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
    
def is_pyz(exec_path: Path=None) -> bool:
    """Checks if the currently running executable (sys.argv[0]) is a PYZ zipapp ."""
    # If it's a pipx installation, it is not the monolithic binary we are concerned with here.
    if is_pipx():
        return False
    if exec_path is None:
        exec_path = Path(sys.argv[0]).resolve()
    print(f"exec_path = {exec_path}")
    # Check if the extension is PYZ
    if not str(exec_path).endswith() == ".pyz":
        return False
    
    if not check_if_zip():
        return False