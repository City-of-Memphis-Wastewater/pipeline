# pipeline/webconfig.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
#import cherrypy
import atexit
import html
import json
import uuid
import time
import threading
import urllib.parse 

from typing import Any

from pipeline.web_utils import launch_browser, get_self_closing_html
# --- Shared State Management ---

"""
# Import shared state from the main server module
try:
    from pipeline.server.trend_server_eds import PROMPT_RESULTS, results_lock, SERVER_HOST_PORT
except ImportError:
    # Fallback for testing/running outside full environment
    PROMPT_RESULTS = {}
    results_lock = threading.Lock()
    SERVER_HOST_PORT = "127.0.0.1:8082" # Fallback needs the actual running default

# --- Server Control State ---
_SERVER_THREAD = None
_SERVER_LOCK = threading.Lock() 
"""

def browser_get_input(manager: Any, key: str, prompt_message: str, hide_input: bool) -> str | None:
    """
    Launches a modal/page on the MAIN FastAPI server and polls for the result.
    This function now BLOCKS the calling thread (SecurityAndConfig).
    """
    # 1. Register the prompt request
    try:
        request_id = manager.register_prompt(key, prompt_message, hide_input)
    except RuntimeError as e:
        typer.echo(f"⚠️ Error: {e}")
        return None # Return None if a prompt is already active
    
    # 1. Build the URL to tell the main server to show the modal
    # NOTE: You MUST use the MAIN FastAPI app's URL/Port (e.g., 8083), not 8081
    # You will need to determine how to get the main server's URL/Port here.
    # For this example, let's assume the main app's URL is passed in or known.
    
    # 2. Get the URL from the manager
    MAIN_SERVER_URL = manager.get_server_url()

    encoded_key = urllib.parse.quote(key)
    encoded_message = urllib.parse.quote(prompt_message)
    
    prompt_url = f"{MAIN_SERVER_URL}/config_modal?request_id={request_id}&key={encoded_key}&message={encoded_message}&is_credential={hide_input}"
    
    print(f"--- Prompt Required on Main UI ---")
    print(f"URL: {prompt_url}")
    
    # 2. Launch the browser to the main UI's config modal
    #launch_browser(prompt_url)
    
    # 3. Poll for the result (This is the blocking part)
    # NO launch_browser() call here! The frontend polling handles the modal display.

    print(f"--- Prompt ID {request_id} stored. Waiting for frontend input... ---")
    
    # 3. Poll for the result (Blocking)
    while True:
        value = manager.get_and_clear_result(request_id)
        if value is not None:
            print("--- Input Received from Main UI! ---")
            return value

        time.sleep(0.5)

