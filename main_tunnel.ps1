Start-Process -FilePath "C:\Program Files\cloudflared\cloudflared.exe" -ArgumentList "tunnel run"
Start-Process -FilePath "C:\Users\GEORGE.BENNETT\.pyenv\pyenv-win\shims\poetry.bat" -ArgumentList "run python -m pipeline.api.eds demo-webplot-live"
