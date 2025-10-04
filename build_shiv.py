#!/usr/bin/env python3

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
import toml

try:
    import distro  # external package, best for Linux detection
except ImportError:
    distro = None


class SystemInfo:
    """Detects the current OS, distro, and version information."""

    def __init__(self):
        self.system = platform.system()  # "Windows", "Linux", "Darwin"
        self.release = platform.release()
        self.version = platform.version()
        self.architecture = platform.machine()

    def detect_linux_distro(self) -> dict:
        """Return Linux distribution info (if available)."""
        if self.system != "Linux":
            return {}

        if distro:
            return {
                "id": distro.id(),
                "name": distro.name(),
                "version": distro.version(),
                "like": distro.like(),
            }
        else:
            # fallback to /etc/os-release parsing
            os_release = Path("/etc/os-release")
            if os_release.exists():
                info = {}
                for line in os_release.read_text().splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        info[k.strip()] = v.strip().strip('"')
                return {
                    "id": info.get("ID"),
                    "name": info.get("NAME"),
                    "version": info.get("VERSION_ID"),
                    "like": info.get("ID_LIKE"),
                }
            return {"id": "unknown", "name": "unknown", "version": "unknown"}

    def detect_android_termux(self) -> bool:
        if "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ:
            return True
        if "android" in self.release.lower():
            return True
        return False
    
    def get_windows_tag(self) -> str:
        """Differentiate Windows 10 vs 11 based on build number."""
        release, version, csd, ptype = platform.win32_ver()
        try:
            build_number = int(version.split(".")[-1])
        except Exception:
            build_number = 0

        if build_number >= 22000:
            return "windows11"
        return "windows10"
    
    def get_os_tag(self) -> str:
        """Return a compact string for use in filenames (e.g. ubuntu22.04)."""
        if self.system == "Windows":
            return self.get_windows_tag()

        if self.system == "Darwin":
            mac_ver = platform.mac_ver()[0].split(".")[0] or "macos"
            return f"macos{mac_ver}"

        if self.system == "Linux":
            if self.detect_android_termux():
                return "android"

            info = self.detect_linux_distro()
            distro_id = info.get("id") or "linux"
            distro_ver = (info.get("version") or "").replace(".", "")
            if distro_ver:
                return f"{distro_id}{info['version']}"
            return distro_id

        return self.system.lower()
    
    def get_arch(self) -> str:
        arch = self.architecture.lower()
        if arch in ("amd64", "x86_64"):
            return "x86_64"
        return self.architecture
    
    def to_dict(self) -> dict:
        """Return a full snapshot of system information."""
        info = {
            "system": self.system,
            "release": self.release,
            "version": self.version,
            "arch": self.architecture,
            "os_tag": self.get_os_tag(),
        }
        if self.system == "Linux" and self.detect_android_termux():
            info["id"] = "android"
            info["name"] = "Android (Termux)"
        elif self.system == "Linux":
            info.update(self.detect_linux_distro())
        elif self.system == "Windows":
            info["win_version"] = platform.win32_ver()
        elif self.system == "Darwin":
            info["mac_ver"] = platform.mac_ver()[0]
        return info

    def pretty_print(self):
        """Nicely formatted printout of system info."""
        info = self.to_dict()
        print("--- System Information ---")
        for k, v in info.items():
            print(f"{k:10}: {v}")
            
# --- Version Retrieval ---
def get_package_version() -> str:
    """Reads project version from pyproject.toml."""
    try:
        data = toml.load('pyproject.toml')
        version = data['tool']['poetry']['version']
    except Exception as e:
        print(f"Error reading version from pyproject.toml: {e}", file=sys.stderr)
        # Fallback version if TOML fails
        version = '0.0.0'
        
    #print(f"Detected project version: {version}")
    return version

def get_package_name() -> str:
    # 1. Read package name from pyproject.toml
    try:
        data = toml.load('pyproject.toml')
        pkg_name = data['tool']['poetry']['name']
    except:
        pkg_name = 'pipeline-eds' # Fallback
    return pkg_name

def get_python_version():
    py_major = sys.version_info.major
    py_minor = sys.version_info.minor
    py_version = f"py{py_major}{py_minor}"
    return py_version

def form_dynamic_binary_name(package_name: str, package_version: str, py_version: str, os_tag: str, arch: str) -> str:    
    # Use hyphens for the CLI/EXE/ELF name
    return f"{package_name}-{package_version}-{py_version}-{os_tag}-{arch}"

# --- Include copies of naming stuff ---

def determine_zipapp_name(extras_str):
    package_name = get_package_name()
    package_version = get_package_version() 
    py_version = get_python_version()
    
    sysinfo = SystemInfo()
    os_tag = sysinfo.get_os_tag()
    architecture = sysinfo.get_arch()

    # Determine the executable name (without the extension)
    executible_descriptor = form_dynamic_binary_name(package_name, package_version, py_version, os_tag, architecture)
    
    # Append the extension
    zipapp_filename = f"{executible_descriptor}{extras_str}.pyz"
    return zipapp_filename