# --- Context Manager for Server Lifecycle ---
class WebConfigurationManager:
    """A context manager to ensure the web server starts once and stops once."""
    def __enter__(self):
        """Called when entering the 'with' block."""
        print("\n--- Starting Web Configuration Session ---")
        start_server_if_needed()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called when exiting the 'with' block."""
        stop_server()
        print("--- Web Configuration Session Ended ---")


def start_server_if_needed():
    """Starts the CherryPy server in a background thread if it is not already running."""
    global _SERVER_THREAD
    
    with _SERVER_LOCK:
        if _SERVER_THREAD is not None and _SERVER_THREAD.is_alive():
            # Server is already running
            return

        # 1. Define the application configuration
        cherrypy.config.update({
            'server.socket_host': '127.0.0.1',
            'server.socket_port': 8081,
            #'server.thread_pool': 5, 
            'log.screen': True, # Suppress logs during background operation
            'engine.autoreload_on': False, 
        })
        
        # 2. Mount the application tree
        config = {
            '/': { 'tools.sessions.on': True }
        }
        cherrypy.tree.mount(WebPromptService(), '/', config=config)

        # 3. Define and start the thread
        print("\n[WEBPROMPT] Starting configuration web server in background thread...")
        # Start the engine components (HTTP server, etc.)
        _SERVER_THREAD = threading.Thread(target=cherrypy.engine.start, daemon=True)
        _SERVER_THREAD.start()
        # Wait briefly for the server to spin up
        time.sleep(0.5)
        print(f"[WEBPROMPT] Server listening on http://127.0.0.1:8081/")


def stop_server():
    """Stops the CherryPy server and waits for the thread to terminate."""
    global _SERVER_THREAD
    
    with _SERVER_LOCK:
        if _SERVER_THREAD is not None and _SERVER_THREAD.is_alive():
            print("\n[WEBPROMPT] Shutting down configuration web server...")
            # Stop all running engine components
            cherrypy.engine.stop()
            
            # Block and wait for the server thread to fully exit.
            # A timeout is good practice to prevent an indefinite hang.
            _SERVER_THREAD.join(timeout=5.0) 
            
            # Now that the thread is joined, we can be sure the engine has stopped.
            _SERVER_THREAD = None
            print("[WEBPROMPT] Server has shut down cleanly.")
        # Always call exit, even if thread wasn’t alive
        cherrypy.engine.exit()

@atexit.register
def shutdown_webprompt():
    # Ensure CherryPy is still running before trying to shut it down
    #if cherrypy.engine.state == cherrypy.engine.states.STARTED:
    #    print("Shutting down CherryPy gracefully...")
    #    cherrypy.engine.exit()

    if cherrypy.engine.state not in (
        cherrypy.engine.states.STOPPED,
        cherrypy.engine.states.EXITING
        ):
        print("Shutting down CherryPy gracefully...")
        cherrypy.engine.exit()

# --- Web Service Class ---
class WebPromptService(object):
    """Manages the web interface for single-value prompts and stores results."""
    @cherrypy.expose
    def index(self):
        """
        Handles the benign GET request from the self-closing success page,
        preventing a 404 error in the logs.
        """
        # Return a simple 200 OK with a minimal message.
        # This response is not typically seen by the user.
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return "Server is active. Awaiting shutdown signal."

    def _render_prompt_page(self, request_id, prompt_key, prompt_message, input_type='text', status_message=None):
        """Renders the minimal page for prompting a single configuration value."""
        
        visibility_hint = "Type a value" if input_type != 'password' else "Hidden input for security"
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Configuration Prompt: {prompt_key}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #1f2937; 
            --card-bg: #374151;
            --text-color: #f3f4f6;
            --primary-color: #3b82f6;
            --border-color: #4b5563;
            --success-color: #10b981;
            --danger-color: #ef4444;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .card {{
            background-color: var(--card-bg);
            padding: 32px;
            border-radius: 12px;
            box-shadow: 0 0 25px rgba(0, 0, 0, 0.4);
            width: 100%;
            max-width: 450px;
        }}
        h1 {{
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 8px;
            text-align: center;
        }}
        .prompt-info {{
            font-size: 1.1rem;
            margin-bottom: 30px;
            text-align: center;
            color: #9ca3af;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 6px;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        input[type="text"], input[type="password"] {{
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background-color: var(--bg-color);
            color: var(--text-color);
            box-sizing: border-box;
            font-size: 1em;
        }}
        input[type="text"]:focus, input[type="password"]:focus {{
            border-color: var(--primary-color);
            outline: none;
        }}
        .button-group {{
            display: flex;
            justify-content: flex-end; /* Align buttons to the right */
            gap: 10px;
            margin-top: 25px; 
        }}
        .button-group button {{
            padding: 12px 20px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s;
            color: white;
            width: auto;
        }}
        .submit-btn {{
            background-color: var(--primary-color);
            flex-grow: 1; 
        }}
        .submit-btn:hover {{ background-color: #2563eb; }}
        .cancel-btn {{
            background-color: var(--danger-color);
        }}
        .cancel-btn:hover {{ background-color: #b91c1c; }}
        .message {{
            background-color: var(--success-color);
            color: #1f2937;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-weight: 600;
            text-align: center;
        }}
        
    </style>
</head>
<body>
    <div class="card">
        <h1>External Input Required</h1>
        
        {f'<div class="message">{status_message}</div>' if status_message else ''}

        <!--p class="prompt-info">
            Please provide the required value for: <code>{html.escape(prompt_key)}</code>
        </p-->

        <form method="post" action="/submit_prompt">
            <input type="hidden" name="request_id" value="{html.escape(request_id)}">
            
            <div class="form-group">
                <label for="value">{html.escape(prompt_message)}</label>
                <input type="{input_type}" id="value" name="value" placeholder="{visibility_hint}" required autofocus>
            </div>

            <div class="button-group">
                <button type="submit" 
                        class="cancel-btn"
                        name="action" 
                        value="cancel" 
                        formaction="/cancel_prompt"
                        formnovalidate>
                    Cancel
                </button>
                <button type="submit" class="submit-btn">
                    Submit Value
                </button>
            </div>
            
        </form>
        
    </div>
</body>
</html>
"""

    @cherrypy.expose
    def start_prompt(self, request_id, key, message, is_credential='False'):
        """
        Endpoint called by the Python utility function to initiate the web interface.
        """
        input_type = 'password' if is_credential == 'True' else 'text'
        return self._render_prompt_page(
            request_id=request_id,
            prompt_key=key, # The clean, internal key
            prompt_message=message, # The verbose, user-friendly message
            input_type=input_type
        )

    @cherrypy.expose
    def submit_prompt(self, request_id, value):
        """
        Endpoint called by the user's browser (form POST) to submit the value.
        """
        with results_lock:
            PROMPT_RESULTS[request_id] = value
        
        return get_self_closing_html(
            message="Configuration input successfully received by the application.",
            delay_seconds=1.0 # Example: 1.0 seconds delay
        )

    # Assuming a basic Python web framework (like Flask or similar)

    @cherrypy.expose
    def cancel_prompt(self, request_id, **kwargs):
        """
        Endpoint called when the user clicks the 'Cancel' button.
        It sets the result to None to signal explicit cancellation.
        **kwargs is used to absorb any extra parameters like 'action'.
        """
        with results_lock:
            # Setting the result to None explicitly signals the waiting pipeline 
            # to stop waiting and process the cancellation.
            PROMPT_RESULTS[request_id] = None
        
        return get_self_closing_html(
            message="Input cancelled by user. Returning 'None' to the application.",
            delay_seconds=0.5 # Close quickly after cancellation
        )
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def check_result(self, request_id):
        """Endpoint called by the *polling Python function* to check if the result is ready."""
        # NOTE: This endpoint is used by the client's internal polling logic (which
        # runs in the same process) to retrieve the result.
        with results_lock:
            if request_id in PROMPT_RESULTS:
                value = PROMPT_RESULTS.pop(request_id)
                return {'status': 'READY', 'value': value}
            else:
                return {'status': 'PENDING', 'value': None}

