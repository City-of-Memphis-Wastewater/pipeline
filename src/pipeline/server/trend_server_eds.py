# src/pipeline/server/trend_server_eds.py
'''
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, validator
from pathlib import Path
from typer import BadParameter
import uvicorn # Used for launching the server
from importlib import resources
from typing import Dict, Any
from importlib.resources import files


# Local imports
from pipeline.core import eds as eds_core 
from pipeline.interface.utils import save_history, load_history
from pipeline.security_and_config import CredentialsNotFoundError
from pipeline.server.web_utils import launch_server_for_web_gui

STATIC_DIR = files("pipeline.interface.web_gui.static")
TEMPLATE_DIR = files("pipeline.interface.web_gui.templates")
# Initialize FastAPI app
app = FastAPI(title="EDS Trend Server", version="1.0.0") # this does not reflect the entire app - just one html for one of the CLI commands converted into a webpage
# Attach the manager instance to the app state for easy access via dependency injection
# app.state.prompt_manager = prompt_manager # possibly not related at this point - maybe two servers need to talk to each other? I don't know anything about servers.

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


@app.get("/", response_class=HTMLResponse) # not a good endpoint if not index.html
async def serve_gui(): # generalized or specific?
    """
    Serves the eds_trend.html file by loading it as a package resource.
    The path must be the package path relative to the project root.
    """
    try:
        # Load the content of eds _trend.html as a resource
        index_content = resources.read_text('pipeline.interface.web_gui.templates', 'eds_trend.html')
        return HTMLResponse(index_content)
    
    except FileNotFoundError:
        # Handle the case where the resource wasn't bundled or the path is wrong
        return HTMLResponse(
            "<html><body><h1>Error 500: eds_trend.html resource not found.</h1>"
            "<h2>Check resource bundling configuration.</h2></body></html>", 
            status_code=500
        )
    except Exception as e:
        # Catch unexpected errors during resource loading
        return HTMLResponse(f"<html><body><h1>Resource Load Error: {e}</h1></body></html>", status_code=500)
    
    
# --- 2. API Endpoint for Core Logic ---

@app.post("/api/fetch_eds_trend") # good specific url and function name - there will be other trends.
async def fetch_eds_trend(request_data: TrendRequest): #
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

@app.get("/api/history") # url possibly too general, though all history could be loaded and then the relevanrt key pulled
async def get_history():
    """Returns the list of saved IDCS queries."""
    history = load_history()
    return JSONResponse(history)

# --- Launch Command ---
def launch_server_for_web_gui_eds_trend_specific():
    print(f"Calling for specific EDS Trend HTML to be served")
    launch_server_for_web_gui(app, port=8082)


if __name__ == "__main__":
    launch_server_for_web_gui_eds_trend_specific()

'''

from __future__ import annotations # Delays annotation evaluation
import msgspec.json # New import for fast JSON serialization
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import HTMLResponse, Response, JSONResponse # Using Response for msgspec
from starlette.exceptions import HTTPException
from starlette.requests import Request # Explicitly import Request
import msgspec.struct # Import for creating data structures

from pathlib import Path
from typer import BadParameter
import uvicorn # Used for launching the server
from importlib import resources
from typing import Dict, Any, List, Optional
from importlib.resources import files

# Local imports
from pipeline.core import eds as eds_core 
from pipeline.interface.utils import save_history, load_history
from pipeline.security_and_config import CredentialsNotFoundError
from pipeline.server.web_utils import launch_server_for_web_gui

STATIC_DIR = files("pipeline.interface.web_gui.static")
TEMPLATE_DIR = files("pipeline.interface.web_gui.templates")

# Initialize Starlette app
app = Starlette(debug=True)

# --- Msgspec Struct for Request Body (Replaces Pydantic BaseModel) ---
# NOTE: msgspec structs are much stricter than Pydantic. We rely on the client
# to send a correctly structured JSON payload (e.g., idcs must be a list of strings).
# The complex @validator logic from Pydantic is removed for simplicity and speed.
class TrendRequest(msgspec.Struct, tag=True):
    idcs: List[str]
    default_idcs: bool = False
    days: Optional[float] = None
    starttime: Optional[str] = None
    endtime: Optional[str] = None
    seconds_between_points: Optional[int] = None
    datapoint_count: Optional[int] = None
    force_webplot: bool = True
    force_matplotlib: bool = False

