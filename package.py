#!/usr/bin/env python3
"""
build_release.py — The Ultimate, No-.pyc, Cross-Platform Build Script
=====================================================================

Why this script exists:
    • We want ONE command to build a wheel + portable .pyz + shiv + pex
    • We want ZERO .pyc files by default (clean, portable, Termux-safe)
    • We want fast startup on second run → use `shiv` (caches .pyc in ~/.shiv)
    • We want clear, copy-pasteable output so anyone can run your app
    • We want to understand WHY things are done this way

Author:  George Clayton Bennett (with love from AI)
Project: pipeline-eds
Date:    November 16, 2025
"""

# ----------------------------------------------------------------------
# 1. GLOBAL: NEVER write .pyc files (unless you opt-in later)
# ----------------------------------------------------------------------
# Why? .pyc files:
#   • Are Python-version specific
#   • Bloat the .pyz
#   • Are useless in read-only .pyz (zipapp)
#   • Can break on Termux/Android
#   • Are cached by `shiv` at runtime anyway
#   → So we disable them at build time for purity


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
    import distro  # Optional: better Linux detection
except ImportError:
    distro = None

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


# ----------------------------------------------------------------------
# 2. CONFIGURATION
# ----------------------------------------------------------------------
PROJECT_NAME = "pipeline-eds"
ENTRY_POINT = "pipeline.cli:app"   # Your Typer/FastAPI entry point
REPO_NAME = "pipeline"
PROJECT_ROOT = Path(__file__).resolve().parent   # repo root
while PROJECT_ROOT.name != REPO_NAME and PROJECT_ROOT != PROJECT_ROOT.parent:
    PROJECT_ROOT = PROJECT_ROOT.parent
SRC_PKG = PROJECT_ROOT / "src" / "pipeline"
DIST_DIR = PROJECT_ROOT / "dist"
#DIST_DIR = "dist"                  # All artifacts go here
PYTHON_BIN = sys.executable        # Use the current venv interpreter


# ----------------------------------------------------------------------
# 3. SYSTEM DETECTION — Why? For filename tagging
# ----------------------------------------------------------------------
# Example output:
#   pipeline-eds-0.3.68-py312-android-aarch64.pyz
#   → Tells user: OS, arch, Python version
class SystemInfo:
    def __init__(self):
        self.system = platform.system()
        self.architecture = platform.machine()

    def detect_android_termux(self):
        # Termux sets these env vars
        return "ANDROID_ROOT" in os.environ or "TERMUX_VERSION" in os.environ

    def get_windows_tag(self):
        # Windows 10 vs 11 detection via build number
        _, version, _, _ = platform.win32_ver()
        try:
            build = int(version.split(".")[-1])
        except Exception:
            build = 0
        return "windows11" if build >= 22000 else "windows10"

    def get_os_tag(self):
        """Compact OS tag for filenames."""
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
        """Normalize architecture for filenames."""
        arch = self.architecture.lower()
        return "x86_64" if arch in ("amd64", "x86_64") else arch

    def _linux_distro(self):
        """Fallback if `distro` not installed."""
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
# 4. POETRY DETECTION — Why? Use Poetry if available
# ----------------------------------------------------------------------
def did_poetry_make_the_call() -> bool:
    """Are we running under `poetry run`?"""
    if os.environ.get("POETRY_ACTIVE") == "1":
        return True
    return ".venv" in sys.executable.lower() or "poetry" in sys.executable.lower()


# ----------------------------------------------------------------------
# 5. METADATA HELPERS
# ----------------------------------------------------------------------
def get_package_version() -> str:
    """Read version from pyproject.toml — Poetry source of truth."""
    try:
        return toml.load("pyproject.toml")["tool"]["poetry"]["version"]
    except Exception:
        return "0.0.0"


def get_package_name() -> str:
    """Read name from pyproject.toml."""
    try:
        return toml.load("pyproject.toml")["tool"]["poetry"]["name"]
    except Exception:
        return "pipeline-eds"


