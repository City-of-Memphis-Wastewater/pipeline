# pipeline/__init__.py
from importlib.resources import files
from pipeline_eds.workspace_manager import WorkspaceManager,establish_default_workspace

__all__ = ["WorkspaceManager","establish_default_workspace", "variable_clarity", "time_manager", "web_utils", "helpers"]

# Ensure static web assets are bundled in frozen binaries (shiv/PyInstaller)
try:
    files("pipeline_eds.interface.web_gui.static")
    files("pipeline_eds.interface.web_gui.templates")
except Exception:
    pass
