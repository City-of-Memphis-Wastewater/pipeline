# src/pipeline/server/config_server.py

from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import msgspec.json # New import for fast JSON serialization
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import HTMLResponse, Response, JSONResponse # Using Response for msgspec
from starlette.exceptions import HTTPException
from starlette.requests import Request # Explicitly import Request
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from pathlib import Path
import uvicorn # Used for launching the server
import socket
from importlib import resources
from importlib.resources import files
from importlib.resources import read_text
from starlette.responses import HTMLResponse
from starlette.requests import Request
import urllib.parse
from typing import Dict, Any
import threading
import time

from pipeline.security_and_config import CredentialsNotFoundError
from pipeline.state_manager import PromptManager
from pipeline.server.web_utils import find_open_port

# Define the middleware list
# for iframe embeddings: HTML iframe from one port can be embedded into a site on a different port.
middleware = [
    Middleware(
        CORSMiddleware,
        # Allow origins from any port on localhost, or be specific: 
        # allow_origins=["http://127.0.0.1:8082"] 
        # Using '*' is simplest for local development:
        allow_origins=["*"], 
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
]

# --- State Initialization ---
prompt_manager = PromptManager()

# Initialize Starlette app
# The title and version previously in FastAPI are not necessary in Starlette's core
app = Starlette(debug=True, middleware=middleware)
# Attach the manager instance to the app state for easy access via request
app.state.prompt_manager = prompt_manager

# --- 4. Configuration Input Endpoints ---

async def serve_config_modal_html(request: Request):
    """
    Handles GET /config_modal.
    Serves the HTML page for the configuration modal/iframe, including the request ID.
    """
    # In Starlette, query parameters are accessed via request.query_params
    request_id = request.query_params.get("request_id")
    if not request_id:
        raise HTTPException(status_code=400, detail="Missing required query parameter: request_id")
        
    try:
        # 1. Read the HTML file content
        html_content = resources.read_text('pipeline.interface.web_gui.templates', 'config_modal.html')
        
        # 2. Inject the request_id into the HTML
        escaped_id = urllib.parse.quote_plus(request_id)
        final_html = html_content.replace('{{ request_id }}', escaped_id)
        
        # 3. Return the HTML
        return HTMLResponse(content=final_html, status_code=200)

    except FileNotFoundError:
        raise HTTPException(
            status_code=500, 
            detail="Config modal HTML file not found."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while serving the config modal: {e}"
        )
    
async def get_active_prompt(request: Request):
    """
    Handles GET /api/get_active_prompt.
    Returns the one and only prompt request waiting for input.
    """
    manager: PromptManager = request.app.state.prompt_manager
    data = manager.get_active_prompt()
    
    if data:
        data["show"] = True
        # Use msgspec for fast serialization
        content = msgspec.json.encode(data)
        # Return a standard Starlette Response with the application/json media type
        return Response(content=content, media_type="application/json", status_code=200)

    empty_data = {"show": False}
    content = msgspec.json.encode(empty_data)
    return Response(content=content, media_type="application/json", status_code=200)
    
async def submit_config(request: Request):
    """
    Handles POST /api/submit_config.
    Receives the submitted form data and unblocks the waiting Python thread.
    """
    manager: PromptManager = request.app.state.prompt_manager
    
    try:
        # Starlette's Request.form() is asynchronous and handles form submissions
        form_data = await request.form()
        request_id = form_data.get("request_id")
        submitted_value = form_data.get("input_value")
        
        if not request_id or submitted_value is None:
            # Raise Starlette's HTTPException
            raise HTTPException(status_code=400, detail="Missing request_id or input_value")

        # 1. Store the result
        manager.submit_result(request_id, submitted_value)    
        
        # 2. Return success HTML
        return HTMLResponse("<h1>Configuration submitted successfully!</h1>", status_code=200)
        
    except HTTPException as http_exc:
        # Re-raise explicit HTTP errors
        raise http_exc
    except Exception as e:
        # General error handling
        print(f"Error during submission: {e}")
        return HTMLResponse(f"<h1>Error during submission: {e}</h1>", status_code=500)
        
# --- Routing Definition (Replaces FastAPI decorators) ---

routes = [
    Route("/config_modal", endpoint=serve_config_modal_html, methods=["GET"]),
    Route("/api/get_active_prompt", endpoint=get_active_prompt, methods=["GET"]),
    Route("/api/submit_config", endpoint=submit_config, methods=["POST"]),
]

app.routes.extend(routes) # Add routes to the Starlette application

# --- Server Run Function ---
    
def run_config_server_in_thread(host: str = "127.0.0.1", port: int = 8083) -> threading.Thread:
    """Launches the Config server in a daemon thread."""
    
    # 1. Use an available port
    port = find_open_port(port, port + 50)
    host_port_str = f"{host}:{port}"
    full_url = f"http://{host_port_str}"
    
    # 2. Update the prompt manager with the Config Server's URL
    prompt_manager.set_server_host_port(host_port_str) 

    print(f"--- Config Server starting at {full_url} ---")
    # Uvicorn config must use the Starlette app
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config=config)
    
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    
    time.sleep(0.5) 
    return server_thread
