@echo off
REM -------------------------------
REM Task Scheduler launcher for run_daemon_minimal.py
REM -------------------------------

REM Absolute path to Python 3.11
set PYTHON_EXE="C:\Program Files\Python311\python.exe"

REM Absolute path to the Python launcher script
set SCRIPT_PATH="C:\path\to\project\run_daemon_minimal.py"

REM Run Python script hidden
start "" /B %PYTHON_EXE% %SCRIPT_PATH%
