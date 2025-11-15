#!/usr/bin/env python3
"""
Unified build script for pipeline-eds project.

Capabilities:
- Builds wheel via Poetry if not present
- Creates portable .pyz (Shiv) and .pex (PEX) archives including dependencies
- Generates Windows .bat and macOS .app launchers
- Stamps metadata (_version.py) with version, timestamp, and Git commit
- Supports extras flags (e.g., windows, mpl, zoneinfo)
- Supports --skip-build-wheel flag for faster iteration
"""

import argparse
import datetime
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
import re
import toml
import pyhabitat as ph

try:
    import distro  # optional, for Linux detection
except ImportError:
    distro = None

# --- Configuration ---
PROJECT_NAME = "pipeline-eds"
ENTRY_POINT = "pipeline.cli:app"
DIST_DIR = "dist"
PYTHON_BIN = sys.executable # Use the current Python interpreter path

# -----------------------------
# System / OS Detection
# -----------------------------
class SystemInfo:
    """Detect system, architecture, OS tag for filenames and wrappers."""

    def __init__(self):
        self.system = platform.system()
        self.release = platform.release()
        self.version = platform.version()
        self.architecture = platform.machine()

    def detect_linux_distro(self):
        if self.system != "Linux":
            return {}
        if distro:
            return {
                "id": distro.id(),
                "name": distro.name(),
                "version": distro.version(),
                "like": distro.like(),
            }
        # fallback to /etc/os-release
        info = {}
        path = Path("/etc/os-release")
        if path.exists():
            for line in path.read_text().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    info[k.strip()] = v.strip().strip('"')
        return {
            "id": info.get("ID", "linux"),
            "name": info.get("NAME", "Linux"),
            "version": info.get("VERSION_ID", ""),
            "like": info.get("ID_LIKE", ""),
        }

    def detect_android_termux(self):
        return "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ

    def get_windows_tag(self):
        release, version, _, _ = platform.win32_ver()
        try:
            build_number = int(version.split(".")[-1])
        except Exception:
            build_number = 0
        return "windows11" if build_number >= 22000 else "windows10"

    def get_os_tag(self):
        """Compact string for filename/archiving."""
        if self.system == "Windows":
            return self.get_windows_tag()
        if self.system == "Darwin":
            mac_ver = platform.mac_ver()[0].split(".")[0] or "macos"
            return f"macos{mac_ver}"
        if self.system == "Linux":
            if self.detect_android_termux():
                return "android"
            info = self.detect_linux_distro()
            ver_str = (info.get("version") or "").replace(".", "")
            return f"{info['id']}{ver_str}" if ver_str else info['id']
        return self.system.lower()

    def get_arch(self):
        arch = self.architecture.lower()
        return "x86_64" if arch in ("amd64", "x86_64") else arch


# -----------------------------
# Poetry Check
# -----------------------------
def did_poetry_make_the_call() -> bool:
    """
    Return True if the script is currently running under `poetry run`.

    This works by checking the `POETRY_ACTIVE` environment variable,
    which Poetry sets automatically when running commands.
    """
    # Environment variable is the most reliable
    if os.environ.get("POETRY_ACTIVE") == "1":
        return True

    # Fallback: check if the executable path includes '.venv' or 'poetry'
    python_path = sys.executable.lower()
    if ".venv" in python_path or "poetry" in python_path:
        return True

    return False

# -----------------------------
# Version / Metadata
# -----------------------------
def get_package_version() -> str:
    """Read version from pyproject.toml."""
    try:
        data = toml.load('pyproject.toml')
        return data['tool']['poetry']['version']
    except Exception:
        return "0.0.0"

def get_package_name() -> str:
    """Read package name from pyproject.toml."""
    try:
        data = toml.load('pyproject.toml')
        return data['tool']['poetry']['name']
    except Exception:
        return "pipeline-eds"

def get_python_version() -> str:
    return f"py{sys.version_info.major}{sys.version_info.minor}"

def form_dynamic_binary_name(pkg_name, pkg_version, py_version, os_tag, arch, extras_str="") -> str:
    extras_part = f"-{extras_str}" if extras_str else ""
    return f"{pkg_name}-{pkg_version}-{py_version}-{os_tag}-{arch}{extras_part}"


# -----------------------------
# Command Execution Helper
# -----------------------------

def run_command(cmd, cwd=None, check=True):
    """Run a command with optional working directory, print stdout/stderr."""
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result

# -----------------------------
# Wheel Handling
# -----------------------------

def clean_dist(dist_dir: Path):
    """Remove all existing artifacts in the dist directory."""
    if dist_dir.exists():
        print(f"Cleaning existing files in {dist_dir}...")
        for item in dist_dir.iterdir():
            if item.is_file() or item.is_dir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

