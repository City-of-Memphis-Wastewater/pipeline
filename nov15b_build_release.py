#!/usr/bin/env python3
"""
build_release.py — Unified, clean, and reliable build script for pipeline-eds

Features:
- Builds wheel (Poetry or python -m build)
- Creates .pyz (zipapp), .pex, and .pyz (shiv) — all from a single clean source
- Zero .pyc files (guaranteed)
- Auto-generates Windows .bat and macOS .app wrappers
- Stamps version, git hash, and build time
- Supports extras: --windows, --mpl, --zoneinfo
- Works on Termux, Linux, macOS, Windows

Usage:
    python build_release.py
    python build_release.py --shiv
    python build_release.py --windows
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

# Optional: better OS detection
try:
    import distro
except ImportError:
    distro = None

# ----------------------------------------------------------------------
# GLOBAL: Prevent .pyc files from ever being written
# ----------------------------------------------------------------------
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
ENTRY_POINT = "pipeline.cli:app"
DIST_DIR = Path("dist")

# ----------------------------------------------------------------------
# System Info
# ----------------------------------------------------------------------
class SystemInfo:
    def __init__(self):
        self.system = platform.system()
        self.arch = platform.machine().lower()

    def is_termux(self):
        return "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ

    def is_alpine(self):
        return Path("/etc/alpine-release").exists()

    def get_os_tag(self):
        if self.system == "Windows":
            ver = platform.win32_ver()[1]
            build = int(ver.split(".")[-1]) if "." in ver else 0
            return "windows11" if build >= 22000 else "windows10"
        if self.system == "Darwin":
            return f"macos{platform.mac_ver()[0].split('.')[0]}"
        if self.system == "Linux":
            if self.is_termux():
                return "android"
            info = self._linux_distro()
            ver = (info.get("version") or "").replace(".", "")
            return f"{info['id']}{ver}" if ver else info['id']
        return self.system.lower()

    def get_arch(self):
        return "x86_64" if self.arch in ("amd64", "x86_64") else self.arch

    def _linux_distro(self):
        if distro:
            return {"id": distro.id(), "version": distro.version()}
        info = {}
        path = Path("/etc/os-release")
        if path.exists():
            for line in path.read_text().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    info[k.strip()] = v.strip().strip('"')
        return {"id": info.get("ID", "linux"), "version": info.get("VERSION_ID", "")}

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def run_command(cmd, cwd=None, check=True):
    print(f"Running: {' '.join(map(str, cmd))}")
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result

def clean_dir(path: Path):
    if path.exists():
        print(f"Cleaning {path}...")
        shutil.rmtree(path, ignore_errors=True)

def remove_pyc(root: Path):
    if not root.exists():
        return
    for f in root.rglob("*.pyc"):
        f.unlink()
        print(f"  Removed {f}")
    for d in root.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)
        print(f"  Removed {d}")

# ----------------------------------------------------------------------
# Wheel & Metadata
# ----------------------------------------------------------------------
def build_wheel(dist_dir: Path) -> Path:
    dist_dir.mkdir(exist_ok=True)
    clean_dir(dist_dir)

    if shutil.which("poetry"):
        print("Building wheel with Poetry...")
        run_command(["poetry", "build", "-f", "wheel"])
    else:
        print("Building wheel with python -m build...")
        run_command([sys.executable, "-m", "build", "--wheel"])

    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError("No wheel built")
    latest = max(wheels, key=lambda p: p.stat().st_mtime)
    print(f"Built: {latest.name}")
    return latest
    
def find_latest_wheel(dist_dir: Path):
    wheels = list(dist_dir.glob("*.whl"))
    return max(wheels, key=os.path.getmtime) if wheels else None
        
def extract_metadata(wheel: Path):
    with zipfile.ZipFile(wheel) as z:
        meta = [f for f in z.namelist() if f.endswith(".dist-info/METADATA")]
        if not meta:
            raise ValueError("No METADATA in wheel")
        content = z.read(meta[0]).decode()
        name = re.search(r"^Name: (.+)", content, re.M).group(1).strip()
        ver = re.search(r"^Version: (.+)", content, re.M).group(1).strip()
        return name, ver

def get_py_tag():
    return f"py{sys.version_info.major}{sys.version_info.minor}"

# ----------------------------------------------------------------------
# Extract & Clean Once
# ----------------------------------------------------------------------
def extract_and_clean(wheel: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="pipeline_build_"))
    print(f"Extracting wheel to {tmp}...")
    with zipfile.ZipFile(wheel) as z:
        z.extractall(tmp)
    print("Removing any stray .pyc files...")
    remove_pyc(tmp)
    return tmp

# ----------------------------------------------------------------------
# Builders
# ----------------------------------------------------------------------
def build_zipapp(src_dir: Path, out_path: Path, entry: str):
    print(f"Building zipapp → {out_path.name}")
    pkg, fn = entry.rsplit(":", 1)
    main_py = f'''\
#!/usr/bin/env python3
from {pkg} import {fn}
if __name__ == "__main__":
    import sys
    sys.exit({fn}())
'''
    (src_dir / "__main__.py").write_text(main_py)

    cmd = [
        sys.executable, "-m", "zipapp",
        str(src_dir), "-p", "/usr/bin/env python3",
        "-o", str(out_path), "-c"
    ]
    run_command(cmd)
    out_path.chmod(0o755)
    print("zipapp ready")

def build_shiv(src_dir: Path, out_path: Path, entry: str):
    print(f"Building shiv → {out_path.name}")
    cmd = [
        "shiv", str(src_dir),
        "-e", entry,
        "-o", str(out_path),
        "-p", "/usr/bin/env python3",
        "--no-cache"
    ]
    run_command(cmd)
    out_path.chmod(0o755)

def build_pex(src_dir: Path, out_path: Path, entry: str):
    print(f"Building pex → {out_path.name}")
    cmd = [
        sys.executable, "-m", "pex",
        str(src_dir),
        "--output-file", str(out_path),
        "--entry-point", entry,
        "--python-shebang=/usr/bin/env python3"
    ]
    run_command(cmd)
    out_path.chmod(0o755)

# ----------------------------------------------------------------------
# Launchers
# ----------------------------------------------------------------------
def make_windows_bat(pyz_path: Path, bat_path: Path):
    bat_path.write_text(f'''@echo off
REM Auto-generated launcher for {pyz_path.name}
python "%~dp0{pyz_path.name}" %*
''')
    print(f"Generated: {bat_path.name}")

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

    finally:
        shutil.rmtree(clean_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
