# src/pipeline/daemon/watchdog.py

import os
import logging
from pipeline.daemon import controller

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def is_daemon_running():
    """
    Check if the daemon is currently running by checking the flag file.
    """
    return os.path.exists(controller.RUNNING_FLAG)

def check_and_restart_if_needed():
    """
    Check if the daemon is running, and restart it if not.
    """
    if not is_daemon_running():
        logger.warning("Daemon is not running. Restarting now...")
        controller.log_status("Watchdog detected daemon was stopped. Restarting...")
        controller.start_daemon()
    else:
        logger.info("Daemon is running. No restart needed.")
