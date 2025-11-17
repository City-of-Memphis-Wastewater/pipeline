# pipeline/server/web_utils.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import webbrowser
import shutil
import subprocess
import time
import socket
import uvicorn # Used for launching the server
from pathlib import Path
import requests
import threading
from typing import Any,  Tuple

from pipeline.cli import GLOBAL_SHUTDOWN_EVENT
# --- Configuration ---
# Define the root directory for serving static files
# Assumes this script is run from the project root or the path is correctly resolved
STATIC_DIR = Path(__file__).parent.parent / "interface" / "web_gui"

# --- Browser Launch Logic ---

def launch_browser(url: str):
    """
    Attempts to launch the URL using specific platform commands first, 
    then falls back to the standard Python webbrowser, ensuring a new tab is opened.
    Includes a delay for stability.

    Uses subprocess.Popen to launch the browser in the background
    without blocking the main Python script.
    """
    
    launched = False
    
    # 1. Try Termux-specific launcher
    if shutil.which("termux-open-url"):
        try:
            print("[WEBPROMPT] Attempting launch using 'termux-open-url'...")
            # Run the command without capturing output to keep it clean
            subprocess.Popen(
                ["termux-open-url", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            launched = True
            return
        # CATCH 1: Specific Error if termux-open-url binary is not found (unlikely if shutil.which passed, but good practice)
        except FileNotFoundError:
            pass # shutil.which should prevent this, so we silently fall through
        # CATCH 2: General failure during execution (e.g., system error, bad URL format)
        except Exception as e:
            print(f"[WEBPROMPT WARNING] 'termux-open-url' failed: {e}. Falling back...")
        
    # 2. Try the explicit WSLg Microsoft Edge executable
    if shutil.which("microsoft-edge"):
        try:
            print("[WEBPROMPT] Attempting launch using 'microsoft-edge' (WSLg)...")
            # Use Popen for non-blocking execution
            # Pass the URL as the first argument to open it in a new tab/window
            subprocess.Popen(
                ["microsoft-edge", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            launched = True
            return
        except FileNotFoundError:
            pass # shutil.which should prevent this, so we silently fall through
        except Exception as e: 
            print(f"[WEBPROMPT WARNING] Direct 'microsoft-edge' launch failed: {e}. Falling back...")
            pass

    # 3. Try general Linux desktop launcher
    if shutil.which("xdg-open"):
        try:
            print("[WEBPROMPT] Attempting launch using 'xdg-open'...")
            subprocess.Popen(
                ["xdg-open", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            launched = True
            return
        except FileNotFoundError:
            pass # shutil.which should prevent this, so we silently fall through
        except Exception as e:
            print(f"[WEBPROMPT WARNING] 'xdg-open' failed: {e}. Falling back...")

    # 4. Fallback to standard Python library, for most environments.
    try:
        print("[WEBPROMPT] Attempting launch using standard Python 'webbrowser' module...")
        webbrowser.open_new_tab(url)
        launched = True
    except FileNotFoundError:
            pass # shutil.which should prevent this, so we silently fall through
    except Exception as e:
        print(f"[WEBPROMPT ERROR] Standard 'webbrowser' failed: {e}. Please manually open the URL.")

    # Add a brief delay after a successful launch for OS stability
    if launched:
        time.sleep(0.5)

def find_open_port(start_port: int = 8082, max_port: int = 8100) -> int:
    """
    Finds an available TCP port starting from `start_port` up to `max_port`.
    Returns the first available port.
    """
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                s.close()
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port found between {start_port} and {max_port}.")

# --- 1. Serve Static Files ---

def launch_server_for_web_gui(app, host: str = "127.0.0.1", port: int = 8082):
    """Launches the server using uvicorn."""

    try:
        port = find_open_port(port, port + 50)
    except RuntimeError as e:
        raise RuntimeError(f"Failed to start server: {e}")
    
    url = f"http://{host}:{port}"
    print(f"Starting Generalized Web Server at {url}")
    
    # --- TEMPORARY THREAD TO LAUNCH BROWSER ---
    # Since uvicorn.run is blocking, we must launch the browser in a new thread
    # and use polling to wait for the server to be ready.
    def launch_browser_when_ready(target_url):
        MAX_WAIT_SECONDS = 5
        POLL_INTERVAL_SECONDS = 0.2
        server_ready = False
        
        for i in range(int(MAX_WAIT_SECONDS / POLL_INTERVAL_SECONDS)):
            if is_server_running(target_url):
                server_ready = True
                break
            time.sleep(POLL_INTERVAL_SECONDS)
        
        try:
            if server_ready:
                print("[WEBPROMPT] Server confirmed responsive. Launching browser.")
                launch_browser(target_url)
            else:
                print(f"[WEBPROMPT WARNING] Server not responsive after {MAX_WAIT_SECONDS}s. Please manually open the URL: {target_url}")
        except Exception:
            print("Could not launch browser automatically. Open the URL manually.")
            
    # Start the non-blocking browser launcher immediately
    threading.Thread(target=launch_browser_when_ready, args=(url,), daemon=True).start()
    # ------------------------------------------

    # Start the server (runs until interrupted) - THIS IS THE BLOCKING CALL
    uvicorn.run(app, host=host, port=port)

def launch_server_for_web_gui_(app: Any, host: str = "127.0.0.1", port: int = 8082) -> Tuple[uvicorn.Server, threading.Thread]:
    """
    Launches the Uvicorn server in a background thread and returns the server 
    object and thread for manual lifecycle management.
    """
    
    try:
        # Note: 'app' must be passed as the application import path or object
        port = find_open_port(port, port + 50)
    except RuntimeError as e:
        print(f"Error finding open port: {e}")
        # Use a dummy tuple to indicate failure, or raise
        raise RuntimeError(f"Failed to start server: {e}")
        
    
    # 1. Instantiate Configuration
    # We explicitly set the `loop` and `http` to 'asyncio' and 'h11' for reliability
    # The `workers=1` ensures it runs in the same thread environment we control
    config = uvicorn.Config(
        app, 
        host=host, 
        port=port, 
        log_level="info", 
        loop="asyncio", 
        http="h11",
        workers=1 # Must be 1 when running manually in a separate thread
    )

    print(f"Starting Generalized Web Server at {url}")
    
    # 2. Instantiate Server
    server = uvicorn.Server(config=config)
    
    # 3. Launch Server in a Thread
    # We use server.run() as the target for the thread.
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    
    # 4. Launch Browser (After starting the thread)
    
    host_port_str = f"{host}:{port}"
    url = f"http://{host_port_str}"
    MAX_WAIT_SECONDS = 5
    POLL_INTERVAL_SECONDS = 0.2
    
    # --- Server Polling Logic (Replaces time.sleep(1)) ---
    server_ready = False
    for i in range(int(MAX_WAIT_SECONDS / POLL_INTERVAL_SECONDS)):
        if is_server_running(url):
            server_ready = True
            break
        time.sleep(POLL_INTERVAL_SECONDS)
    # --- End Polling Logic ---

    try:
        if server_ready:
            print("[WEBPROMPT] Server confirmed responsive. Launching browser.")
            launch_browser(url)
        else:
            print(f"[WEBPROMPT WARNING] Server did not become responsive after {MAX_WAIT_SECONDS}s. Please manually open the URL: {url}")
            
    except Exception:
        print("Could not launch browser automatically. Open the URL manually.")
        
    # Return the control objects
    return server, server_thread

# --- Helper to check server status ---
def is_server_running(url: str) -> bool:
    """Check if the server at the given URL is responsive."""
    try:
        # A lightweight HEAD request to the base URL
        requests.head(url, timeout=1.0)
        return True
    except requests.exceptions.RequestException:
        return False