# --- 1. Endpoint to Serve the HTML GUI ---

async def serve_gui(request: Request):
    """
    Handles GET /.
    Serves the eds_trend.html file by loading it as a package resource.
    """
    try:
        # Load the content of eds_trend.html as a resource
        index_content = resources.read_text('pipeline.interface.web_gui.templates', 'eds_trend.html')
        return HTMLResponse(index_content)
    
    except FileNotFoundError:
        return HTMLResponse(
            "<html><body><h1>Error 500: eds_trend.html resource not found.</h1>"
            "<h2>Check resource bundling configuration.</h2></body></html>", 
            status_code=500
        )
    except Exception as e:
        return HTMLResponse(f"<html><body><h1>Resource Load Error: {e}</h1></body></html>", status_code=500)
    
    
# --- 2. API Endpoint for Core Logic ---

async def fetch_eds_trend(request: Request):
    """
    Handles POST /api/fetch_eds_trend.
    Fetches trend data and triggers plotting based on request parameters.
    """
    try:
        # 1. Decode the JSON request body using msgspec
        body = await request.body()
        request_data: TrendRequest = msgspec.json.decode(body, type=TrendRequest)
        
    except msgspec.DecodeError as e:
        # Catch JSON decoding errors (malformed JSON or invalid types)
        raise HTTPException(status_code=400, detail={"error": f"Invalid request body format or types: {e}"})
    except Exception as e:
        # Catch general body reading errors
        raise HTTPException(status_code=400, detail={"error": f"Failed to read request body: {e}"})

    # --- Core Logic Execution ---
    idcs_list = request_data.idcs
        
    try:
        # 1. Save history immediately if valid input was provided
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
            response_data = {"no_data": True, "message": "No data returned."}
            return Response(
                content=msgspec.json.encode(response_data),
                media_type="application/json",
                status_code=200
            )
        
        # 3. Plotting
        eds_core.plot_trend_data(
            data_buffer, 
            request_data.force_webplot, 
            request_data.force_matplotlib
        )
        
        response_data = {"success": True, "message": "Data fetched and plot initiated."}
        return Response(
            content=msgspec.json.encode(response_data),
            media_type="application/json",
            status_code=200
        )

    except BadParameter as e:
        # Catch errors from core logic and raise Starlette's HTTPException
        raise HTTPException(status_code=400, detail={"error": f"Input Error: {str(e).strip()}"})
    
    except CredentialsNotFoundError as e:
        # Catch config errors and convert them to HTTP 400
        print(f"SECURITY ERROR: {e}") 
        raise HTTPException(status_code=400, detail={"error": f"Configuration Required: {str(e)}"})
    
    except Exception as e:
        # Catch unexpected errors
        raise HTTPException(status_code=500, detail={"error": f"Server Error (VPN/Core Issue): {str(e)}"})

# --- 3. API Endpoint for History ---

async def get_history(request: Request):
    """
    Handles GET /api/history.
    Returns the list of saved IDCS queries.
    """
    history = load_history()
    
    # Use msgspec for fast serialization
    content = msgspec.json.encode(history)
    
    return Response(
        content=content,
        media_type="application/json",
        status_code=200
    )


# --- Routing Definition (Replaces FastAPI decorators) ---

routes = [
    Route("/", endpoint=serve_gui, methods=["GET"]),
    Route("/api/fetch_eds_trend", endpoint=fetch_eds_trend, methods=["POST"]),
    Route("/api/history", endpoint=get_history, methods=["GET"]),
]

app.routes.extend(routes) # Add routes to the Starlette application

# --- Launch Command ---
def launch_server_for_web_gui_eds_trend_specific():
    print(f"Calling for specific EDS Trend HTML to be served")
    # This utility function must still be defined elsewhere to run uvicorn
    launch_server_for_web_gui(app, port=8082)


if __name__ == "__main__":
    launch_server_for_web_gui_eds_trend_specific()