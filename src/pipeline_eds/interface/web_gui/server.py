# src/pipeline_eds/interface/web_gui/server.py
"""
Implemented on 19 Novermber 2025 as a way to dig out of multi server complexity.
See
"""
from starlette.applications import Starlette
from starlette.routing import WebSocketRoute, Route
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse, HTMLResponse
import os

# --- Placeholder Handlers (replace with your actual logic) ---
async def homepage(request):
    # This will serve your main SvelteKit/Alpine.js index.html file
    return HTMLResponse("<html><body><h1>Pipeline Dashboard</h1></body></html>")

async def input_api(request):
    # This replaces one of your "pop-up" servers.
    # It handles input validation (using msgspec) and returns a result.
    return JSONResponse({"status": "ready", "fields": ["tag", "start_time"]})

async def plotting_ws(websocket):
    # This replaces your "plotting window" server.
    await websocket.accept()
    # Logic to stream plot data or status updates
    await websocket.send_json({"plot_status": "generating"})
    await websocket.close()

# --- Application Configuration ---
# Determine the base directory for static and template files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")


routes = [
    Route("/", endpoint=homepage),
    Route("/api/input", endpoint=input_api, methods=["GET", "POST"]),
    WebSocketRoute("/ws/plotting", endpoint=plotting_ws),
]

# Create the main Starlette app
app = Starlette(
    routes=routes,
    debug=True, # Set to False in production
)

# Mount static files (CSS, JS, images)
# The `include` section in your pyproject.toml already includes this directory.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Expose the application factory function for Uvicorn
def get_app():
    return app