def build_wheel(dist_dir: Path, use_poetry:bool=True) -> Path:
    """
    Always rebuild a wheel from pyproject.toml.
    Returns the path to the new wheel.
    """
    # Ensure the dist directory exists
    dist_dir.mkdir(exist_ok=True)

    # Optional: clean old builds to avoid stale artifacts
    clean_dist(dist_dir)

    # Attempt build with Poetry first if requested
    if use_poetry and shutil.which("poetry"):
        print("Building wheel using Poetry...")
        run_command(["poetry", "build", "-f", "wheel"], cwd=None)
    else:
        # Fallback: python -m build
        print("Building wheel using 'python -m build --wheel'...")
        if not shutil.which("python3"):
            raise RuntimeError("python3 not found for building wheel.")
        #run_command([sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)], cwd=None)
        run_command([sys.executable, "-m", "build", "--wheel"])

    # Find the latest wheel in dist
    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError(f"No wheel found in {dist_dir} after build.")
    # Pick the newest file just in case
    latest_wheel = max(wheels, key=lambda f: f.stat().st_mtime)
    print(f"Built wheel: {latest_wheel}")
    return latest_wheel

def find_latest_wheel(dist_dir: Path):
    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        return None
    return max(wheels, key=os.path.getmtime)


def extract_metadata_from_wheel(wheel_path: Path):
    """Extract package name and version from wheel METADATA."""
    with zipfile.ZipFile(wheel_path, 'r') as zf:
        metadata_files = [f for f in zf.namelist() if f.endswith('.dist-info/METADATA')]
        if not metadata_files:
            raise ValueError(f"No METADATA in {wheel_path}")
        with zf.open(metadata_files[0]) as f:
            content = f.read().decode()
            name = re.search(r"^Name: (.+)", content, re.MULTILINE).group(1)
            version = re.search(r"^Version: (.+)", content, re.MULTILINE).group(1)
            return name.strip(), version.strip()

def get_site_packages_path() -> str | None:
    """Dynamically finds the site-packages directory of the active environment."""
    # Look for the path containing 'site-packages' that is not a zip file
    for path in sys.path:
        p = Path(path)
        if "site-packages" in path and p.exists() and p.is_dir():
            return path
    return None

# -----------------------------
# Shiv / PEX Building
# -----------------------------
#def build_shiv(latest_wheel: Path, pyz_path: Path, entry_point="pipeline.cli:app"):
#    # FIX: Add --site-packages/-S to ensure all dependencies from the active virtual environment are included.
#    cmd = ["shiv", str(latest_wheel), "-e", entry_point, "-o", str(pyz_path), "-p", "/usr/bin/env python3", "-S"]
#    return run_command(cmd)

#def build_pex(latest_wheel: Path, pex_path: Path, entry_point="pipeline.cli:app"):
#    # FIX: Add --site-packages to ensure all dependencies from the active virtual environment are included.
#    cmd = ["python", "-m", "pex", str(latest_wheel), "--output-file", str(pex_path),
#            "--entry-point", entry_point, "--python", "python3", "--python-shebang=/usr/bin/env python3", "--site-packages"]
#    return run_command(cmd)

# --- Build Functions ---

