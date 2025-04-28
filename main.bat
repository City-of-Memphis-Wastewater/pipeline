@echo off
where poetry
poetry --version
poetry run python -m projects.eds_to_rjn.scripts.main >> daemon_log.txt 2>&1