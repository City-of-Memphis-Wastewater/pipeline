from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import sys
import importlib.resources as pkg_resources
from pathlib import Path
from importlib.resources import files

STATIC_DIR = files("pipeline_eds.interface.web_gui.static")
TEMPLATE_DIR = files("pipeline_eds.interface.web_gui.templates")

# IMPORTANT: This must match the name of the directory/package where the 
# HTML file is placed when building the PEX.
# Since we include the current directory ('.') in the PEX build, the
# resource is accessible relative to the root namespace.
RESOURCE_PACKAGE = 'pex_app' 
RESOURCE_FILENAME = 'dashboard.html'

def get_html_content() -> bytes:
    """
    Loads the dashboard.html file from inside the PEX archive using 
    importlib.resources. This is the byte-serving core.
    """
    # Use the newer, path-based access method for robustness
    try:
        # 1. Get the path handle (Traversable) to the package root inside PEX
        package_root = pkg_resources.files(RESOURCE_PACKAGE)
        
        # 2. Join the filename and read the content as raw bytes
        html_bytes = package_root.joinpath(RESOURCE_FILENAME).read_bytes()
        
        print(f"✅ Resource '{RESOURCE_FILENAME}' loaded successfully from PEX archive.")
        print(f"   Content Length: {len(html_bytes) / 1024:.2f} KB")
        return html_bytes
        
    except FileNotFoundError:
        print(f"❌ ERROR: Resource file not found in PEX.", file=sys.stderr)
        return b"<h1>Error: Resource not found.</h1>"
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        return b"<h1>Error: Internal PEX execution failure.</h1>"

def main():
    """
    The main execution function called by the PEX executable.
    """
    print("--- PEX Application Started ---")
    
    html_bytes = get_html_content()
    
    # In a real application, a web framework (Flask/FastAPI) would now
    # take 'html_bytes' and return it as the HTTP response body.
    
    # We simulate this by printing the start of the content:
    print("\n--- Simulated HTTP Response ---")
    print(html_bytes[:100].decode('utf-8').strip() + "...")
    print("-----------------------------\n")

    # The single HTML file ensures all front-end dependencies (CSS/JS) are met.

if __name__ == "__main__":
    # If run directly outside of PEX (for debugging)
    main()