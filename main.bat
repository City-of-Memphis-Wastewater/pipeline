@echo off

REM Log current timestamp with TimeManager formatting
poetry run python -c "from pipeline.time_manager import TimeManager; print('----', TimeManager.now().as_formatted_date_time(), '----')" >> daemon_log.txt

REM Show Poetry version
poetry --version

REM Run the daemon runner and log output & errors
poetry run python -m projects.eds_to_rjn.scripts.daemon_runner >> daemon_log.txt 2>&1
