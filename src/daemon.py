import importlib.util
import os
import time
import json
import datetime
from typing import Callable, Any


from src.project_manager import ProjectManager

# ----------------------------
# JARGON GLOSSARY
# ----------------------------
# Daemon       : A background process that runs continuously to perform scheduled tasks
# Snapshot     : A small data capture (e.g., current sensor values)
# Aggregate    : A compiled summary (e.g., 12 snapshots per hour)
# Ingestion    : The process of collecting, transforming, and preparing data for use or export
# Hook         : A function that can be plugged into a modular system (e.g., data retrieval or export)
# UTC Time     : Coordinated Universal Time, used for consistency in timestamping

# ----------------------------
# CONFIGURABLE HOOKS (to be passed into the Daemon)
# ----------------------------

# These should be implemented elsewhere in your project to stay modular

def load_snapshot_hook(pm: ProjectManager) -> Callable[[], dict]:
    """
    Dynamically load retrieve_snapshot_data() from the project's main.py script.
    """
    script_path = pm.get_scripts_file_path("main.py")

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"No main.py found at: {script_path}")

    spec = importlib.util.spec_from_file_location("main", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "retrieve_snapshot_data"):
        raise AttributeError(f"'retrieve_snapshot_data()' not found in {script_path}")

    return getattr(module, "retrieve_snapshot_data")

def retrieve_snapshot_data() -> dict:
    """
    Return live data as a dictionary. Should include timestamp and sensor data.
    """
    import script from current project, in the main file at pm.get_scripts_dir()
    raise NotImplementedError("You must implement retrieve_snapshot_data()")

def run_hourly_ingestion(pm: ProjectManager):
    """
    Called once per hour. Should load stored snapshots, aggregate them,
    and POST or export the final data.
    """
    raise NotImplementedError("You must implement run_hourly_ingestion()")

# ----------------------------
# THE GENERIC DAEMON CLASS
# ----------------------------

class DataCaptureDaemon:
    def __init__(self, project_manager: ProjectManager,
                 snapshot_hook: Callable[[], dict],
                 hourly_hook: Callable[[ProjectManager], Any]):
        self.pm = project_manager
        self.snapshot_hook = snapshot_hook
        self.hourly_hook = hourly_hook
        self.last_hour = None

    def log(self, message: str):
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"[{timestamp}] {message}")

    def get_snapshot_path(self, timestamp: datetime.datetime) -> str:
        """
        Build a timestamped path for the snapshot file.
        """
        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M")
        filename = f"snapshot_{date_str}_{time_str}.json"
        self.pm.create_imports_dir()
        return self.pm.get_imports_file_path(filename)

    def save_snapshot(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        snapshot = self.snapshot_hook()
        snapshot["timestamp"] = now.isoformat()

        path = self.get_snapshot_path(now)
        with open(path, "w") as f:
            json.dump(snapshot, f, indent=2)

        self.log(f"Saved snapshot to {path}")

    def run(self):
        self.log("Starting data capture daemon...")

        while True:
            now = datetime.datetime.now(datetime.timezone.utc)

            # Every 5 minutes
            if now.minute % 5 == 0 and now.second < 5:
                try:
                    self.save_snapshot()
                except Exception as e:
                    self.log(f"[ERROR] Snapshot failed: {e}")

            # Every hour on the hour
            if now.minute == 0 and now.hour != self.last_hour:
                try:
                    self.log("Running hourly ingestion...")
                    self.hourly_hook(self.pm)
                    self.last_hour = now.hour
                except Exception as e:
                    self.log(f"[ERROR] Hourly ingestion failed: {e}")

            time.sleep(5)  # check every few seconds for clock alignment

# ----------------------------
# MAIN ENTRY POINT
# ----------------------------

if __name__ == "__main__":
    # Dynamically identify the default-project from TOML
    project_name = ProjectManager.identify_default_project()
    pm = ProjectManager(project_name)

    # Dynamically load the hook from the default-project's script
    snapshot_hook = load_snapshot_hook(pm)

    # Pass all into the daemon
    daemon = DataCaptureDaemon(
        project_manager=pm,
        snapshot_hook=snapshot_hook,
        hourly_hook=run_hourly_ingestion
    )

    daemon.run()