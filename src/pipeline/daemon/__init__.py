# pipeline/daemon/__init__.py
from src.pipeline.daemon.controller import main_cli
from src.pipeline.daemon.watchdog import is_daemon_running, check_and_restart_if_needed  

import sys
import os
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "projects")))

def main():
    # Check if the daemon is already running
    if is_daemon_running():
        print("Daemon is already running.")
        return
    
    print("Starting the daemon...")
    # Here you could include any other code for initializing or starting the daemon.
    # For example:
    # start_daemon()

    # Optionally check if a restart is necessary
    check_and_restart_if_needed()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python -m pipeline.daemon -start | -stop | -status")
    else:
        main_cli(sys.argv[1])
