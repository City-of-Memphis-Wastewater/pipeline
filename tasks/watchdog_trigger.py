# tasks/watchdog_trigger.py
from pipeline.daemon import watchdog

if __name__ == "__main__":
    watchdog.check_and_restart_if_needed()
