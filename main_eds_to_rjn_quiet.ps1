<#
.SYNOPSIS
    Launches the EDS-to-RJN daemon in a Python 3.8 environment.

.DESCRIPTION
    - Computes project paths dynamically, making the script portable.
    - Installs Python dependencies from a pinned requirements file (Python 3.8-safe).
    - Runs the daemon_runner module in the background with logs redirected.
    - Safe to use with Task Scheduler or interactive launch.
#>

# -----------------------------
# Compute script-relative paths
# -----------------------------

# Folder where this script lives
#$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
# Project root is one level above the scripts folder
#$projectRoot = Split-Path -Parent $ScriptDir

# --- Paths & Directories ---
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$logDir = Join-Path $projectRoot "logs"
$workingDir = $projectRoot
$requirementsFile = Join-Path $projectRoot "requirements-38.txt"
$venvDir = Join-Path $projectRoot "venv38"

# --- Ensure logs directory exists ---
if (-not (Test-Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory | Out-Null
}

# --- Create venv if it doesn't exist ---
if (-not (Test-Path "$venvDir\Scripts\python.exe")) {
    python -m venv $venvDir
}

# --- Activate venv and install dependencies ---
$venvPython = Join-Path $venvDir "Scripts\python.exe"
Start-Process -FilePath $venvPython `
    -ArgumentList "-m", "pip", "install", "-r", "$requirementsFile" `
    -WorkingDirectory $workingDir `
    -Wait -NoNewWindow

# --- Run daemon using venv Python ---
Start-Process -FilePath $venvPython `
    -ArgumentList "-m", "projects.eds_to_rjn.scripts.daemon_runner", "main" `
    -WorkingDirectory $workingDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $logDir "daemon_eds_to_rjn_output.log") `
    -RedirectStandardError  (Join-Path $logDir "daemon_eds_to_rjn_error.log")

# -----------------------------
# End of script
# -----------------------------
