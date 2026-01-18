#!/usr/bin/env python3
import subprocess, sys, platform
from pathlib import Path
from datetime import datetime

# ---------- CONFIG ----------
python_exe = Path("C:/Program Files/Python311/python.exe") if platform.system()=="Windows" else Path("/usr/bin/python3.11")
project_root = Path(__file__).parent.resolve()
venv_dir = project_root / ".venv311"
venv_python = venv_dir / ("Scripts/python.exe" if platform.system()=="Windows" else "bin/python")
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

def log(msg):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    (log_dir/"bootstrap.log").write_text(f"{t}  {msg}\n", encoding="utf-8", append=True)

def run(cmd):
    log(f"Running: {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True)

# ---------- VENV ----------
if not venv_python.exists(): run([str(python_exe), "-m", "venv", str(venv_dir)])
run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "uv"])
run([str(venv_python), "-m", "uv", "install", "--no-interaction", "--no-root", "--quiet"])

# ---------- LAUNCH DAEMON ----------
log("Launching daemon")
subprocess.Popen(
    [str(venv_python), "-m", "workspaces.eds_to_rjn.scripts.daemon_runner", "main"],
    cwd=str(project_root),
    stdout=open(log_dir/"daemon_output.log","a",encoding="utf-8"),
    stderr=open(log_dir/"daemon_error.log","a",encoding="utf-8"),
)
log("Daemon launched successfully")
