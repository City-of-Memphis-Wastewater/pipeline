#!/usr/bin/env python3
"""
Unified, clean, no-pyc build script for pipeline-eds.

Features:
- Wheel built with Poetry (or fallback to `python -m build`)
- Single extraction + .pyc cleanup (shared by zipapp, shiv, pex)
- Zero .pyc files (PYTHONDONTWRITEBYTECODE=1 + explicit cleanup)
- Portable .pyz (zipapp), .pex, optional shiv
- Windows .bat & macOS .app wrappers
- Metadata stamping (_version.py)
- Extras support (windows, mpl, zoneinfo)
- --skip-build-wheel for fast iteration
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
    import distro  # optional
except ImportError:
    distro = None


# ----------------------------------------------------------------------
# 1. GLOBAL SETTINGS — NEVER write .pyc
# ----------------------------------------------------------------------
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
PROJECT_NAME = "pipeline-eds"
ENTRY_POINT = "pipeline.cli:app"
DIST_DIR = "dist"
PYTHON_BIN = sys.executable


# ----------------------------------------------------------------------
# System / OS Detection
# ----------------------------------------------------------------------
class SystemInfo:
    def __init__(self):
        self.system = platform.system()
        self.architecture = platform.machine()

    def detect_android_termux(self):
        return "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ

    def get_windows_tag(self):
        _, version, _, _ = platform.win32_ver()
        try:
            build = int(version.split(".")[-1])
        except Exception:
            build = 0
        return "windows11" if build >= 22000 else "windows10"

    def get_os_tag(self):
        if self.system == "Windows":
            return self.get_windows_tag()
        if self.system == "Darwin":
            mac_ver = platform.mac_ver()[0].split(".")[0] or "macos"
            return f"macos{mac_ver}"
        if self.system == "Linux":
            if self.detect_android_termux():
                return "android"
            info = self._linux_distro()
            ver = (info.get("version") or "").replace(".", "")
            return f"{info['id']}{ver}" if ver else info['id']
        return self.system.lower()

    def get_arch(self):
        arch = self.architecture.lower()
        return "x86_64" if arch in ("amd64", "x86_64") else arch

    def _linux_distro(self):
        if distro:
            return {"id": distro.id(), "version": distro.version()}
        info = {}
        p = Path("/etc/os-release")
        if p.exists():
            for line in p.read_text().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    info[k.strip()] = v.strip().strip('"')
        return {"id": info.get("ID", "linux"), "version": info.get("VERSION_ID", "")}


# ----------------------------------------------------------------------
# Poetry Check
# ----------------------------------------------------------------------
def did_poetry_make_the_call() -> bool:
    if os.environ.get("POETRY_ACTIVE") == "1":
        return True
    return ".venv" in sys.executable.lower() or "poetry" in sys.executable.lower()


# ----------------------------------------------------------------------
# Version / Metadata
# ----------------------------------------------------------------------
def get_package_version() -> str:
    try:
        return toml.load("pyproject.toml")["tool"]["poetry"]["version"]
    except Exception:
        return "0.0.0"


def get_package_name() -> str:
    try:
        return toml.load("pyproject.toml")["tool"]["poetry"]["name"]
    except Exception:
        return "pipeline-eds"


def get_python_version() -> str:
    return f"py{sys.version_info.major}{sys.version_info.minor}"


def form_dynamic_binary_name(pkg, ver, py, os_tag, arch, extras="") -> str:
    extra = f"-{extras}" if extras else ""
    return f"{pkg}-{ver}-{py}-{os_tag}-{arch}{extra}"


# ----------------------------------------------------------------------
# Command Runner
# ----------------------------------------------------------------------
def run_command(cmd, cwd=None, check=True):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result


# ----------------------------------------------------------------------
# Wheel Handling
# ----------------------------------------------------------------------
def clean_dist(dist_dir: Path):
    if dist_dir.exists():
        print(f"Cleaning {dist_dir}...")
        for item in dist_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()


def build_wheel(dist_dir: Path, use_poetry: bool = True) -> Path:
    dist_dir.mkdir(exist_ok=True)
    clean_dist(dist_dir)

    if use_poetry and shutil.which("poetry"):
        print("Building wheel with Poetry (no .pyc)…")
        run_command(["poetry", "build", "-f", "wheel"])
    else:
        print("Building wheel with python -m build (no .pyc)…")
        run_command([sys.executable, "-m", "build", "--wheel"])

    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError("No wheel built")
    latest = max(wheels, key=lambda f: f.stat().st_mtime)
    print(f"Built wheel: {latest.name}")
    return latest


def find_latest_wheel(dist_dir: Path):
    wheels = list(dist_dir.glob("*.whl"))
    return max(wheels, key=os.path.getmtime) if wheels else None


def extract_metadata_from_wheel(wheel: Path):
    with zipfile.ZipFile(wheel) as z:
        meta = [f for f in z.namelist() if f.endswith(".dist-info/METADATA")]
        if not meta:
            raise ValueError("No METADATA")
        content = z.read(meta[0]).decode()
        name = re.search(r"^Name: (.+)", content, re.M).group(1)
        ver = re.search(r"^Version: (.+)", content, re.M).group(1)
        return name.strip(), ver.strip()


# ----------------------------------------------------------------------
# .pyc Cleanup & Extraction
# ----------------------------------------------------------------------
def remove_pyc(root: Path):
    if not root.exists():
        return
    for f in root.rglob("*.pyc"):
        f.unlink()
        print(f"Removed {f}")
    for d in root.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)
        print(f"Removed {d}")


def extract_and_clean(wheel: Path) -> Path:
    extract_dir = Path(tempfile.mkdtemp(prefix="pipeline_"))
    with zipfile.ZipFile(wheel) as z:
        z.extractall(extract_dir)
    print("\nCleaning stray .pyc from extracted wheel…")
    remove_pyc(extract_dir)
    return extract_dir


# ----------------------------------------------------------------------
# Builders (all use clean_dir)
# ----------------------------------------------------------------------
def build_zipapp(clean_dir: Path, out_path: Path, entry: str):
    print(f"\nBuilding zipapp → {out_path.name}")
    pkg, fn = entry.rsplit(":", 1)
    main_py = f'''\
#!/usr/bin/env python3
from {pkg} import {fn}
if __name__ == "__main__":
    import sys
    sys.exit({fn}())
'''
    (clean_dir / "__main__.py").write_text(main_py)

    cmd = [
        sys.executable, "-m", "zipapp",
        str(clean_dir),
        "-p", "/usr/bin/env python3",
        "-o", str(out_path),
        "-c"
    ]
    run_command(cmd)
    out_path.chmod(0o755)
    print("zipapp built – pure .py, no .pyc")


def build_shiv(clean_dir: Path, out_path: Path, entry: str):
    cmd = [
        "shiv",
        str(clean_dir),
        "-e", entry,
        "-o", str(out_path),
        "-p", "/usr/bin/env python3",
        "--no-cache"
    ]
    run_command(cmd)
    out_path.chmod(0o755)


def build_pex(clean_dir: Path, out_path: Path, entry: str):
    cmd = [
        sys.executable, "-m", "pex",
        str(clean_dir),
        "--output-file", str(out_path),
        "--entry-point", entry,
        "--python-shebang=/usr/bin/env python3"
    ]
    run_command(cmd)
    out_path.chmod(0o755)


# ----------------------------------------------------------------------
# Launchers
# ----------------------------------------------------------------------
def generate_windows_launcher(pyz: Path, bat: Path):
    bat.write_text(f"""@echo off
