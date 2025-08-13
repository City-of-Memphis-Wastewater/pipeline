@echo off

REM Log current timestamp with TimeManager formatting
poetry run python -c "from src.pipeline.time_manager import TimeManager; print('----', TimeManager.now().as_formatted_date_time(), '----')" >> logs/daemon_log.txt

REM Show Poetry version
poetry --version

REM Run the daemon runner and log output & errors
poetry run python -m workspaces.eds_to_rjn.scripts.daemon_runner main>> logs/daemon_log.txt 2>&1
