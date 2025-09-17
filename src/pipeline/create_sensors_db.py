# create_sensors_db.py
import sqlite3
from pathlib import Path
import os
import sys
import shutil
import sqlite3
from pathlib import Path
from importlib import resources

# Your sensor data here:
sensors_data = [
    # (idcs, iess, zd, units, description)
    ("M310LI", "M310LI.UNIT0@NET0", "Maxson", "Inches", "Wet Well Level"),
    ("M100FI", "M100FI.UNIT0@NET0", "Maxson", "MGD", "Influent Flow"),
    ("D-321E", "D-321E.UNIT0@NET0", "Maxson", "MG/L", "PAA Dose"),
    ("FI8001", "FI8001.UNIT0@NET0", "Maxson", "MGD", "Effluent Flow"),
    ("I-0201A", "I-0201A.UNIT1@NET1", "WWTF", "", ""),
    ("I-5005A", "I-5005A.UNIT1@NET1", "WWTF", "MGD", "Plant Influent Flow"),
]

# -----------------------------
# Rollout packaged DB
# -----------------------------

def ensure_user_db() -> Path:
    """Copy packaged DB to user folder if it doesn't exist."""
    user_db = get_user_db_path()
    packaged_db = get_packaged_db_path()
    if not user_db.exists() and packaged_db.exists():
        with resources.as_file(resources.files("pipeline.data") / "sensors.db") as packaged_db:
            print(f"packaged_db = {packaged_db}")
            shutil.copy(packaged_db, user_db)
    if not packaged_db.exists():
        packaged_db = create_packaged_db()
        user_db = reset_user_db(packaged_db)
    return user_db

# -----------------------------
# DB connection
# -----------------------------
def get_db_connection():
    db_path = ensure_user_db()
    conn = sqlite3.connect(db_path)
    return conn

# -----------------------------
# Packaged DB location
# -----------------------------
def get_packaged_db_path() -> Path:
    db_path = Path(__file__).parent / "data" / "sensors.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path

# -----------------------------
# User DB location
# -----------------------------

def get_user_db_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"

    user_dir = base / "pipeline"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "sensors.db"

#def get_packaged_db_path() -> Path:
#    packaged_db = resources.as_file(resources.files("pipeline.data") / "sensors.db")
#    return packaged_db

# -----------------------------
# Create packaged DB
# -----------------------------
def create_packaged_db():
    db_path = get_packaged_db_path()
    if db_path.exists():
        print(f"⚠️ {db_path} already exists. Overwriting...")
        db_path.unlink()
    else:
        print(f"✅ Creating Packaged DB at {db_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE sensors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idcs TEXT NOT NULL,
            iess TEXT NOT NULL,
            zd TEXT NOT NULL,
            units TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)

    cur.executemany(
        "INSERT INTO sensors (idcs, iess, zd, units, description) VALUES (?, ?, ?, ?, ?)",
        sensors_data
    )

    conn.commit()
    conn.close()
    return db_path

# -----------------------------
# Reset user DB
# -----------------------------
def reset_user_db(packaged_db_path: Path):
    user_db = get_user_db_path()
    if user_db.exists():
        user_db.unlink()
        print(f"🗑  Old user DB removed: {user_db}")
    shutil.copy(packaged_db_path, user_db)
    print(f"✅ User DB reset from Packaged DB: {user_db}")
    return user_db

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    packaged_db = create_packaged_db()
    reset_user_db(packaged_db)