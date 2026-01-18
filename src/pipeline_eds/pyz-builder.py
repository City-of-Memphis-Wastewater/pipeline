from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import sys
import importlib.resources as pkg_resources
from pathlib import Path
from typing import Optional

# --- Simulation of Package Structure ---
# For this code to work in a PEX/pyz, imagine you have a directory structure like:
#
# my_pyz_app/
# ├── __init__.py
# ├── resource_loader.py (This file)
# └── dashboard.html (The file to be served)
#
# You would reference the package name 'my_pyz_app' below.
# For demonstration purposes in a single script, we'll use a placeholder package name
# and assume the HTML file is adjacent (which works for simple `python -m my_pyz_app`).

# Define the package that contains the resource and the resource filename
RESOURCE_PACKAGE = 'resource_loader' # In a real app, this would be your app's package name 
RESOURCE_FILENAME = 'dashboard.html'

def get_html_resource_bytes(package_name: str, filename: str) -> Optional[bytes]:
    """
    Reads the content of the specified file from within the Python package
    as raw bytes, suitable for byte-serving over HTTP.
    
    This method works reliably whether the code is run from a standard
    installation, an egg, or a PEX/pyz archive.
    """
    try:
        # Use importlib.resources.files for the modern, Path-based access.
        # This returns a Traversable object (which acts like a Path).
        resource_path = pkg_resources.files(package_name)

        # Join the filename and read the content as bytes
        # .read_bytes() is the most robust way to get binary data for serving.
        html_bytes = resource_path.joinpath(filename).read_bytes()
        
        print(f"✅ Successfully loaded resource '{filename}' from package '{package_name}'.")
        print(f"   Resource size: {len(html_bytes) / 1024:.2f} KB")
        return html_bytes
        
    except FileNotFoundError:
        print(f"❌ Error: The resource file '{filename}' was not found inside the package '{package_name}'.", file=sys.stderr)
        print("   Ensure the HTML file is included in your source package.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred during resource loading: {e}", file=sys.stderr)
        return None

def serve_dashboard():
    """
    Simulates the core action of a web framework (like Flask or FastAPI)
    which would take the raw bytes and serve them in an HTTP response.
    """
    
    # 1. Get the raw HTML bytes using importlib.resources
    html_content_bytes = get_html_resource_bytes(RESOURCE_PACKAGE, RESOURCE_FILENAME)
    
    if not html_content_bytes:
        # If the bytes couldn't be loaded, return a server error message.
        return b"Error: Resource not found."
    
    # 2. In a real web server:
    #    a. You would set the HTTP Content-Type header to 'text/html; charset=utf-8'
    #    b. You would return the html_content_bytes as the response body.
    
    print("\n--- Simulation of HTTP Response Payload (First 200 bytes) ---")
    print(html_content_bytes[:200].decode('utf-8').strip() + "...")
    print("----------------------------------------------------------\n")
    
    # Example of a final response structure (if using a WSGI/ASGI application):
    # response = {
    #     'status': '200 OK',
    #     'headers': [('Content-Type', 'text/html; charset=utf-8')],
    #     'body': html_content_bytes
    # }
    
    return html_content_bytes

if __name__ == "__main__":
    # NOTE: For this simple example to work directly, ensure dashboard.html is
    # in the same directory as this script and run it as a package if possible:
    # > python -m resource_loader
    
    # Since we are running this script directly (not as an installed package),
    # we temporarily adjust the path so that importlib.resources can find the
    # files relative to the script's execution context.
    
    # In a real PEX, this path manipulation is NOT necessary!
    # PEX handles finding the resources inside the archive automatically.
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Run the serving simulation
    serve_dashboard()
    
    sys.path.pop(0)