def run_command(command, check=False, cwd=None):
    """A helper to run a command and capture its output and exit code."""
    print(f"Executing: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found.", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}\n{e}", file=sys.stderr)
        return None

def find_latest_wheel(dist_dir: Path):
    """Finds the most recently modified .whl file in the dist directory."""
    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        return None
    return max(wheels, key=os.path.getmtime)

def build_wheel(dist_dir: Path):
    """Attempts to build a wheel using Poetry, falling back to python -m build."""
    # Try using poetry first
    if shutil.which("poetry"):
        print("No wheel found. Trying Poetry...")
        if run_command(["poetry", "build", "-f", "wheel"], check=True):
            return find_latest_wheel(dist_dir)
    else:
        print("Poetry not found, skipping.", file=sys.stderr)

    # Fallback to python -m build
    print("Trying 'python3 -m build --wheel'...")
    if run_command([sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)], check=True):
        return find_latest_wheel(dist_dir)

    return None

def extract_metadata_from_wheel(wheel_path: Path):
    """Extracts package name and version from a wheel's METADATA file."""
    with zipfile.ZipFile(wheel_path, 'r') as zf:
        metadata_files = [f for f in zf.namelist() if f.endswith('.dist-info/METADATA')]
        if not metadata_files:
            raise ValueError(f"Could not find METADATA file in {wheel_path}")

        with zf.open(metadata_files[0]) as meta_file:
            content = meta_file.read().decode('utf-8')
            name_match = re.search(r"^Name: (.+)", content, re.MULTILINE)
            version_match = re.search(r"^Version: (.+)", content, re.MULTILINE)

            if not name_match or not version_match:
                raise ValueError("Could not parse Name and Version from METADATA.")

            return name_match.group(1).strip(), version_match.group(1).strip()

def generate_windows_launcher(pyz_path: Path, bat_path: Path):
    """Generates a .bat file to launch the .pyz on Windows."""
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

def main():
    """Main script execution."""
    parser = argparse.ArgumentParser(description="Build a Shiv executable (.pyz) from a Python project.")
    parser.add_argument("--windows", action="store_true", help="Include 'windows' extra in the filename.")
    parser.add_argument("--mpl", action="store_true", help="Include 'mpl' extra in the filename.")
    parser.add_argument("--zoneinfo", action="store_true", help="Include 'zoneinfo' extra in the filename.")
    # You can add more arguments for entry point, etc. if needed.
    # parser.add_argument("-e", "--entry-point", default="pipeline.cli:app", help="The entry point for the shiv app.")
    args = parser.parse_args()

    # --- Setup directories and Python version ---
    py_major, py_minor = sys.version_info[0], sys.version_info[1]
    py_version_str = f"py{py_major}{py_minor}"
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    # --- Detect extras ---
    extras = []
    if args.windows: extras.append("windows")
    if args.mpl: extras.append("mpl")
    if args.zoneinfo: extras.append("zoneinfo")
    extras_str = f"-{'-'.join(extras)}" if extras else ""

    # --- Find or build the wheel ---
    latest_wheel = find_latest_wheel(dist_dir)
    if not latest_wheel:
        latest_wheel = build_wheel(dist_dir)

    if not latest_wheel:
        print("Error: Could not find or create a wheel. Aborting.", file=sys.stderr)
        sys.exit(1)

    print(f"Using wheel: {latest_wheel}")

    # --- Extract metadata from the wheel ---
    try:
        pkg_name, pkg_version = extract_metadata_from_wheel(latest_wheel)
        print(f"PKG_NAME: {pkg_name}")
        print(f"PKG_VERSION: {pkg_version}")
    except (ValueError, FileNotFoundError) as e:
        print(f"Error extracting metadata: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Compose final filenames ---
    pyz_filename = determine_zipapp_name(extras_str)
    pyz_path = dist_dir / pyz_filename
    bat_path = pyz_path.with_suffix(".bat")

    print(f"Output .pyz will be: {pyz_path}")
    print(f"Output launcher .bat will be: {bat_path}")

    # --- Build the .pyz with Shiv ---
    shiv_command = [
        "shiv",
        str(latest_wheel),
        "-e", "pipeline.cli:app",  # Hardcoded as in the shell script
        "-o", str(pyz_path),
        "-p", "/usr/bin/env python3"
    ]

    result = run_command(shiv_command)

    if result and result.returncode == 0:
        print(f"Successfully created {pyz_path}")
        # --- Generate Windows launcher ---
        if platform.system() == "Windows" or args.windows:
             generate_windows_launcher(pyz_path, bat_path)
    else:
        print(f"Shiv failed with exit code {result.returncode if result else 1}", file=sys.stderr)
        sys.exit(result.returncode if result else 1)

if __name__ == "__main__":
    main()