def get_python_version() -> str:
    """py312, py311, etc."""
    return f"py{sys.version_info.major}{sys.version_info.minor}"


def form_dynamic_binary_name(pkg, ver, py, os_tag, arch, extras="") -> str:
    """Generate final filename: pkg-ver-py-os-arch-extras.pyz"""
    extra = f"-{extras}" if extras else ""
    return f"{pkg}-{ver}-{py}-{os_tag}-{arch}{extra}"


# ----------------------------------------------------------------------
# 6. COMMAND RUNNER — With pretty output
# ----------------------------------------------------------------------
def run_command(cmd, cwd=None, check=True, env=None):
    """
    Run command, print it, capture output, raise on error.
    Allow env vars to be used.
    """
    print(f"Running: {' '.join(cmd)}")
    final_env = os.environ.copy()
    if env:
        final_env.update(env)
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, env=final_env)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result

# ----------------------------------------------------------------------
# 7. WHEEL HANDLING
# ----------------------------------------------------------------------
def clean_dist(dist_dir: Path):
    """Nuke old builds — avoid stale artifacts."""
    if dist_dir.exists():
        print(f"Cleaning {dist_dir}...")
        for item in dist_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()


def build_wheel(dist_dir: Path, use_poetry: bool = True) -> Path:
    """
    Build wheel using Poetry (preferred) or fallback to `python -m build`.
    Why Poetry? It respects pyproject.toml extras, lockfile, etc.
    """
    dist_dir.mkdir(exist_ok=True)
    clean_dist(dist_dir)

    if use_poetry and shutil.which("poetry"):
        print("Building wheel with Poetry (no .pyc)…")
        run_command(["poetry", "build", "-f", "wheel", "--output", str(dist_dir)])
    else:
        print("Building wheel with python -m build (no .pyc)…")
        run_command([sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)])

    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError("No wheel built")
    latest = max(wheels, key=lambda f: f.stat().st_mtime)
    print(f"Built wheel: {latest.name}")
    return latest


def find_latest_wheel(dist_dir: Path):
    """Reuse existing wheel if --skip-build-wheel."""
    wheels = list(dist_dir.glob("*.whl"))
    return max(wheels, key=os.path.getmtime) if wheels else None


def extract_metadata_from_wheel(wheel: Path):
    """Parse METADATA from .whl to get name/version."""
    with zipfile.ZipFile(wheel) as z:
        meta = [f for f in z.namelist() if f.endswith(".dist-info/METADATA")]
        if not meta:
            raise ValueError("No METADATA in wheel")
        content = z.read(meta[0]).decode()
        name = re.search(r"^Name: (.+)", content, re.M).group(1)
        ver = re.search(r"^Version: (.+)", content, re.M).group(1)
        return name.strip(), ver.strip()


# ----------------------------------------------------------------------
# 8. .pyc CLEANUP — Defensive, even if disabled at build
# ----------------------------------------------------------------------
def remove_pyc(root: Path):
    """Delete any stray .pyc or __pycache__ dirs."""
    if not root.exists():
        return
    for f in root.rglob("*.pyc"):
        f.unlink()
        print(f"Removed {f}")
    for d in root.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)
        print(f"Removed {d}")


def extract_and_clean(wheel: Path) -> Path:
    """
    Extract wheel → temp dir → strip .pyc → return clean dir.
    Why extract? zipapp needs a directory, not a .whl.
    Why clean? Defensive — in case build slipped through.
    """
    extract_dir = Path(tempfile.mkdtemp(prefix="pipeline_"))
    with zipfile.ZipFile(wheel) as z:
        z.extractall(extract_dir)
    print("\nCleaning stray .pyc from extracted wheel…")
    remove_pyc(extract_dir)
    return extract_dir


# ----------------------------------------------------------------------
# 9. BUILDERS
# ----------------------------------------------------------------------
def build_zipapp_(clean_dir: Path, out_path: Path, entry: str):
    """
    Build pure-Python .pyz using zipapp.
    Why zipapp?
        • No dependencies
        • Works on Termux
        • Pure .py → maximum portability
    """
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
        "-c"  # compress
    ]
    run_command(cmd)
    out_path.chmod(0o755)
    print("zipapp built – pure .py, no .pyc")