# --- Python Utility Functions (The "Pythonic" Wrappers) ---

def _wait_for_web_input(request_id, key, prompt_message: str, hide_input: bool) -> str:
    """Blocks execution and polls the web service until the user submits a value."""
    server_port = cherrypy.config.get('server.socket_port', 8081)
    
    is_credential = 'True' if hide_input else 'False'
    
    # CRITICAL: Use urllib.parse.quote to safely encode both the key and the message
    encoded_message = urllib.parse.quote(prompt_message)
    encoded_key = urllib.parse.quote(key)

    prompt_url = (
        f"http://127.0.0.1:{server_port}/start_prompt?"
        f"request_id={request_id}&key={encoded_key}&message={encoded_message}&is_credential={is_credential}"
    )

    print(f"\n--- Awaiting Web Input for '{key}' ---")
    print(f"Automatically launching URL in browser...")
    print(f"URL: {prompt_url}") 
    print("---------------------------------------")

    poll_count = 0 
    browser_launched = False
    # Launch the browser once, before the polling loop starts
    try:
        launch_browser(prompt_url)
        browser_launched = True
    except Exception as e:
        print(f"[WEBPROMPT ERROR] Failed to launch browser: {e}")

    while True:
        try:
            if not browser_launched:

                # Use the robust internal launcher
                launch_browser(prompt_url)
                time.sleep(0.5)
                browser_launched = True

            # Direct dictionary check (relies on shared memory in the same process)
            with results_lock:
                if request_id in PROMPT_RESULTS:
                    result = {'status': 'READY', 'value': PROMPT_RESULTS.pop(request_id)}
                else:
                    result = {'status': 'PENDING', 'value': None}

            if result['status'] == 'READY':
                print(f"--- Input Received! ---")
                return result['value']
            
            time.sleep(1) 
            poll_count += 1
            
            if poll_count % 5 == 0:
                print(f"[POLLING] Waiting for web submission for '{key}'...")

        except Exception as e:
            print(f"[WEBPROMPT ERROR] Polling loop exception: {e}")
            time.sleep(5)



def browser_get_input_defunct(key: str, prompt_message: str, hide_input: bool = False) -> str:
    """
    Retrieves a config value by launching a web prompt.
    NOTE: This function now ASSUMES the server is already running via the
    WebConfigurationManager context manager
    """
    # CRITICAL: The start_server and stop_server calls are REMOVED from here and are inferred in 'with WebConfigurationManager()'.
    request_id = str(uuid.uuid4())
    value = _wait_for_web_input(request_id, key, prompt_message, hide_input)
    # The server is no longer stopped here.
    return value