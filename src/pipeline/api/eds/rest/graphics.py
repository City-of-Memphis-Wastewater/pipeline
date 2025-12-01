from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import logging
import os

from pipeline.decorators import log_function_call
from pipeline.api.eds.rest.demo import demo_eds_start_session_CoM_WWTPs

logger = logging.getLogger(__name__)


"""
Graphics-specific EDS functions copied manually by Clayton on 1 December 2025 from eds.py.
"""
@log_function_call(level=logging.DEBUG)
def demo_eds_save_graphics_export():
    # Start sessions for your WWTPs
    workspace_manager, sessions = demo_eds_start_session_CoM_WWTPs()
    session_maxson = sessions["Maxson"]

    # Get list of graphics from the EDS session
    graphics_list = get_graphics_list(session_maxson, session_maxson.base_url)
    print(f"Found {len(graphics_list)} graphics to export.")

    # Loop through each graphic and save it
    for graphic in graphics_list:
        graphic_name = graphic.get("name", os.path.splitext(graphic["file"])[0])
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in graphic_name)
        output_file_path = workspace_manager.get_exports_file_path(filename=f"{safe_name}.png")

        # Fetch and save the graphic
        graphic_bytes = get_graphic_export(session_maxson, session_maxson.base_url, graphic["file"])
        save_graphic_export(graphic_bytes, output_file_path)

        print(f"Saved graphic: {graphic_name} → {output_file_path}")

    print("All graphics exported successfully.")


def get_graphics_list(session, api_url):
    """Return list of graphics from EDS session."""
    resp = session.get(f"{api_url}/graphics")  # api_url passed in
    resp.raise_for_status()
    return resp.json()

def get_graphic_export(session, api_url, graphic_file):
    """Fetch a graphic as PNG bytes."""
    resp = session.get(f"{api_url}/graphics/{graphic_file}/export", params={"format": "png"})
    resp.raise_for_status()
    return resp.content

def save_graphic_export(graphic_bytes, output_file_path):
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    with open(output_file_path, "wb") as f:
        f.write(graphic_bytes)
