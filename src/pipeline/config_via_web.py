# pipeline/config_via_web.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import threading
import urllib.parse 
from typing import Any

from pipeline.server.web_utils import launch_browser, is_server_running
from pipeline.server.config_server import get_prompt_manager, run_config_server_in_thread # Import the getter
from pipeline.cli import GLOBAL_SHUTDOWN_EVENT
# Import the launch function (Assuming you can import it or pass it)
# Assuming 'launch_server_for_web_gui' is available in the module that imports config_via_web
# For this example, let's assume you pass the launch function to the manager if needed.


def browser_get_input(manager: Any, key: str, prompt_message: str, hide_input: bool) -> str | None:
    """
    Launches a modal/page on the MAIN FastAPI server and polls for the result.
    This function now BLOCKS the calling thread (SecurityAndConfig).
    """
    global GLOBAL_SHUTDOWN_EVENT

    # 1. Register the prompt request
    try:
        request_id = manager.register_prompt(key, prompt_message, hide_input)
    except RuntimeError as e:
        # typer not imported in config_via_web, use print/log
        print(f"⚠️ Error: {e}") 
        return None 
    
    CONFIG_SERVER_URL_CHECK = manager.get_server_url()
    
    # 1. Server Status Check
    server_thread = None
    if not is_server_running(CONFIG_SERVER_URL_CHECK):
        print(f"--- Server not running. Launching temporary config server. ---")
        server_thread = run_config_server_in_thread(port=8083)

       # Now the manager has the correct URL (e.g., http://127.0.0.1:8083)
        CONFIG_SERVER_URL = manager.get_server_url()
    else:
        # Server is running, we just need to ensure the client is polling.
        # If the client isn't polling, we should launch the config modal page
        CONFIG_SERVER_URL = CONFIG_SERVER_URL_CHECK
        print(f"--- Config Server is active. Using existing server at {CONFIG_SERVER_URL} ---")

    # URL-encode the variables you want to pass
    encoded_message = urllib.parse.quote_plus(prompt_message)
    encoded_hide_input = str(hide_input) # "True" or "False" string
    #CONFIG_MODAL_URL = f"{CONFIG_SERVER_URL}/config_modal?request_id={request_id}"
    # Construct the full URL, including the new parameters
    CONFIG_MODAL_URL = (
        f"{CONFIG_SERVER_URL}/config_modal?"
        f"request_id={request_id}&"
        f"message={encoded_message}&"
        f"hide_input={encoded_hide_input}"
    )
    launch_browser(CONFIG_MODAL_URL)
    print(f"--- Config Server is active. Launched browser to dedicated modal page... ---")
    # 4. Poll for the result (Blocking)
    try:
        while True:
            # 1. Check if the main process wants to shut down
            if GLOBAL_SHUTDOWN_EVENT.is_set():
                print("\nPolling loop detected shutdown signal. Exiting gracefully.")
                # Clean up the registered prompt before exiting
                manager.clear_result(request_id)
                return None # Exit the function
            value = manager.get_and_clear_result(request_id)
            if value is not None:
                print("--- Input Received from Main UI! ---")
                return value
            #time.sleep(0.5)
            # Use a threading Event to make the sleep interruptible by signals
            threading.Event().wait(0.5)
    except KeyboardInterrupt: # 
        print("KeyboardInterrupt")
        # Clean up the registered prompt before exiting
        print("CALL manager.clear_result(request_id)")
        manager.clear_result(request_id)
        print("\nPolling cancelled by user. Returning None.")
        # Optional: You might need to stop the server_thread gracefully here if it was started
        return None
    except Exception as e: 
        # Handle server connection loss gracefully during poll
        print(f"\nPolling error: {e}")
        return None