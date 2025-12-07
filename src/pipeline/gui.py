# pipeline/gui.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import threading

from pipeline.interface import gui_eds

GLOBAL_SHUTDOWN_EVENT = threading.Event()

def handle_interrupt(sig, frame):
    """Signal handler for SIGINT (Ctrl+C)."""
    print("Main process received CTRL+C. Setting shutdown flag...")
    GLOBAL_SHUTDOWN_EVENT.set()
    # You may also want to propagate the signal to stop Uvicorn
    # If Uvicorn is in a separate thread/process, this handles the main script.

# Set the signal handler right after starting your server
import signal
#signal.signal(signal.SIGINT, handle_interrupt)


gui_eds.main()
