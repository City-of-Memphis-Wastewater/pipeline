# src/pipeline/server/trend_server_eds.py

from __future__ import annotations # Delays annotation evaluation
import msgspec.json # New import for fast JSON serialization
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import HTMLResponse, Response, JSONResponse # Using Response for msgspec
from starlette.exceptions import HTTPException
from starlette.requests import Request # Explicitly import Request
#import msgspec.struct # Import for creating data structures
# FIX: Use 'from msgspec import Struct' instead of 'import msgspec.struct'
from msgspec import Struct 

from pathlib import Path
from typer import BadParameter
import uvicorn # Used for launching the server
from importlib import resources
from typing import Dict, Any, List, Optional
#from importlib.resources import files
from importlib.resources import read_text

# Local imports
from pipeline.core import eds as eds_core 
from pipeline.interface.utils import save_history, load_history
from pipeline.security_and_config import CredentialsNotFoundError
from pipeline.server.web_utils import launch_server_for_web_gui_

# Initialize Starlette app
app = Starlette(debug=True)

# --- Msgspec Struct for Request Body (Replaces Pydantic BaseModel) ---
# NOTE: msgspec structs are much stricter than Pydantic. We rely on the client
# to send a correctly structured JSON payload (e.g., idcs must be a list of strings).
# The complex @validator logic from Pydantic is removed for simplicity and speed.
class TrendRequest(Struct, tag=True):
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
    # ←←← REPLACE EVERYTHING FROM HERE DOWN TO THE END OF THE FUNCTION ←←←

    except requests.exceptions.ConnectTimeout:
        error_msg = "Connection to the EDS API timed out. Please check your VPN connection and try again."
        print(f"[EDS TREND SERVER] {error_msg}")
        raise HTTPException(status_code=503, detail=error_msg)

    except BadParameter as e:
        raise HTTPException(status_code=400, detail=f"Input Error: {str(e).strip()}")

    except CredentialsNotFoundError as e:
        print(f"SECURITY ERROR: {e}")
        raise HTTPException(status_code=400, detail=f"Configuration Required: {str(e)}")

    except Exception as e:
        error_msg = f"Unexpected error fetching trend data: {str(e)}"
        print(f"[EDS TREND SERVER] {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)
        
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
    launch_server_for_web_gui_(app, port=8082)
    config = uvicorn.Config(
        # The entry point is the factory function, not the app object itself
        app=app, 
        host="127.0.0.1",
        port=8000,
        log_level="info",
        # Use the single server process
        workers=1 
    )
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    launch_server_for_web_gui_eds_trend_specific()
