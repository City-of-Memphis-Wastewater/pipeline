# dummy __init__.py to point to original 'pipeline' package
from pipeline import *  # import everything from the original package

# optionally, explicitly expose CLI entry points
from pipeline.cli import app
