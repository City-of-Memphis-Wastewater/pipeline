# pipeline/config_via_web.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import time
import urllib.parse 

from typing import Any

from pipeline.server.web_utils import launch_browser, is_server_running
from pipeline.server.config_server import get_prompt_manager, run_config_server_in_thread # Import the getter

# Import the launch function (Assuming you can import it or pass it)
# Assuming 'launch_server_for_web_gui' is available in the module that imports config_via_web
# For this example, let's assume you pass the launch function to the manager if needed.


def browser_get_input(manager: Any, key: str, prompt_message: str, hide_input: bool) -> str | None:
    """
    Launches a modal/page on the MAIN FastAPI server and polls for the result.
    This function now BLOCKS the calling thread (SecurityAndConfig).
    """
    # 1. Register the prompt request
    try:
        request_id = manager.register_prompt(key, prompt_message, hide_input)
    except RuntimeError as e:
        # typer not imported in config_via_web, use print/log
        print(f"⚠️ Error: {e}") 
        return None 
    
    CONFIG_SERVER_URL = manager.get_server_url()
    
    # 1. Server Status Check
    server_is_active = is_server_running(CONFIG_SERVER_URL)
    
    # If the server isn't running, we must launch a temporary instance.
    # We will launch the main server in a separate thread, which is complex and often messy.
    # The clean solution is to have a dedicated *minimal* server for this.
    # For now, let's assume the manager's server_url is set by the main server.

    # 2. If the main server is not running, we must tell the user to start it or
    #    handle the launch *here*.
    # Since `launch_server_for_web_gui` blocks, we must run it in a separate thread.
    
    server_thread = None
    if not is_server_running(CONFIG_SERVER_URL)
        print(f"--- Server not running. Launching temporary config server. ---")
        server_thread = run_config_server_in_thread(port=8083)

        # Launch browser to the CONFIG MODAL page (not the main Trend page)
        # We need a dedicated URL for the config modal, e.g., /config_modal/{request_id}
        # For now, let's keep launching the main UI, assuming it polls the new CONFIG server.
        
        # Launch browser to the MAIN UI to trigger polling
        # Note: We need the MAIN Trend UI's URL, which the manager *does not know* directly.
        # For simplicity, let's launch the CONFIG MODAL dedicated page for now:
        CONFIG_MODAL_URL = f"http://{CONFIG_SERVER_URL}/config_modal?id={request_id}" 
        launch_browser(CONFIG_MODAL_URL) # <-- This launches the second tab
    else:
        # Server is running, we just need to ensure the client is polling.
        # If the client isn't polling, we should launch the config modal page
        CONFIG_MODAL_URL = f"http://{CONFIG_SERVER_URL}/config_modal?id={request_id}"
        launch_browser(CONFIG_MODAL_URL)
        print(f"--- Config Server is active. Launched browser to dedicated modal page... ---")
        

    # 4. Poll for the result (Blocking)
    try:
        while True:
        
            value = manager.get_and_clear_result(request_id)
            if value is not None:
                print("--- Input Received from Main UI! ---")
                return value
            time.sleep(0.5)
    except KeyboardInterrupt: # <--- CATCH KEYBOARD INTERRUPT HERE!
        # Clean up the registered prompt before exiting
        manager.clear_result(request_id)
        print("\nPolling cancelled by user. Returning None.")
        # Optional: You might need to stop the server_thread gracefully here if it was started
        return None
    except Exception as e: 
        # Handle server connection loss gracefully during poll
        print(f"\nPolling error: {e}")
        return None