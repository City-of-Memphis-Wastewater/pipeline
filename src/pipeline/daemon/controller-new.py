import os
import logging
import importlib
from pipeline.projectmanager import ProjectManager

# Paths
RUNTIME_DIR = os.path.join(os.getenv("APPDATA", os.path.expanduser("~/.config")), "memphis_pipeline", "runtime")
RUNNING_FLAG = os.path.join(RUNTIME_DIR, "daemon_running.flag")
STATUS_LOG = os.path.join(RUNTIME_DIR, "daemon_status.log")

# Ensure runtime dir exists
os.makedirs(RUNTIME_DIR, exist_ok=True)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def log_status(message: str):
    with open(STATUS_LOG, "a") as f:
        f.write(f"{message}\n")
    logger.info(message)

def write_running_flag():
    with open(RUNNING_FLAG, "w") as f:
        f.write("running")

def remove_running_flag():
    if os.path.exists(RUNNING_FLAG):
        os.remove(RUNNING_FLAG)

def start_daemon():
    """
    Starts the daemon process for the identified project and runs its `run_daemon()` function.
    """
    default_project = ProjectManager.identify_default_project()
    module_path = f"projects.{default_project}.main"
    project_module = importlib.import_module(module_path)

    # Get and call the `run_daemon` function from the project module
    run_daemon = getattr(project_module, "run_daemon")
    write_running_flag()
    run_daemon()
    remove_running_flag()