def build_zipapp__(clean_dir: Path, out_path: Path, entry: str):
    """
    Build pure-Python .pyz using zipapp with --main.
    Why --main?
    • Avoids __main__.py in root → prevents MultiplexedPath crash
    • Works on Termux, Android, Python 3.12+
    • Cleaner, more reliable
    """
    print(f"\nBuilding zipapp → {out_path.name}")

    cmd = [
        sys.executable, "-m", "zipapp",
        str(clean_dir),
        "-p", "/usr/bin/env python3",
        "-o", str(out_path),
        "-c",
        "--main", f"{entry}(__import__('sys').argv[1:])" # the --main flag does not exist for zipapp
    ]
    run_command(cmd)
    out_path.chmod(0o755)
    print("zipapp built – pure .py, no .pyc, Termux-safe")

def build_zipapp(clean_dir: Path, out_path: Path, entry: str):
    """
    Build zipapp with isolated __main__.py in subdir.
    Relies on ./src/__main__.py already existing.

    Avoids:
    • MultiplexedPath crash (no it does not)
    • zipapp --main limitations
    • package name conflicts
    """
    print(f"\nBuilding zipapp → {out_path.name}")
   
    main_py = '''\
#!/usr/bin/env python3
import sys
from pipeline.cli import app
sys.exit(app())
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

def build_shiv(wheel: Path, out_path: Path, entry: str):
    """
    Build shiv .pyz from WHEEL (not extracted dir).
    Why wheel?
        • shiv requires pyproject.toml or setup.py
        • Extracted dir has neither → fails
        • Wheel has full metadata → works
    Why shiv?
        • Caches .pyc in ~/.shiv → fast second+ run
    """
    print(f"\nBuilding shiv → {out_path.name}")
    cmd = [
        "shiv",
        str(wheel),
        "-e", entry,
        "-o", str(out_path),
        "-p", "/usr/bin/env python3",
        "--compressed",
        "--no-cache",  # Don't bake .pyc — cache at runtime
        "--", "--no-binary=msgspec"
    ]
    env = {
        "PIP_PROGRESS_BAR": "on",
        "PIP_CACHE_DIR": "/data/data/com.termux/files/home/.cache/pip",
        "PIP_NO_INPUT": "1"
    }

    run_command(cmd, env=env)
    out_path.chmod(0o755)
    print("shiv built – fast startup after first run")


def build_pex(clean_dir: Path, out_path: Path, entry: str):
    """
    Build .pex — single-file executable.
    Why not on Termux?
        • Uses os.link() → fails on Android
    Currently unused.
    """
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
# 10. LAUNCHERS
# ----------------------------------------------------------------------
def generate_windows_launcher(pyz: Path, bat: Path):
    """Simple .bat wrapper for Windows."""
    bat.write_text(f"""@echo off
REM Windows launcher for {pyz.name}
"%~dp0{pyz.name}" %*
""")
    print(f"BAT : dist/{bat.name}")


def generate_macos_app(pyz: Path, app_dir: Path):
    """Stub .app for macOS."""
    app_dir.mkdir(parents=True, exist_ok=True)
    contents = app_dir / "Contents" / "MacOS"
    contents.mkdir(parents=True, exist_ok=True)
    exec_path = contents / pyz.name
    shutil.copy2(pyz, exec_path)
    exec_path.chmod(0o755)
    print(f"Generated macOS app: {app_dir.name}")


# ----------------------------------------------------------------------
# 11. METADATA STAMPING
# ----------------------------------------------------------------------
def write_version_file(src_pkg_dir: Path):
    """_version.py — for runtime inspection."""
    #file = dist_dir / "_version.py"
    #file = Path("src") / "pipeline" / "_version.py" # hardcode until fixed
    file = src_pkg_dir / "_version.py"
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
# 12. MAIN — The Grand Orchestrator
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Build pipeline-eds: wheel + zipapp + shiv + pex + launchers"
    )
    parser.add_argument("--windows", action="store_true", help="Include Windows extras")
    parser.add_argument("--shiv", action="store_true", help="Build shiv .pyz (fast repeat runs)")
    parser.add_argument("--mpl", action="store_true", help="Include matplotlib extras")
    parser.add_argument("--zoneinfo", action="store_true", help="Include zoneinfo")
    parser.add_argument("--entry-point", default=ENTRY_POINT, help="CLI entry point")
    parser.add_argument("--skip-build-wheel", action="store_true", help="Reuse existing wheel")
    args = parser.parse_args()

    # Build extras string: --windows--mpl
    extras = [e for e, f in [
        ("windows", args.windows),
        ("mpl", args.mpl),
        ("zoneinfo", args.zoneinfo)
    ] if f]
    extras_str = "-".join(extras) if extras else ""

    dist_dir = Path(DIST_DIR)
    dist_dir.mkdir(exist_ok=True)

    # --- 1. Wheel ---
    wheel = find_latest_wheel(dist_dir)
    if args.skip_build_wheel and wheel:
        print(f"Using existing wheel: {wheel.name}")
    else:
        wheel = build_wheel(dist_dir, use_poetry=did_poetry_make_the_call())
    print(f"Wheel : {wheel.name}")
    
    # --- 2. Extract once, clean once ---
    clean_dir = extract_and_clean(wheel)

    try:
        name, ver = extract_metadata_from_wheel(wheel)
        py_ver = get_python_version()
        os_tag = SystemInfo().get_os_tag()
        arch = SystemInfo().get_arch()
        bin_name = form_dynamic_binary_name(name, ver, py_ver, os_tag, arch, extras_str)

        # --- 3. Build artifacts ---
        if False: # not ph.on_termux(): *see "Why is build_zipapp disabled?"
            """
            Zipapp has known issues building on Termux.
            There are also implications regarding __main__.py filea.
            """
            """
            *Why is build_zipapp disabled?
            =============================

            The `zipapp` module (PEP 441) requires a `__main__.py` file in the **root** of the archive.
            When the source package also contains a `pipeline/__main__.py` (used for `python -m pipeline`),
            Python 3.12+ creates a **MultiplexedPath** to merge the zip archive with the import path.

            What is MultiplexedPath?
            ------------------------
            - Introduced in Python 3.12 to support *multiple* import sources (zip + filesystem).
            - It builds a virtual filesystem view: `sys.path[0]` = the .pyz archive.
            - When a name appears **both** as a file and a package directory, the loader fails:
            """
            zipapp_path = dist_dir / f"{bin_name}-zipapp.pyz"
            build_zipapp(clean_dir, zipapp_path, args.entry_point)
            print(f"Zipapp: {zipapp_path.name}")
            try:
                rel = zipapp_path.relative_to(dist_dir.parent)
                print(f"    ./{rel}  # or")
                print(f"    python {rel}")
            except ValueError:
                print(f"    {zipapp_path}")
                
        if True: #ph.on_termux() or args.shiv:
            # Filename ends with -shiv.pyz as requested
            shiv_path = dist_dir / f"{bin_name}-shiv.pyz"
            build_shiv(wheel, shiv_path, args.entry_point)
            print(f"Shiv : dist/{shiv_path.name}")
        if False: #not ph.on_termux():
            pex_path = dist_dir / f"{bin_name}.pex"
            build_pex(clean_dir, pex_path, args.entry_point)
            print(f"PEX : dist/{pex_path.name}")
        
        # --- 4. Launchers ---
        path = shiv_path
        generate_windows_launcher(path, path.with_suffix(".bat"))
        if False:
            generate_macos_app(path, path.with_suffix(".app"))

        write_version_file(SRC_PKG)

        # --- 5. FINAL SUMMARY: Copy-paste ready ---
        print("\n" + "="*70)
        print("BUILD COMPLETE")
        
    finally:
        # Always clean up temp dir
        shutil.rmtree(clean_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
