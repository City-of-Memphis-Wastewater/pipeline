@echo off

REM Log current timestamp with TimeManager formatting
uv run python -c "from pipeline_eds.time_manager import TimeManager; print('----', TimeManager.now().as_formatted_date_time(), '----')" >> logs/daemon_log.txt

REM Show uv version
uv --version

REM Run the daemon runner and log output & errors
uv run python -m workspaces.eds_to_rjn.scripts.daemon_runner main>> logs/daemon_log.txt 2>&1
