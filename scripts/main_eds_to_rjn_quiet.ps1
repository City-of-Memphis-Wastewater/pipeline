# Program: %SystemRoot%\system32\WindowsPowerShell\v1.0\powershell.exe
# Add arguments: -NoProfile -ExecutionPolicy Bypass -File "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline38\main_tunnel_quiet.ps1" > "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline38\logs\launch_log.txt" 2>&1


# Get the script directory (the folder where this script lives)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Define paths relative to script directory
#$projectRoot = $scriptDir  # if scripts are in root
$projectRoot = Split-Path -Parent $scriptDir  # one level up from scripts/
$LogDir = Join-Path $projectRoot "logs"
$RequirementsFile = Join-Path $projectRoot "requirements.txt"

# Run setup script
## Write-Output "Running virtual environment setup..."
## powershell.exe -NoProfile -ExecutionPolicy Bypass -File $venvSetupScript
	
#Start-Process -FilePath "C:\Users\GEORGE.BENNETT\.pyenv\pyenv-win\shims\poetry.bat" `
Start-Process -FilePath "python.exe" `
    -ArgumentList "-m", "workspaces.eds_to_rjn.scripts.daemon_runner", "main" `
    -WorkingDirectory $projectRoot `
    -RedirectStandardOutput (Join-Path $LogDir "daemon_eds_to_rjn_output.log") `
    -RedirectStandardError (Join-Path $LogDir "daemon_eds_to_rjn_error.log")
	-WindowStyle Hidden `
	