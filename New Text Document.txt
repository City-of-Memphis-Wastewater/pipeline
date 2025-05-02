@echo off
cd C:\Users\george.bennett\OneDrive - City of Memphis\Documents\dev\pipeline
poetry --version
timeout /t 5
poetry run python -m tasks.watchdog_trigger