REM Windows launcher for {pyz.name}
"%~dp0{pyz.name}" %*
""")
    print(f"Generated {bat.name}")


def generate_macos_app(pyz: Path, app_dir: Path):
    app_dir.mkdir(parents=True, exist_ok=True)
    contents = app_dir / "Contents" / "MacOS"
    contents.mkdir(parents=True, exist_ok=True)
    exec_path = contents / pyz.name
    shutil.copy2(pyz, exec_path)
    exec_path.chmod(0o755)
    print(f"Generated macOS app: {app_dir.name}")


# ----------------------------------------------------------------------
# Metadata
# ----------------------------------------------------------------------
def write_version_file(dist_dir: Path):
    file = dist_dir / "_version.py"
    ver = get_package_version()
    git = subprocess.getoutput("git rev-parse --short HEAD")
    ts = datetime.datetime.now().isoformat()
    file.write_text(f'''# Auto-generated
__version__ = "{ver}"
__git__ = "{git}"
__build_time__ = "{ts}"
''')
    print(f"Stamped version: {file}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Build pipeline-eds artifacts")
    parser.add_argument("--windows", action="store_true")
    parser.add_argument("--shiv", action="store_true")
    parser.add_argument("--mpl", action="store_true")
    parser.add_argument("--zoneinfo", action="store_true")
    parser.add_argument("--entry-point", default=ENTRY_POINT)
    parser.add_argument("--skip-build-wheel", action="store_true")
    args = parser.parse_args()

    extras = []
    if args.windows: extras.append("windows")
    if args.mpl: extras.append("mpl")
    if args.zoneinfo: extras.append("zoneinfo")
    extras_str = "-".join(extras) if extras else ""

    dist_dir = Path(DIST_DIR)
    dist_dir.mkdir(exist_ok=True)

    # --- Wheel ---
    wheel = find_latest_wheel(dist_dir)
    if args.skip_build_wheel and wheel:
        print(f"Using existing wheel: {wheel.name}")
    else:
        wheel = build_wheel(dist_dir, use_poetry=did_poetry_make_the_call())

    # --- Extract once, clean once ---
    clean_dir = extract_and_clean(wheel)

    try:
        name, ver = extract_metadata_from_wheel(wheel)
        py_ver = get_python_version()
        os_tag = SystemInfo().get_os_tag()
        arch = SystemInfo().get_arch()
        bin_name = form_dynamic_binary_name(name, ver, py_ver, os_tag, arch, extras_str)

        # --- Build artifacts ---
        zipapp_path = dist_dir / f"{bin_name}.pyz"
        build_zipapp(clean_dir, zipapp_path, args.entry_point)

        if args.shiv:
            shiv_path = dist_dir / f"{bin_name}_shiv.pyz"
            build_shiv(clean_dir, shiv_path, args.entry_point)

        if not ph.on_termux():
            pex_path = dist_dir / f"{bin_name}.pex"
            build_pex(clean_dir, pex_path, args.entry_point)

        # --- Launchers ---
        if not ph.on_termux() and not ph.on_ish_alpine():
            generate_windows_launcher(zipapp_path, zipapp_path.with_suffix(".bat"))
            generate_macos_app(zipapp_path, zipapp_path.with_suffix(".app"))

        write_version_file(dist_dir)

        print("\n" + "="*70)
        print("BUILD COMPLETE – ONE‑LINE COPY‑PASTE")
        print("="*70)
        print(f"Wheel : {wheel.name}")
        print(f"Zipapp: {zipapp_path.name}")
        if args.shiv:
            print(f"Shiv  : {shiv_path.name}")
        if not ph.on_termux():
            print(f"PEX   : {pex_path.name}")
        print("-"*70)
        print("Run the app:")
        try:
            rel_zipapp = zipapp_path.relative_to(dist_dir.parent)
            print(f"    ./{rel_zipapp}  # or")
            print(f"    python {rel_zipapp}")
        except ValueError:
            # Fallback: absolute path (rare)
            print(f"    {zipapp_path}")
        print("="*70 + "\n")
                                                                                    
    finally:
        shutil.rmtree(clean_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
