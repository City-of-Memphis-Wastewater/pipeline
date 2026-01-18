# src/pipeline/server/server_manager.py 

from __future__ import annotations
import threading
import signal
import sys
from typing import List, Tuple
import uvicorn
from typing import Any

class ServerManager:
    """
    Manages the lifecycle (start/stop) of all background Uvicorn servers.
    This replaces manual thread/server tracking in the main loop.
    """
    def __init__(self):
        # Stores tuples of (uvicorn.Server, threading.Thread)
        self.active_servers: List[Tuple[uvicorn.Server, threading.Thread]] = []
        self.shutdown_event = threading.Event()

    def register_server(self, server: uvicorn.Server, thread: threading.Thread):
        """Adds a newly launched server to the management list."""
        self.active_servers.append((server, thread))

    def run_main_loop(self):
        """
        Starts the central event loop, waits for a shutdown signal, 
        and initiates the graceful shutdown of all registered servers.
        """
        # 1. Register signal handler for Ctrl+C
        #signal.signal(signal.SIGINT, self._signal_handler)
        
        print("\n[INFO] Server Manager started. Press Ctrl+C to shut down.")

        # 2. Main Blocking Loop (waits for the shutdown event to be set)
        while not self.shutdown_event.is_set():
            self.shutdown_event.wait(0.5)

        # 3. Shutdown initiated (event was set by signal handler)
        self._graceful_shutdown()
        
    def _signal_handler(self, sig, frame):
        """Sets the shutdown event when a SIGINT is received."""
        # Note: This is executed in the main thread when Ctrl+C is pressed.
        print("\n[SHUTDOWN] Keyboard Interrupt received. Starting graceful server shutdown...")
        self.shutdown_event.set()

    def _graceful_shutdown(self):
        """Tells all servers to stop and waits for their threads to exit."""
        print("[SHUTDOWN] Shutting down all active Uvicorn servers...")
        
        # 1. Instruct all servers to stop listening
        for server, _ in self.active_servers:
            # Set this flag so Uvicorn exits gracefully after its next tick
            server.should_exit = True

        # 2. Wait for all threads to join (clean exit)
        # Timeout prevents main thread from waiting forever if a thread hangs
        for _, thread in self.active_servers:
            if thread.is_alive():
                print(f"[SHUTDOWN] Waiting for thread {thread.name} to finish...")
                thread.join(timeout=5)
                
        print("[SHUTDOWN] All server threads closed. Application exiting.")
        sys.exit(0)
