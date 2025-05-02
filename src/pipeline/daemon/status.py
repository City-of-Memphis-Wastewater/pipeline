# src/daemon/status.py
from datetime import datetime
import json, os

STATUS_PATH = "exports/status_daemon_log.txt"

def update_status(state: str, msg: str = ""):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "status": state,
        "message": msg,
    }
    with open(STATUS_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def get_latest_status():
    if not os.path.exists(STATUS_PATH):
        return {"status": "unknown", "message": ""}
    with open(STATUS_PATH) as f:
        lines = f.readlines()
        return json.loads(lines[-1]) if lines else {"status": "unknown", "message": ""}
