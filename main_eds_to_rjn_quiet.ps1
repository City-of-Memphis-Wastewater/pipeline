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

# --- Paths & Directories ---
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$logDir = Join-Path $projectRoot "logs"
$workingDir = $projectRoot
$requirementsFile = Join-Path $projectRoot "requirements-38.txt"

# Folder where this script lives
#$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
# Project root is one level above the scripts folder
#$projectRoot = Split-Path -Parent $ScriptDir

# -----------------------------
# Install dependencies
# -----------------------------
# Ensures all required packages are installed before running daemon
Start-Process -FilePath "python.exe" `
    -ArgumentList "-m", "pip", "install", "-r", "$requirementsFile" `
    -WorkingDirectory $workingDir `
    -Wait -NoNewWindow

# -----------------------------
# Run the daemon
# -----------------------------
# Launches the daemon_runner module with 'main' argument
# Output and errors are redirected to log files
Start-Process -FilePath "python.exe" `
    -ArgumentList "-m", "workspaces.eds_to_rjn.scripts.daemon_runner", "main" `
    -WorkingDirectory $workingDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $logDir "daemon_eds_to_rjn_output.log") `
    -RedirectStandardError  (Join-Path $logDir "daemon_eds_to_rjn_error.log")

# -----------------------------
# End of script
# -----------------------------
