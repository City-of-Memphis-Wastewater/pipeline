#@echo off
$env:PYTHONPATH="src"
where poetry
poetry --version
#poetry run python -m projects.eds_to_rjn.scripts.daemon_runner >> daemon_log.txt 2>&1
poetry run python -m projects.eds_to_rjn.scripts.main