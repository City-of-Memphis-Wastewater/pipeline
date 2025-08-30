import os
import requests
#from pyeds2 import EdsClient

# --- CONFIG ---
EDS_HOST = "http://172.19.4.127:43084"  # REST API host
USERNAME = "admin"
PASSWORD = ""
OUTPUT_DIR = r"C:\Users\george.bennett\dev\pipeline\workspaces\eds_graphics\exports"
os.makedirs(OUTPUT_DIR, exist_ok=True)
"""
# --- INIT CLIENT ---
session = requests.Session()
session.auth = (USERNAME, PASSWORD)

# --- FETCH ALL DIAGRAMS ---
response = session.get(f"{EDS_HOST}/api/graphics")
if response.status_code == 200:
    graphics_list = response.json()
    print(f"Found {len(graphics_list)} graphics.")

    for graphic in graphics_list:
        graphic_id = graphic["id"]
        graphic_name = graphic.get("name", f"graphic_{graphic_id}")
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in graphic_name)
        output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.png")

        try:
            # Fetch the PNG bytes
            png_response = session.get(f"{EDS_HOST}/api/graphics/{graphic_id}/render", params={"format": "png", "width": 1920, "height": 1080})
            if png_response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(png_response.content)
                print(f"Saved {graphic_name} → {output_path}")
            else:
                print(f"Failed to fetch PNG for {graphic_name}: {png_response.status_code}")
        except Exception as e:
            print(f"Error exporting {graphic_name}: {e}")
else:
    print(f"Failed to fetch graphics list: {response.status_code}")

print("Done exporting all graphics.")"""

SOURCE = "EDS"  # source system name in your environment

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- LOGIN TO WEB API ---
session = requests.Session()
login_resp = session.post(
    f"{EDS_HOST}/api/v1/login",
    json={"username": USERNAME, "password": PASSWORD},
)
login_resp.raise_for_status()

# --- LIST ALL GRAPHICS FILES ---
resp = session.get(f"{EDS_HOST}/api/v1/graphics")  # adjust endpoint if needed
resp.raise_for_status()
graphics_list = resp.json()
print(f"Found {len(graphics_list)} graphics.")

# --- LOOP THROUGH GRAPHICS ---
for graphic in graphics_list:
    graphic_file = graphic["file"]  # e.g., '1000.edf'
    graphic_name = graphic.get("name", os.path.splitext(graphic_file)[0])
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in graphic_name)
    output_path = os.path.join(OUTPUT_DIR, f"{safe_name}.png")

    try:
        # Step 1: open diagram session
        open_url = f"{EDS_HOST}/api/v1/diagram/open"
        query = {
            "source": SOURCE,
            "file": graphic_file,
            "httpUrl": f"http://127.0.0.1:43090/",  # GFX host/port
        }
        open_resp = session.post(open_url, json=query)
        open_resp.raise_for_status()
        diagram_url = open_resp.json()["url"]

        # Step 2: extract UUID and create gfx API URL
        session_id = diagram_url.rstrip("/").split("/")[-1]
        gfx_api_url = f"http://127.0.0.1:43090/api/v1/{session_id}/"

        # Step 3: render diagram as PNG
        render_resp = session.get(f"{gfx_api_url}/render", params={"format": "png", "width": 1920, "height": 1080})
        render_resp.raise_for_status()

        # Step 4: save PNG
        with open(output_path, "wb") as f:
            f.write(render_resp.content)
        print(f"Saved {graphic_name} → {output_path}")

    except Exception as e:
        print(f"Failed to export {graphic_name}: {e}")

# --- LOGOUT ---
session.post(f"{EDS_HOST}/api/v1/logout")
print("Done exporting all graphics.")