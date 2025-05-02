# tasks/watchdog_trigger.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'projects')))

from pipeline.daemon import watchdog


if __name__ == "__main__":
    watchdog.check_and_restart_if_needed()