def build_shiv(wheel_path, output_path):
    """Builds the PYZ file using Shiv."""
    print(f"\nBuilding PYZ with Shiv: {output_path}")
    
    # Get the path to the virtual environment's site-packages
    venv_path = os.environ.get("VIRTUAL_ENV")
    if not venv_path:
        # Fallback assumption for standard Python 3.12 structure
        venv_path = os.path.dirname(os.path.dirname(os.path.dirname(PYTHON_BIN)))
    site_packages_path = os.path.join(venv_path, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
    
    print(f"Bundling dependencies from: {site_packages_path}")
    
    # Use poetry export to generate a clean requirements.txt excluding dev dependencies
    reqs_cmd = ["poetry", "export", "-f", "requirements.txt", "--output", "requirements.txt", "--without-hashes"]

    cmd = [
        "shiv",
        str(wheel_path),
        "-e", ENTRY_POINT,
        "-o", str(output_path),
        "-p", "/usr/bin/env python3", # The shebang line for execution
        # Shiv needs to be explicitly told to bundle the venv packages
        #"--site-packages", site_packages_path # the fact that pex is used causes problems.
    ]
    try:
        run_command(cmd)
        print("Shiv build successful.")
        return True
    except subprocess.CalledProcessError:
        print("Shiv build failed.")
        return False

def build_pex(wheel_path, output_path):
    """Builds the PEX file using Pex."""
    print(f"\nBuilding PEX with Pex: {output_path}")

    # PEX Command: We remove the --site-packages argument!
    # PEX automatically bundles all required dependencies from the wheel metadata.
    cmd = [
        PYTHON_BIN, "-m", "pex",
        str(wheel_path),
        "--output-file", str(output_path),
        "--entry-point", ENTRY_POINT,
        # We explicitly use the Python interpreter from the venv for running the pex module
        "--python", "python3", 
        "--python-shebang=/usr/bin/env python3"
        # Removed: "--site-packages" <--- THIS WAS THE ERROR
    ]
    try:
        run_command(cmd)
        print("Pex build successful.")
        return True
    except subprocess.CalledProcessError:
        print("Pex build failed.")
        return False


# -----------------------------
# Launcher Wrappers
# -----------------------------
def generate_windows_launcher(pyz_path: Path, bat_path: Path):
    content = f"""@echo off
REM Windows launcher for {pyz_path.name}
set PY_EXE=python.exe
set PYZ_FILE={pyz_path.name}
PUSHD "%~dp0"
"%PY_EXE%" "%PYZ_FILE%" %*
POPD
pause
"""
    bat_path.write_text(content)
    print(f"Generated Windows launcher: {bat_path}")

def generate_macos_app(pyz_path: Path, app_dir: Path):
    app_dir.mkdir(parents=True, exist_ok=True)
    contents_dir = app_dir / "Contents" / "MacOS"
    contents_dir.mkdir(parents=True, exist_ok=True)
    exec_path = contents_dir / pyz_path.name
    shutil.copy2(pyz_path, exec_path)
    exec_path.chmod(0o755)
    print(f"Generated macOS app stub: {app_dir}")


# -----------------------------
# Metadata stamping
# -----------------------------
def write_version_file(dist_dir: Path):
    version_file = dist_dir / "_version.py"
    version = get_package_version()
    git_hash = subprocess.getoutput("git rev-parse --short HEAD")
    timestamp = datetime.datetime.now().isoformat()
    content = f'''# Auto-generated version file
__version__ = "{version}"
__git__ = "{git_hash}"
__build_time__ = "{timestamp}"
'''
    version_file.write_text(content)
    print(f"Stamped version metadata: {version_file}")


# -----------------------------
# Main build logic
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Unified build script for pipeline-eds")
    parser.add_argument("--windows", action="store_true")
    parser.add_argument("--mpl", action="store_true")
    parser.add_argument("--zoneinfo", action="store_true")
    parser.add_argument("--entry-point", default="pipeline.cli:app")
    parser.add_argument("--skip-build-wheel", action="store_true", 
                        help="Skip the poetry wheel build if a wheel already exists in 'dist/'.")
    args = parser.parse_args()

    extras = []
    if args.windows: extras.append("windows")
    if args.mpl: extras.append("mpl")
    if args.zoneinfo: extras.append("zoneinfo")
    extras_str = "-".join(extras) if extras else ""

    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

   # --- Wheel ---
    latest_wheel = find_latest_wheel(dist_dir)

    if args.skip_build_wheel and latest_wheel:
        print(f"Skipping wheel build. Using existing wheel: {latest_wheel.name}")
    else:
        # If we are building, ensure old artifacts are cleaned first
        clean_dist(dist_dir)
        latest_wheel = build_wheel(dist_dir, use_poetry=did_poetry_make_the_call())
    
    if not latest_wheel:
        if args.skip_build_wheel:
            print("Error: --skip-build-wheel used, but no existing wheel found.", file=sys.stderr)
        else:
            print("Error: Could not build wheel.", file=sys.stderr)
        sys.exit(1)

    pkg_name, pkg_version = extract_metadata_from_wheel(latest_wheel)
    py_version = get_python_version()
    sysinfo = SystemInfo()
    os_tag = sysinfo.get_os_tag()
    arch = sysinfo.get_arch()

    # --- Portable binaries ---
    pyz_path = dist_dir / f"{form_dynamic_binary_name(pkg_name, pkg_version, py_version, os_tag, arch, extras_str)}.pyz"
    pex_path = dist_dir / f"{form_dynamic_binary_name(pkg_name, pkg_version, py_version, os_tag, arch, extras_str)}.pex"

    # --- Build Shiv / PEX ---
    if Fm build_shiv(latest_wheel, pyz_path):
        print(f"Successfully created:\n  {pyz_path}")
    # PEX will not build for Termux due to Android compatibility issue with os.link() 
    if not ph.on_termux() and build_pex(latest_wheel, pex_path): 
        print(f"Successfully created:\n  {pex_path}")

    # --- Generate launchers ---
    if not ph.on_termux() and not ph.on_ish_alpine():
        #if args.windows or platform.system() == "Windows":
        bat_path = pyz_path.with_suffix(".bat")
        generate_windows_launcher(pyz_path, bat_path)
        #if args.windows platform.system() == "Darwin":
        app_dir = pyz_path.with_suffix(".app")
        generate_macos_app(pyz_path, app_dir)

    # --- Metadata stamping ---
    write_version_file(dist_dir)


if __name__ == "__main__":
    main()

"""
### ✅ Features included:

1. Wheel auto-build with Poetry (or fallback to `python -m build`).
2. Portable `.pyz` (Shiv) **with dependencies included**.
3. Portable `.pex` (PEX) **with dependencies included**.
4. Auto-generated **Windows `.bat`** and **macOS `.app`** wrappers.
5. Metadata stamping (`_version.py`) with version, Git hash, and timestamp.
6. Extras support (`--windows`, `--mpl`, `--zoneinfo`) that affects filenames.
7. Fully commented for easy future enhancements (like PyInstaller or GitHub release integration).
"""
