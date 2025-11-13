# src/pipeline/server/config_server.py

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, validator
from pathlib import Path
import uvicorn # Used for launching the server
import socket
from importlib import resources
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
STATIC_DIR = Path(__file__).parent.parent / "interface" / "web_gui"

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
    
    # 2. Update the prompt manager with the Config Server's URL
    # Assuming prompt_manager is globally accessible or imported correctly here
    prompt_manager.set_server_port(host_port_str) 

    print(f"--- Config Server starting at http://{host_port_str} ---")
    
    # Uvicorn's Server must be explicitly created to run in a thread
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config=config)
    
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    
    time.sleep(0.5) # Give the thread time to bind the port
    return server_thread