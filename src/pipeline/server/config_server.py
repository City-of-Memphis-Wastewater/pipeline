# src/pipeline/server/config_server.py
'''
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, validator
from pathlib import Path
import uvicorn # Used for launching the server
import socket
from importlib import resources
from importlib.resources import files

import urllib.parse
from typing import Dict, Any
import threading
import time

from pipeline.security_and_config import CredentialsNotFoundError
from pipeline.state_manager import PromptManager # Import the new class
from pipeline.server.web_utils import find_open_port
# --- State Initialization ---
prompt_manager = PromptManager()

# --- Configuration ---
# Define the root directory for serving static files
# Assumes this script is run from the project root or the path is correctly resolved
#STATIC_DIR = Path(__file__).parent.parent / "interface" / "web_gui"
STATIC_DIR = files("pipeline.interface.web_gui.static")
TEMPLATE_DIR = files("pipeline.interface.web_gui.templates")

# Initialize FastAPI app
app = FastAPI(title="Config and Credential Modal Input Server", version="1.0.0") # should this have its own server?
# Attach the manager instance to the app state for easy access via dependency injection
app.state.prompt_manager = prompt_manager

def get_prompt_manager() -> PromptManager:
    """Dependency injector for the PromptManager."""
    return app.state.prompt_manager

# --- Pydantic Schema for Request Body ---
class ConfigModular(BaseModel):
    pass

# --- 4. Configuration Input Endpoints ---

# --- New Endpoint: Serves the Config Modal HTML ---
@app.get("/config_modal", response_class=HTMLResponse)
async def serve_config_modal_html(request_id: str):
    """
    Serves the HTML page for the configuration modal/iframe, including the request ID.
    
    The HTML will contain JavaScript that polls for the prompt data associated with the ID.
    """
    try:
        # 1. Read the HTML file content
        # Adjust the path to where your config_modal.html is located
        # Assuming config_modal.html is directly under pipeline/interface/web_gui
        html_content = resources.read_text(
            'pipeline.interface.web_gui.templates', # Assuming this is the module path
            'config_modal.html'
        )
        
        # 2. Inject the request_id into the HTML for the JavaScript/form to use
        # This is a common pattern to pass server-side variables to the client
        # We will replace a placeholder like {{ request_id }}
        
        # Note: We should URL-escape the request_id just in case, though UUIDs are usually safe
        escaped_id = urllib.parse.quote_plus(request_id)
        
        # Assuming the HTML file has a placeholder like '{{ request_id }}'
        # If not, you'll need to update config_modal.html to include one.
        final_html = html_content.replace('{{ request_id }}', escaped_id)
        
        # 3. Return the HTML
        return HTMLResponse(content=final_html)

    except FileNotFoundError:
        # Handle case where the HTML file is missing
        raise HTTPException(
            status_code=500, 
            detail="Config modal HTML file not found."
        )
    except Exception as e:
        # General error handling
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while serving the config modal: {e}"
        )
    
@app.get("/api/get_active_prompt", response_class=JSONResponse)
async def get_active_prompt(manager: PromptManager = Depends(get_prompt_manager)):
    """Returns the one and only prompt request waiting for input."""
    data = manager.get_active_prompt()
    if data:
        data["show"] = True
        return JSONResponse(data)
    return JSONResponse({"show": False})
    
@app.post("/api/submit_config", response_class=HTMLResponse)
async def submit_config(request: Request, manager: PromptManager = Depends(get_prompt_manager)):
    """
    Receives the submitted form data from the auto-launched config modal and unblocks the waiting Python thread.
    """
    try:
        # FastAPI's Request.form() handles standard form submissions
        form_data = await request.form()
        request_id = form_data.get("request_id")
        submitted_value = form_data.get("input_value")
        
        if not request_id or submitted_value is None:
            raise HTTPException(status_code=400, detail="Missing request_id or input_value")

        # 1. Store the result using the manager method
        manager.submit_result(request_id, submitted_value)    
        
        # 2. Return the self-closing HTML (using the existing utility)
     
        return HTMLResponse(f"<h1>Configuration submitted successfully!</h1>", status_code=200)
        
    except Exception as e:
        return HTMLResponse(f"<h1>Error during submission: {e}</h1>", status_code=500)
    
def run_config_server_in_thread(host: str = "127.0.0.1", port: int = 8083) -> threading.Thread:
    """Launches the Config server in a daemon thread."""
    
    # 1. Use an available port (important, as 8082 is already taken by the Trend server)
    port = find_open_port(port, port + 50)
    host_port_str = f"{host}:{port}"
    full_url = f"http://{host_port_str}"
    
    # 2. Update the prompt manager with the Config Server's URL
    # Assuming prompt_manager is globally accessible or imported correctly here
    prompt_manager.set_server_host_port(host_port_str) 

    print(f"--- Config Server starting at {full_url} ---")
    # Uvicorn's Server must be explicitly created to run in a thread
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config=config)
    
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    
    time.sleep(0.5) # Give the thread time to bind the port
    return server_thread
'''

from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import msgspec.json # New import for fast JSON serialization
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import HTMLResponse, Response, JSONResponse # Using Response for msgspec
from starlette.exceptions import HTTPException
from starlette.requests import Request # Explicitly import Request

from pathlib import Path
import uvicorn # Used for launching the server
import socket
from importlib import resources
from importlib.resources import files

import urllib.parse
from typing import Dict, Any
import threading
import time

from pipeline.security_and_config import CredentialsNotFoundError
from pipeline.state_manager import PromptManager
from pipeline.server.web_utils import find_open_port

# --- State Initialization ---
prompt_manager = PromptManager()

# --- Configuration ---
STATIC_DIR = files("pipeline.interface.web_gui.static")
TEMPLATE_DIR = files("pipeline.interface.web_gui.templates")

# Initialize Starlette app
# The title and version previously in FastAPI are not necessary in Starlette's core
app = Starlette(debug=True)
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
        html_content = resources.read_text(
            'pipeline.interface.web_gui.templates',
            'config_modal.html'
        )
        
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