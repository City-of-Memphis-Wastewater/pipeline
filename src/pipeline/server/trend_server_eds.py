# src/pipeline/server/trend_server_eds.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator
from pathlib import Path
from typer import BadParameter
import uvicorn # Used for launching the server

# Import core business logic and history functions
# Assuming pipeline.core.eds is available
from pipeline.core import eds as eds_core
from pipeline.interface.gui_eds import load_history, save_history 
from pipeline.web_utils import launch_browser

# --- Configuration ---
# Define the root directory for serving static files
# Assumes this script is run from the project root or the path is correctly resolved
STATIC_DIR = Path(__file__).parent.parent / "interface" / "web_gui"

# Initialize FastAPI app
app = FastAPI(title="EDS Trend Server", version="1.0.0")

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
    """Serves the main index.html file."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        return HTMLResponse("<html><body><h1>Error: index.html not found.</h1></body></html>", status_code=500)
    
    with open(index_path, 'r') as f:
        return f.read()

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
    
    except Exception as e:
        # Catch unexpected errors (like VPN/network issues)
        raise HTTPException(status_code=500, detail={"error": f"Server Error (VPN/Core Issue): {str(e)}"})

# --- 3. API Endpoint for History ---

@app.get("/api/history")
async def get_history():
    """Returns the list of saved IDCS queries."""
    history = load_history()
    return JSONResponse(history)

# --- Launch Command ---

def launch_server_for_web_gui(host: str = "127.0.0.1", port: int = 8082):
    """Launches the FastAPI server using uvicorn."""
    print(f"Starting EDS Trend Web Server at http://{host}:{port}")
    # Launch browser automatically
    try:
        launch_browser(f"http://{host}:{port}")
    except Exception:
        print("Could not launch browser automatically. Open the URL manually.")
        
    # Start the server (runs until interrupted)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    launch_server_for_web_gui()