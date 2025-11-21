#!/usr/bin/env python3
import sys
import platform
import shutil
import os
from pathlib import Path
from subprocess import run

# Project paths
ROOT = Path(__file__).parent.resolve()
CLI_ENTRY = ROOT / "src" / "pipeline" / "cli.py"
STATIC    = ROOT / "src" / "pipeline" / "interface" / "web_gui" / "static"
TEMPLATES = ROOT / "src" / "pipeline" / "interface" / "web_gui" / "templates"

# Version from pyproject.toml
def get_version() -> str:
    import toml
    data = toml.load(ROOT / "pyproject.toml")
    return data["tool"]["poetry"]["version"]

VERSION = get_version()
PY_TAG  = f"py{sys.version_info.major}{sys.version_info.minor}"
OS_TAG  = "android" if "TERMUX_VERSION" in os.environ else platform.system().lower()
ARCH    = platform.machine().lower()
NAME    = f"pipeline-eds-{VERSION}-{PY_TAG}-{OS_TAG}-{ARCH}"

def clean():
    for item in ("build", f"{NAME}.spec"):
        p = Path(item)
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()

def generate_rc():
    if not sys.platform.startswith("win"):
        return None
    tmpl = ROOT / "version.rc.template"
    if not tmpl.exists():
        return None
    rc = ROOT / "version.rc"
    content = tmpl.read_text(encoding="utf-8")
    major, minor, patch = VERSION.split(".")[:3] + ["0"]
    content = content.replace("{{VERSION}}", VERSION)
    content = content.replace("{{FILEVERSION}}", f"{major},{minor},{patch},0")
    content = content.replace("{{PRODUCTVERSION}}", f"{major},{minor},{patch},0")
    rc.write_text(content, encoding="utf-8")
    return rc

def build():
    clean()
    print(f"Building {NAME}")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--clean",
        f"--name={NAME}",
    ]

    rc_file = generate_rc()
    if rc_file:
        cmd.append(f"--version-file={rc_file}")

    sep = ";" if sys.platform.startswith("win") else ":"
    cmd += [
        f"--add-data={STATIC}{sep}pipeline/interface/web_gui/static",
        f"--add-data={TEMPLATES}{sep}pipeline/interface/web_gui/templates",
    ]

    cmd.append(str(CLI_ENTRY))

    print("Command:", " ".join(cmd))
    run(cmd, check=True)

    suffix = ".exe" if sys.platform.startswith("win") else ""
    exe = Path("dist") / f"{NAME}{suffix}"
    exe.chmod(0o755)

    print("\nBuild finished")
    print(f"Executable: {exe}")
    print(f"Size: {exe.stat().st_size // 1024 // 1024} MiB\n")

if __name__ == "__main__":
    build()
