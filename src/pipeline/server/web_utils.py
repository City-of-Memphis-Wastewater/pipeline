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
            subprocess.Popen(["termux-open-url", url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            launched = True
            return
        except subprocess.CalledProcessError as e:
            print(f"[WEBPROMPT WARNING] 'termux-open-url' failed: {e}. Falling back...")
        except FileNotFoundError:
             pass
        
    # 2. Try the explicit WSLg Microsoft Edge executable
    if shutil.which("microsoft-edge"):
        try:
            print("[WEBPROMPT] Attempting launch using 'microsoft-edge' (WSLg)...")
            # Use Popen for non-blocking execution
            # Pass the URL as the first argument to open it in a new tab/window
            subprocess.Popen(["microsoft-edge", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            launched = True
            return
        except Exception as e:
            print(f"[WEBPROMPT WARNING] Direct 'microsoft-edge' launch failed: {e}. Falling back...")
            pass

    # 3. Try general Linux desktop launcher
    if shutil.which("xdg-open"):
        try:
            print("[WEBPROMPT] Attempting launch using 'xdg-open'...")
            subprocess.Popen(["xdg-open", url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            launched = True
            return
        except subprocess.CalledProcessError as e:
            print(f"[WEBPROMPT WARNING] 'xdg-open' failed: {e}. Falling back...")
        except FileNotFoundError:
             pass
             
    # 4. Fallback to standard Python library, for most environments.
    try:
        print("[WEBPROMPT] Attempting launch using standard Python 'webbrowser' module...")
        webbrowser.open_new_tab(url)
        launched = True
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
    """Launches the FastAPI server using uvicorn."""

    try:
        port = find_open_port(port, port + 50)
    except RuntimeError as e:
        print(e)
        return
    
    host_port_str = f"{host}:{port}" # e.g., "127.0.0.1:8082"
    url = f"http://{host_port_str}"

    print(f"Starting Generalized Web Server at {url}")
    
    try:
        launch_browser(url)
        #pass
    except Exception:
        print("Could not launch browser automatically. Open the URL manually.")
        
    # Start the server (runs until interrupted)
    uvicorn.run(app, host=host, port=port)


# --- Helper to check server status ---
def is_server_running(url: str) -> bool:
    """Check if the server at the given URL is responsive."""
    try:
        # A lightweight HEAD request to the base URL
        requests.head(url, timeout=1.0)
        return True
    except requests.exceptions.RequestException:
        return False
