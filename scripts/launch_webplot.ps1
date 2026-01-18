# Get script folder (where this .ps1 lives)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
#$projectRoot = $scriptDir  # if scripts are in root
$projectRoot = Split-Path -Parent $scriptDir  # one level up from scripts/


# Use script dir for setup_venv.ps1 and .venv folder
$venvSetupScript = Join-Path $scriptDir "setup_venv.ps1"
$venvPath = Join-Path $projectRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

# Use environment variable for logs under Documents
$logDir = Join-Path $projectRoot "logs"

# Run setup script
## Write-Output "Running virtual environment setup..."
## powershell.exe -NoProfile -ExecutionPolicy Bypass -File $venvSetupScript

# Launch Python app
# Launch the Plotly demo Python module
Write-Output "Launching the main Python application..."
Start-Process -FilePath $pythonExe `
    -ArgumentList "-m", "src.pipeline_eds.api.eds", "demo-webplot-live" `
	-WorkingDirectory $projectRoot `
    -RedirectStandardOutput (Join-Path $logDir "webplot_output.log") `
    -RedirectStandardError (Join-Path $logDir "webplot_error.log") `
	#-WindowStyle Hidden 
	
