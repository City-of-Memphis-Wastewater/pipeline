#!/usr/bin/env python3
"""
Generate src/pipeline/_version.py and copy it to dist/ after a build.

./tools/generate_version.py
"""

import datetime
import pathlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]   # repo root
SRC_PKG = PROJECT_ROOT / "src" / "pipeline"
DIST = PROJECT_ROOT / "dist"

def get_version() -> str:
    """Read version from pyproject.toml (Poetry)"""
    import tomllib  # Python 3.11+; fallback for <3.11 below
    with open(PROJECT_ROOT / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["tool"]["poetry"]["version"]

def get_git_rev() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"

def main() -> None:
    version = get_version()
    git_rev = get_git_rev()
    now = datetime.datetime.utcnow().isoformat(timespec="microseconds")

    content = f'''\
# Auto-generated version file – DO NOT EDIT
__version__ = "{version}"
__git__ = "{git_rev}"
__build_time__ = "{now}"
'''

    # 1. Write inside the package (so it ends up in the wheel)
    (SRC_PKG / "_version.py").write_text(content)
    print(f"Version file written to {SRC_PKG / '_version.py'}")

    # 2. Also copy to dist/ for the release assets
    DIST.mkdir(exist_ok=True)
    (DIST / "_version.py").write_text(content)
    print(f"Version file copied to {DIST / '_version.py'}")

if __name__ == "__main__":
    main()
