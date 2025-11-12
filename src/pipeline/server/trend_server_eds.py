# src/pipeline/server/trend_server_eds.py

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator
from pathlib import Path
from typer import BadParameter
import uvicorn # Used for launching the server
import socket
from importlib import resources
import urllib.parse
from typing import Dict, Any

# Local imports
from pipeline.core import eds as eds_core 
from pipeline.interface.utils import save_history, load_history
from pipeline.web_utils import get_self_closing_html
from pipeline.security_and_config import CredentialsNotFoundError
from pipeline.state_manager import PromptManager # Import the new class

# --- State Initialization ---
prompt_manager = PromptManager()

# --- Configuration ---
# Define the root directory for serving static files
# Assumes this script is run from the project root or the path is correctly resolved
STATIC_DIR = Path(__file__).parent.parent / "interface" / "web_gui"

# Initialize FastAPI app
app = FastAPI(title="EDS Trend Server", version="1.0.0")
# Attach the manager instance to the app state for easy access via dependency injection
app.state.prompt_manager = prompt_manager

def get_prompt_manager() -> PromptManager:
    """Dependency injector for the PromptManager."""
    return app.state.prompt_manager

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


# --- Pydantic Schema for Request Body ---
class TrendRequest(BaseModel):
    # Match the data structure from your Alpine.js payload
    idcs: list[str]
    default_idcs: bool = False
    days: float | None = None
    starttime: str | None = None
    endtime: str | None = None
    seconds_between_points: int | None = None
    datapoint_count: int | None = None
    force_webplot: bool = True
    force_matplotlib: bool = False
    
    # Custom validator to clean IDCS input (Alpine already does some, but good to double-check)
    @validator('idcs', pre=True)
    def normalize_idcs(cls, v):
        if isinstance(v, str):
            # Handle comma/space separation if the frontend sends it as a single string
            return [i.strip() for i in v.split() if i.strip()]
        return v
    
# --- 1. Serve Static Files ---

# Mount the static directory for CSS/JS/images
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_gui():
    """
    Serves the main index.html file by loading it as a package resource.
    The path must be the package path relative to the project root.
    Assuming the file is in 'pipeline.interface.web_gui'.
    """
    try:
        # Load the content of index.html as a resource
        # Replace 'pipeline.interface.web_gui' with the actual Python package path 
        # where the web_gui folder resides inside the installed/bundled package.
        index_content = resources.read_text('pipeline.interface.web_gui', 'index.html')
        return HTMLResponse(index_content)
    
    except FileNotFoundError:
        # Handle the case where the resource wasn't bundled or the path is wrong
        return HTMLResponse(
            "<html><body><h1>Error 500: index.html resource not found.</h1>"
            "<h2>Check resource bundling configuration.</h2></body></html>", 
            status_code=500
        )
    except Exception as e:
        # Catch unexpected errors during resource loading
        return HTMLResponse(f"<html><body><h1>Resource Load Error: {e}</h1></body></html>", status_code=500)
    
    
# --- 2. API Endpoint for Core Logic ---

@app.post("/api/fetch_trend")
async def fetch_trend(request_data: TrendRequest):
    """Fetches trend data and triggers plotting based on request parameters."""
    
    # Clean up IDCS list for the core logic
    idcs_list = request_data.idcs
    if not idcs_list and request_data.default_idcs:
        # Fallback to history not implemented here; rely strictly on current input or default flag
        pass 
        
    # --- Execute Core Logic ---
    try:
        # 1. Save history immediately if valid input was provided (before core logic potentially fails)
        if idcs_list:
            # Reconstruct the space-separated string for history saving
            save_history(" ".join(idcs_list)) 
            
        data_buffer, _ = eds_core.fetch_trend_data(
            idcs=idcs_list, 
            starttime=request_data.starttime, 
            endtime=request_data.endtime, 
            days=request_data.days, 
            plant_name=None, 
            seconds_between_points=request_data.seconds_between_points, 
            datapoint_count=request_data.datapoint_count,
            default_idcs=request_data.default_idcs
        )
        
        # 2. Check for empty data
        if data_buffer.is_empty():
            return JSONResponse({"no_data": True, "message": "No data returned."})
        
        # 3. Plotting
        # Note: In a pure web model, plotting should ideally return plot data (e.g., Plotly JSON) 
        # to the frontend, which then renders it. For now, we rely on the core function's 
        # existing behavior (e.g., opening a new browser tab for Plotly).
        
        eds_core.plot_trend_data(
            data_buffer, 
            request_data.force_webplot, 
            request_data.force_matplotlib
        )
        
        return JSONResponse({"success": True, "message": "Data fetched and plot initiated."})

    except BadParameter as e:
        # Catch errors from core logic and return a structured JSON error
        raise HTTPException(status_code=400, detail={"error": f"Input Error: {str(e).strip()}"})
    
    except CredentialsNotFoundError as e: # <-- ✅ NEW CATCH BLOCK
        # Catch CLI-centric config errors and convert them to HTTP 400/500
        # HTTP 400 is often appropriate for missing required input/config.
        print(f"SECURITY ERROR: {e}") # Log the specific failure on the server
        raise HTTPException(status_code=400, detail={"error": f"Configuration Required: {str(e)}"})
    
    except Exception as e:
        # Catch unexpected errors (like VPN/network issues)
        raise HTTPException(status_code=500, detail={"error": f"Server Error (VPN/Core Issue): {str(e)}"})

# --- 3. API Endpoint for History ---

@app.get("/api/history")
async def get_history():
    """Returns the list of saved IDCS queries."""
    history = load_history()
    return JSONResponse(history)

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
     
        return HTMLResponse(get_self_closing_html("Configuration submitted successfully!"))
        
    except Exception as e:
        return HTMLResponse(f"<h1>Error during submission: {e}</h1>", status_code=500)
        
# --- Launch Command ---

def launch_server_for_web_gui(host: str = "127.0.0.1", port: int = 8082):
    """Launches the FastAPI server using uvicorn."""

    try:
        port = find_open_port(port, port + 50)
    except RuntimeError as e:
        print(e)
        return
    
    host_port_str = f"{host}:{port}" # e.g., "127.0.0.1:8082"
    url = f"http://{host_port_str}"

    # Use the Manager instance to set the port, eliminating the global SERVER_HOST_PORT
    prompt_manager.set_server_port(host_port_str)

    print(f"Starting EDS Trend Web Server at {url}")
    
    try:
        #launch_browser(url)
        pass
    except Exception:
        print("Could not launch browser automatically. Open the URL manually.")
        
    # Start the server (runs until interrupted)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    launch_server_for_web_gui()