# pipeline/webconfig.py
import cherrypy
import html
import json
import uuid
import time
import threading
import urllib.parse 

from pipeline.web_utils import launch_browser, get_self_closing_html
# --- Shared State Management ---

# Global store for results awaiting retrieval by the calling Python function.
# Key: request_id (str), Value: submitted_value (str)
PROMPT_RESULTS = {}
results_lock = threading.Lock() 

# --- Server Control State ---
_SERVER_THREAD = None
_SERVER_LOCK = threading.Lock() 

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
            'server.thread_pool': 5, 
            'log.screen': False, # Suppress logs during background operation
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
    """Stops the CherryPy server."""
    global _SERVER_THREAD
    
    with _SERVER_LOCK:
        if _SERVER_THREAD is not None and _SERVER_THREAD.is_alive():
            print("\n[WEBPROMPT] Shutting down configuration web server...")
            # Stop all running engine components
            cherrypy.engine.stop()
            # Ensure a clean exit of the engine process
            cherrypy.engine.exit()
            _SERVER_THREAD = None

# --- Web Service Class ---

class WebPromptService(object):
    """Manages the web interface for single-value prompts and stores results."""

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
        button {{
            width: 100%;
            padding: 12px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        button:hover {{ background-color: #2563eb; }}
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

        <p class="prompt-info">
            Please provide the required value for: <code>{html.escape(prompt_key)}</code>
        </p>

        <form method="post" action="/submit_prompt">
            <input type="hidden" name="request_id" value="{html.escape(request_id)}">
            
            <div class="form-group">
                <label for="value">{html.escape(prompt_message)}</label>
                <input type="{input_type}" id="value" name="value" placeholder="{visibility_hint}" required autofocus>
            </div>
            
            <button type="submit">Submit Value</button>
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
            delay_seconds=1.5 # Example: 1.5 seconds delay
        )

        # Defunct, Render a simple confirmation page
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Submission Complete</title>
    <style>
        body {{ background-color: #1f2937; color: #f3f4f6; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .message-box {{ background-color: #10b981; color: #1f2937; padding: 40px; border-radius: 12px; text-align: center; box-shadow: 0 0 25px rgba(0, 0, 0, 0.4); }}
        h2 {{ margin-top: 0; font-size: 1.5em; }}
        p {{ font-size: 1.1em; }}
    </style>
</head>
<body>
    <div class="message-box">
        <h2>Success!</h2>
        <p>The value has been saved and returned to your application.</p>
        <p>You may now close this browser tab.</p>
    </div>
</body>
</html>
"""

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

    while True:
        try:
            if not browser_launched:

                # Use the robust internal launcher
                print(f"Automatically launching URL in browser...")
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

def browser_get_input(key: str, prompt_message: str, hide_input: bool = False) -> str:
    """
    Retrieves a config value by launching a web prompt. Starts the server if needed.
    """
    # CRITICAL: Start the server before attempting to communicate with it
    start_server_if_needed() 
    
    request_id = str(uuid.uuid4())
    # Note: we pass the clean 'key' here
    value = _wait_for_web_input(request_id, key, prompt_message, hide_input)
    
    return value
