# Get the directory where this script lives
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
#$projectRoot = $scriptDir  # if scripts are in root
$projectRoot = Split-Path -Parent $scriptDir  # one level up from scripts/

# Define venv path relative to script folder (you can customize this)
$venvPath = Join-Path $projectRoot ".venv"

# Logs folder inside user's Documents (adjust relative to your liking)
$logDir = Join-Path $projectRoot "logs"


# Ensure logs folder exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

if (-Not (Test-Path $venvPath)) {
    Write-Output "Creating virtual environment at $venvPath ..."
    python -m venv $venvPath
} else {
    Write-Output "Virtual environment already exists at $venvPath"
}

# Activate venv executables
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$pipExe = Join-Path $venvPath "Scripts\pip.exe"

# Upgrade pip first
Write-Output "Upgrading pip..."
& $pythonExe -m pip install --upgrade pip > (Join-Path $logDir "pip_upgrade.log") 2>&1

# Install dependencies (requirements.txt relative to script folder)
$requirementsPath = Join-Path $projectRoot "requirements.txt"

Write-Output "Installing dependencies from $requirementsPath ..."
& $pipExe install -r $requirementsPath > (Join-Path $logDir "pip_install.log") 2>&1

# Optional: Upgrade importlib-metadata pinned version (if needed)
Write-Output "Upgrading importlib-metadata..."
& $pipExe install --upgrade importlib-metadata==4.8.3 >> (Join-Path $logDir "pip_install.log") 2>&1

Write-Output "Virtual environment setup completed!"
