# src/api/status_api.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import msgspec.json
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response, JSONResponse
from starlette.exceptions import HTTPException
from pipeline_eds.daemon.status import get_latest_status

# Note: get_latest_status() is assumed to return a serializable Python object
# (e.g., dict, list, or a msgspec.Struct instance).

async def status_endpoint(request):
    """
    Handles the /status GET request, fetching the status and serializing
    it to JSON using msgspec for maximum performance.
    
    We wrap the status logic in a try/except block to ensure proper error 
    handling and response formatting if the status fetch fails.
    """
    try:
        # 1. Fetch the data from the pipeline logic
        status_data = get_latest_status()
        
        # 2. Encode the status data to JSON bytes using msgspec.
        # This is generally faster than Starlette's default JSONResponse 
        # (which uses the standard library's json.dumps).
        content = msgspec.json.encode(status_data)
        
        # 3. Return a Starlette Response object with the JSON content type
        return Response(
            content=content, 
            media_type="application/json",
            status_code=200
        )
        
    except Exception as e:
        # Handle exceptions during status retrieval
        # In a real app, you'd log the full traceback.
        print(f"Error retrieving status: {e}")
        # Use Starlette's built-in JSONResponse for simple error messages
        return JSONResponse(
            {"detail": "Internal Server Error during status retrieval"},
            status_code=500
        )


# Define the routing table for the application
routes = [
    Route("/status", endpoint=status_endpoint, methods=["GET"])
]

# Initialize the Starlette application
# Set debug=True for development to see tracebacks easily.
app = Starlette(
    routes=routes,
    debug=True 
)

# Example usage with uvicorn:
# uvicorn src.api.status_api:app --reload