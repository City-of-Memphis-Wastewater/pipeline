# src/pipeline/daemon/watchdog.py

import os
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def is_daemon_running():
    """
    Check if the daemon is currently running by checking the flag file.
    """
    from pipeline.daemon import controller
    return os.path.exists(controller.RUNNING_FLAG)

def check_and_restart_if_needed():
    """
    Check if the daemon is running, and restart it if not.
    """
    from pipeline.daemon import controller
    if not is_daemon_running():
        logger.warning("Daemon is not running. Restarting now...")
        controller.log_status("Watchdog detected daemon was stopped. Restarting...")
        controller.start_daemon()
    else:
        logger.info("Daemon is running. No restart needed.")


import os
import psutil
import subprocess
from pipeline.projectmanager import ProjectManager
import logging

logger = logging.getLogger(__name__)

PID_FILE = "daemon.pid"  # Could be placed in %APPDATA% or a temp dir

def is_process_running(pid):
    return psutil.pid_exists(pid) and psutil.Process(pid).status() != psutil.STATUS_ZOMBIE

def check_and_restart_if_needed():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            if is_process_running(pid):
                logger.info("Daemon is running. No restart needed.")
                return
            else:
                logger.warning("Stale PID found. Daemon not alive.")
        except Exception as e:
            logger.error(f"Error reading PID file: {e}")
    else:
        logger.info("No PID file found. Daemon not running.")

    logger.info("Restarting daemon...")

    # Determine which project to run
    project_name = ProjectManager.identify_default_project()
    daemon_script = f"projects/{project_name}/scripts/main.py"

    # Start the daemon (e.g., via subprocess)
    process = subprocess.Popen(["poetry", "run", "python", daemon_script])
    with open(PID_FILE, 'w') as f:
        f.write(str(process.pid))
    logger.info(f"Daemon started with PID {process.pid}")



