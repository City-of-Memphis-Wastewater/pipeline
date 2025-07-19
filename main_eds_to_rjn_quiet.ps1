# Program: %SystemRoot%\system32\WindowsPowerShell\v1.0\powershell.exe
# Add arguments: -NoProfile -ExecutionPolicy Bypass -File "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline38\main_tunnel_quiet.ps1" > "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline\logs\launch_log.txt" 2>&1
# Start in : C:\Users\GEORGE.BENNETT\Documents\dev\pipeline38\
#
$logDir = "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline38\logs"
## $env:TUNNEL_ORIGIN_CERT = "C:\Users\GEORGE.BENNETT\.cloudflared\cert.pem"
$workingDir = "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline38"

## Start-Process -FilePath "C:\Program Files\cloudflared\cloudflared.exe" `
##     -ArgumentList "--config", "C:\Users\george.bennett\.cloudflared\config.yml", "tunnel", "run", "pipeline-api" `
##     -WindowStyle Hidden `
##     -RedirectStandardOutput "$logDir\cloudflared_output.log" `
##     -RedirectStandardError "$logDir\cloudflared_error.log"
	
# Install dependencies via pip first (wait for it to finish)
Start-Process -FilePath "python.exe" `
    -ArgumentList "-m", "pip", "install", "-r", "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline38\requirements-38.txt" `
    -WorkingDirectory $workingDir `
    -Wait -NoNewWindow

Start-Process -FilePath "python.exe" `
    -ArgumentList "-m", "pip", "install", "--upgrade", "importlib-metadata==4.8.3" `
    -WorkingDirectory $workingDir `
    -Wait -NoNewWindow

#Start-Process -FilePath "C:\Users\GEORGE.BENNETT\.pyenv\pyenv-win\shims\poetry.bat" `
Start-Process -FilePath "python.exe" `
    -ArgumentList "-m", "projects.eds_to_rjn.scripts.daemon_runner", "main" `
    -WorkingDirectory $workingDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput "$logDir\daemon_eds_to_rjn_output.log" `
    -RedirectStandardError "$logDir\daemon_eds_to_rjn_error.log"
