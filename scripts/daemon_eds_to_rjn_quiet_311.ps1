# ----- CONFIG -----
$python311 = "C:\Program Files\Python311\python.exe"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvDir = Join-Path $projectRoot ".venv311"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

$logDir = Join-Path $projectRoot "logs"
$logFile = Join-Path $logDir "bootstrap.log"

function Log($msg) {
    $timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    "$timestamp  $msg" | Out-File -FilePath $logFile -Append -Encoding UTF8
}

# ----- STARTUP -----
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

Log "==== Startup trigger ===="

# ----- CREATE VENV IF MISSING -----
if (!(Test-Path $venvPython)) {
    Log "Creating venv using Python 3.11"
    & $python311 -m venv $venvDir
} else {
    Log "venv already exists; skipping creation"
}

# ----- PIP + POETRY INSTALL (idempotent) -----
Log "Ensuring pip + poetry installed"

& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install poetry --quiet

# ----- DEPENDENCY INSTALL (minimal output, idempotent) -----
Log "Running poetry install (dependencies only)"

& $venvPython -m poetry install --no-interaction --no-root --quiet

if ($LASTEXITCODE -ne 0) {
    Log "ERROR: Poetry install failed (exit $LASTEXITCODE)"
} else {
    Log "Poetry install completed (no update, dependencies satisfied)"
}

# ----- RUN DAEMON -----
Log "Launching daemon"

Start-Process $venvPython `
    -ArgumentList "-m workspaces.eds_to_rjn.scripts.daemon_runner main" `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $logDir "daemon_output.log") `
    -RedirectStandardError  (Join-Path $logDir "daemon_error.log")

Log "Daemon launched successfully"
