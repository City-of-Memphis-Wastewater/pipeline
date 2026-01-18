# Program: %SystemRoot%\system32\WindowsPowerShell\v1.0\powershell.exe
# Add arguments: -NoProfile -ExecutionPolicy Bypass -File "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline\main_tunnel_quiet.ps1" > "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline\logs\launch_log.txt" 2>&1

# Get the script directory (the folder where this script lives)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Define paths relative to script directory
#$projectRoot = $scriptDir  # if scripts are in root
$projectRoot = Split-Path -Parent $scriptDir  # one level up from scripts/

$LogDir = Join-Path $projectRoot "logs"
$CloudflaredConfig = Join-Path $env:USERPROFILE ".cloudflared\config.yml"
$CloudflaredCert = Join-Path $env:USERPROFILE ".cloudflared\cert.pem"
#$RequirementsFile = Join-Path $projectRoot "requirements.txt"

# Set environment variable for cloudflared cert
$env:TUNNEL_ORIGIN_CERT = $CloudflaredCert

Write-Host "Starting cloudflared tunnel and Plotly server..."

# Run setup script
## Write-Output "Running virtual environment setup..."
## powershell.exe -NoProfile -ExecutionPolicy Bypass -File $venvSetupScript
	
	
Start-Process -FilePath "C:\Program Files\cloudflared\cloudflared.exe" `
    -ArgumentList "--config", $CloudflaredConfig, "tunnel", "run", "pipeline-api" `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $LogDir "cloudflared_output.log") `
    -RedirectStandardError (Join-Path $LogDir "cloudflared_error.log")

# Launch the Plotly demo Python module
Start-Process -FilePath "python.exe" `
    -ArgumentList "-m", "src.pipeline_eds.api.eds", "demo-webplot-live" `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $LogDir "webplot_output.log") `
    -RedirectStandardError (Join-Path $LogDir "webplot_error.log")