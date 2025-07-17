# Program: %SystemRoot%\system32\WindowsPowerShell\v1.0\powershell.exe
# Add arguments: -NoProfile -ExecutionPolicy Bypass -File "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline\main_tunnel_quiet.ps1" > "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline\logs\launch_log.txt" 2>&1
# Start in : C:\Users\GEORGE.BENNETT\Documents\dev\pipeline\
$logDir = "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline\logs"
$env:TUNNEL_ORIGIN_CERT = "C:\Users\GEORGE.BENNETT\.cloudflared\cert.pem"

Start-Process -FilePath "C:\Program Files\cloudflared\cloudflared.exe" `
	-ArgumentList "--config", "C:\Users\george.bennett\.cloudflared\config.yml", "tunnel", "run", "pipeline-api" `
    -WindowStyle Hidden `
    -RedirectStandardOutput "$logDir\cloudflared_output.log" `
    -RedirectStandardError "$logDir\cloudflared_error.log"
	
# Install dependencies via pip first (wait for it to finish)
Start-Process -FilePath "python.exe" `
    -ArgumentList "-m", "pip", "install", "-r", "C:\Users\GEORGE.BENNETT\Documents\dev\pipeline\requirements.txt" `
    -Wait -NoNewWindow

Start-Process -FilePath "python.exe" `
	-ArgumentList "-m", "pip", "install", "--upgrade", "importlib-metadata==4.8.3" `
	-Wait -NoNewWindow

#Start-Process -FilePath "C:\Users\GEORGE.BENNETT\.pyenv\pyenv-win\shims\poetry.bat" `
Start-Process -FilePath "python.exe" `
	-ArgumentList "-m", "src.pipeline.api.eds", "demo-webplot-live" `
    -WindowStyle Hidden `
    -RedirectStandardOutput "$logDir\webplot_output.log" `
    -RedirectStandardError "$logDir\webplot_error.log"