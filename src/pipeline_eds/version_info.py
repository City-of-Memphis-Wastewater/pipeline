# pipeline_eds.version_info.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import sys
import toml
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path  

from pipeline_eds.system_info import SystemInfo

# -- Versioning --
PIP_PACKAGE_NAME = "pipeline-eds"

def get_version_from_known_alias():
    try:
        PIPELINE_VERSION = version(PIP_PACKAGE_NAME)
    except PackageNotFoundError:
        PIPELINE_VERSION = "0.0.0"
    return PIPELINE_VERSION

PIPELINE_VERSION = get_version_from_known_alias()
try:
    __version__ = version(PIP_PACKAGE_NAME)

except PackageNotFoundError:
    # fallback if running from source
    try:
            with open(Path(__file__).parent / "VERSION") as f:
                __version__ = f.read().strip()
    except FileNotFoundError:
        __version__ = "dev" 

# --- Version Retrieval ---
def get_package_version() -> str:
    """Reads project version from pyproject.toml."""
    try:
        data = toml.load('pyproject.toml')
        version = data['tool']['poetry']['version']
    except Exception as e:
        # print(f"Error reading version from pyproject.toml: {e}", file=sys.stderr)
        # Fallback version if TOML fails
        version = get_version_from_known_alias()
        
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

if __name__ == "__main__":
    package_name = get_package_name()
    package_version = get_package_version()
    py_version = get_python_version()
    
    sysinfo = SystemInfo()
    os_tag = sysinfo.get_os_tag()
    architecture = sysinfo.get_arch()

    bin_name = form_dynamic_binary_name(package_name, package_version, py_version, os_tag, architecture)
    print(f"bin_name = {bin_name}")