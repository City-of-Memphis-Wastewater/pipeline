#!bin/bash
source .venv/bin/activate
export PYTHONPATH=$(pwd)/src
python -m pipeline.cli --help
