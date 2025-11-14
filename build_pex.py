#!/usr/bin/env python3
"""
build_pex.py
Builds a PEX file using Poetry's environment.
Safe for WSL2. Generates a Windows .bat launcher.
"""
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path
import argparse
import zipfile


# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------

def run(cmd, **kwargs):
    print(" ".join(cmd))
    subprocess.check_call(cmd, **kwargs)


def find_latest_wheel(dist: Path) -> Path:
    wheels = sorted(dist.glob("*.whl"), key=os.path.getmtime, reverse=True)
    if not wheels:
        raise SystemExit("No wheels found in dist/")
    return wheels[0]


# -------------------------------------------------------------
# Generate .bat launcher
# -------------------------------------------------------------
def write_bat(pex_path: Path):
    bat_path = pex_path.parent / (pex_path.stem + "-pex.bat")
    print(f"Writing Windows launcher: {bat_path}")

    content = f"""@echo off
REM Launcher for {pex_path.name}
SET PY_EXE=python.exe
PUSHD %~dp0
"%PY_EXE%" "{pex_path.name}" %*
POPD
"""
    bat_path.write_text(content, encoding="utf-8")


# -------------------------------------------------------------
# Read metadata from wheel
# -------------------------------------------------------------
def read_wheel_metadata(wheel_path: Path):
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(wheel_path) as z:
            z.extractall(tmp)

        for root, _, files in os.walk(tmp):
            if "METADATA" in files:
                meta = Path(root) / "METADATA"
                break
        else:
            raise SystemExit("METADATA not found inside wheel")

        name = None
        version = None

        for line in meta.read_text().splitlines():
            if line.startswith("Name:"):
                name = line.split(":")[1].strip()
            if line.startswith("Version:"):
                version = line.split(":")[1].strip()

        return name, version


# -------------------------------------------------------------
# Main
# -------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry-point",
                        default="pipeline.cli:app",
                        help="Override poetry entry point")
    parser.add_argument("--extras", nargs="*", default=[],
                        help="Extra tags for filename (windows, mpl, zoneinfo)")
    args = parser.parse_args()

    dist = Path("dist")
    dist.mkdir(exist_ok=True)

    # ---------------------------------------
    # Build wheel via Poetry
    # ---------------------------------------
    print("--- Building fresh wheel ---")
    run(["poetry", "build", "-f", "wheel"])

    wheel = find_latest_wheel(dist)
    print(f"Using wheel: {wheel}")

    pkg_name, pkg_version = read_wheel_metadata(wheel)
    print(f"Package: {pkg_name} {pkg_version}")

    pyver = f"py{sys.version_info.major}{sys.version_info.minor}"

    extras = "-" + "-".join(args.extras) if args.extras else ""
    out_name = f"{pkg_name}-{pkg_version}-{pyver}{extras}.pex"
    out_path = dist / out_name

    print(f"--- Building PEX: {out_path} ---")

    # ---------------------------------------
    # Build PEX inside Poetry environment
    # ---------------------------------------
    pex_cmd = [
        "poetry", "run", "python",
        "-m", "pex",
        str(wheel),
        "--output-file", str(out_path),
        "--entry-point", args.entry_point,
        "--python", "python3",
        "--python-shebang=/usr/bin/env python3",
    ]

    run(pex_cmd)

    print(f"PEX created: {out_path}")

    # ---------------------------------------
    # Generate Windows launcher
    # ---------------------------------------
    write_bat(out_path)

    print("\nDONE.")


if __name__ == "__main__":
    main()
