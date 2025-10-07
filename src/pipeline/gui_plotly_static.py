# src/pipeline/gui_plotly_static.py

from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import plotly.graph_objs as go
import plotly.offline as pyo
import webbrowser
import tempfile
import threading
from pipeline.environment import is_termux
import http.server
import time
from pathlib import Path
import os
import subprocess
from urllib.parse import urlparse
import numpy as np

from pipeline.web_utils import launch_browser

buffer_lock = threading.Lock()  # Optional, if you want thread safety

# A simple HTTP server that serves files from the current directory.
# We suppress logging to keep the Termux console clean.
# --- Plot Server with Shutdown Endpoint ---
class PlotServer(http.server.SimpleHTTPRequestHandler):
    """
    A simple HTTP server that serves files and includes a /shutdown endpoint.
    """
    # Suppress logging to keep the console clean
    def log_message(self, format, *args):
        return
    
    def do_GET(self):
        """Handle GET requests, including the custom /shutdown path."""
        
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == '/shutdown':
            # 1. Respond to the browser first
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><head><title>Closing...</title></head><body>Server shutting down. You may close this tab.</body></html>')
            
            # 2. CRITICAL: Shut down the server thread
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
            
        # If not the shutdown path, serve the file normally
        else:
            http.server.SimpleHTTPRequestHandler.do_GET(self)

# --- Plot Generation and Server Launch ---

# Placeholder for plot_buffer.get_all() data structure
class MockBuffer:
    def get_all(self):
        return {
            "Series Alpha": {"x": [1, 2, 3, 4], "y": [10, 20, 15, 25], "unit": "MG/L"},
            "Series Beta": {"x": [1, 2, 3, 4], "y": [5, 12, 18, 10], "unit": "MGD"},
            "Series Gamma": {"x": [1, 2, 3, 4], "y": [5000, 4000, 12000, 9000], "unit": "KW"},
            "Series Sigma": {"x": [1, 2, 3, 4], "y": [5000, 4000, 12000, 9000], "unit": "KW"},
        }
#plot_buffer = MockBuffer()

COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    

# --- Helper Function for Normalization ---
# It's good practice to have this as a separate, robust function.
# Normalization function (scaling to range [0, 1])
# Returns the normalized array, min, and max of the original data
def normalize(data):
    """Normalizes a numpy array to the range [0, 1], 
    and return max and min."""
    min_val = np.min(data)
    max_val = np.max(data)
    # Handle the case where max_val == min_val to avoid division by zero
    if max_val == min_val:
        return np.zeros_like(data), min_val, max_val
    return (data - min_val) / (max_val - min_val), min_val, max_val

# Function to normalize a set of ticks based on the original data's min/max
def normalize_ticks(ticks, data_min, data_max):
    # Handle the case where max_val == min_val
    ticks_arr = np.asarray(ticks, dtype=np.float64)
    if not np.isfinite(data_min) or not np.isfinite(data_max):
        return (ticks_arr - float(data_min)) / (float(data_max) - float(data_min))
    if data_max == data_min:
        return np.zeros_like(ticks_arr)
    return np.array((ticks_arr - float(data_min)) / (float(data_max) - float(data_min)))

def get_ticks_array_n(y_min, y_max, steps):
    # Calculate the step size
    step = (y_max - y_min) / steps
    array_tick_location = []
    for i in range(steps+1): 
        array_tick_location.append(y_min+i*step)
    return array_tick_location

def build_y_axis(y_data,axis_index,axis_label,tick_count = 10):
    # Normalize the data and get min/max for original scale
    yn_normalized, y_min, y_max = normalize(y_data)
    
    # Define the original tick values for each axis
    
    original_ticks = get_ticks_array_n(y_min,y_max,tick_count)
    
    # Calculate the normalized positions for the original ticks
    ticktext = [f"{t:.0f}" for t in original_ticks]
    tickvals=normalize_ticks(original_ticks, y_min, y_max) # Normalized positions
    print(f"tickvals = {tickvals}")
    pos = (axis_index-1)*0.05+0.06
    yaxis_dict=dict(
        title=axis_label,
        overlaying="y", # or "no", no known difference
        side="left",
        anchor="x",
        position = pos,
        #position = (0.002*axis_index**2)+(axis_index*0.05)+0.06,
        #range=[0, 1], # Set the axis range to the normalized data range
        range = [-0.05, 1.05], # Set range for normalized data [0,1] with a little padding
        tickmode='array',
        #tickvals = list(map(np.float64(tickvals))),
        #tickvals = list(map(tickvals)),
        tickvals = tickvals,
        
        ticktext=ticktext,           # Original labels
        color=COLORS[axis_index-1],
        showgrid=False,
        zeroline=False,
        layer = "above traces")
    
    return yaxis_dict
# --- Modified show_static Function ---

def show_static(plot_buffer):
    """
    Renders the current contents of plot_buffer as a static HTML plot.
    - Data is visually normalized, but hover-text shows original values.
    - Each curve gets its own y-axis, evenly spaced horizontally.
    """
    if plot_buffer is None:
        print("plot_buffer is None")
        return

    with buffer_lock:
        data = plot_buffer.get_all()
        
    if not data:
        print("plot_buffer is empty")
        return

    traces = []
    units_used = []
    layout_updates = {}
    j=0
    for i, (label, series) in enumerate(data.items()):
        
        y_original = np.array(series["y"],dtype="float")
        unit = series["unit"]
        # 1. VISUAL NORMALIZATION: Normalize y-data for plotting
        y_normalized , yn_min, yn_max = normalize(y_original)
        
        # Determine the y-axis ID for this trace. First is 'y', second is 'y2', etc.
        axis_id = 'y' if i == 0 else f'y{i+1}' # This is the Plotly trace axis *name* ('y1', 'y2', etc.)


        scatter_trace = go.Scatter(
            x=series["x"],
            y=y_normalized,  # Use normalized data for visual plotting
            mode="lines+markers",
            name=label,
            yaxis=axis_id, # Link this trace to its specific y-axis using the expected plotly jargon (e.g. 'y', 'y1', 'y2', 'y3', etc.) 
            line=dict(color=COLORS[i % len(COLORS)],width=2),
            marker=dict(color=COLORS[i % len(COLORS)],size=8,symbol='circle'),
            
        #,
            # 2. NUMERICAL ACCURACY: Store original data for hover info
            customdata=y_original,
            hovertemplate=(
                f"<b>{label}</b><br>"
                "X: %{x}<br>"
                "Y: %{customdata:.4f}<extra></extra>" # Display original Y from customdata
            )
        )
        
        traces.append(scatter_trace)

        # The first axis is named 'yaxis', subsequent ones are 'yaxis2', 'yaxis3', etc.
        if not unit in units_used:
            units_used.append(unit)
            layout_key = 'yaxis' if j == 0 else f'yaxis{j+1}'
            layout_updates[layout_key] = build_y_axis(y_original,axis_index=j,axis_label = f"{unit}",tick_count = 10)
            j+=1
            
    # --- Figure Creation and Layout Updates ---

    # Define the base layout, hiding the default legend since axes titles now serve that purpose
    layout = go.Layout(
        title="EDS Data Plot (Static, Visually Normalized)",
        showlegend=True, 
        xaxis=dict(domain= [0.05, 0.95],title="Time") # Add a small margin to prevent axes titles from being cut off
    )

    fig = go.Figure(data=traces, layout=layout)
    
    # Apply all the generated y-axis layouts at once
    # Update the layout to position the legend at the top-left corner
    fig.update_layout(legend=dict(
        yanchor="auto",
        y=0.0,
        xanchor="auto",
        x=0.0,
        bgcolor='rgba(255, 255, 255, 0.1)',  # Semi-transparent background
        bordercolor='black',   
        )
    )

    # Apply all the generated y-axis layouts at once
    fig.update_layout(**layout_updates)
    if True:
        fig.update_layout(legend=dict(title="Curves"))
    # --- File Generation and Display ---

    # Write to a temporary HTML file
    tmp_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode='w', encoding='utf-8')
    pyo.plot(fig, filename=tmp_file.name, auto_open=False, include_plotlyjs='full')
    tmp_file.close()

    # Create a Path object from the temporary file's name
    tmp_path = Path(tmp_file.name)
    
    # Use Path attributes to get the directory and filename
    tmp_dir = tmp_path.parent
    tmp_filename = tmp_path.name

    # Change the current working directory to the temporary directory.
    # This is necessary for the SimpleHTTPRequestHandler to find the file.
    # pathlib has no direct chdir equivalent, so we still use os.
    original_cwd = os.getcwd() # Save original CWD to restore later if needed

    # --- Inject the button based on environment ---
    is_termux_mode = is_termux()
    tmp_path = inject_button(tmp_path, is_server_mode=is_termux_mode)

    
    os.chdir(str(tmp_dir))

    # If running in Windows, open the file directly
    if not is_termux():
        webbrowser.open(f"file://{tmp_file.name}")
        # Restore CWD before exiting
        os.chdir(original_cwd) 
        return
        
    else:
        pass

    # Start a temporary local server in a separate, non-blocking thread
    PORT = 8000
    httpd = None
    server_address = ('', PORT)
    server_thread = None
    MAX_PORT_ATTEMPTS = 10
    server_started = False 
    for i in range(MAX_PORT_ATTEMPTS):
        server_address = ('', PORT)
        try:
            httpd = http.server.HTTPServer(server_address, PlotServer)
            # Setting daemon=True ensures the server thread will exit when the main program does
            server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            server_thread.start()
            server_started = True # Mark as started
            break # !!! Crucial: Exit the loop after a successful start
        except OSError as e:
            if i == MAX_PORT_ATTEMPTS - 1:
                # If this was the last attempt, print final error and return
                print(f"Error starting server: Failed to bind to any port from {8000} to {PORT}.")
                print(f"File path: {tmp_path}")
                return
            # Port is busy, try the next one
            PORT += 1
    # --- START HERE IF SERVER FAILED ENTIRELY ---
     # Check if the server ever started successfully
    if not server_started:
        # If we reached here without starting the server, just return
        return

    # Construct the local server URL
    tmp_url = f'http://localhost:{PORT}/{tmp_filename}'
    print(f"Plot server started. Opening plot at:\n{tmp_url}")
    
    # Open the local URL in the browser
    # --- UNIFIED OPENING LOGIC ---
    try:
        launch_browser(tmp_url)

    except Exception as e:
        print(f"Failed to open browser using standard method: {e}")
        print("Please open the URL manually in your browser.")
    # ------------------------------
    
    # Keep the main thread alive for a moment to allow the browser to open.
    # The server will run in the background until the script is manually terminated.
    print("\nPlot displayed. Press Ctrl+C to exit this script and stop the server.")
    try:
        while server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        if httpd:
            httpd.shutdown()
            # Clean up the temporary file on exit
            # Restore CWD before exiting
            os.chdir(original_cwd) 
            if tmp_path.exists():
                tmp_path.unlink()

def inject_button(tmp_path: Path, is_server_mode: bool) -> Path:
    """
    Injects a shutdown button and corresponding JavaScript logic into the existing plot HTML file.
    The JavaScript logic is conditional based on whether a server is running (is_server_mode).
    """
    
    # The JavaScript logic for closing the plot, made conditional via Python f-string
    if is_server_mode:
        # SERVER MODE: Uses fetch to talk to the Python server's /shutdown endpoint
        js_logic = """
        function closePlot() {
            // SERVER MODE: Send shutdown request to Python server
            fetch('/shutdown')
                .then(response => {
                    console.log("Server shutdown requested.");
                    window.close(); 
                })
                .catch(error => {
                    console.error("Server shutdown request failed:", error);
                });
        }
        """
        button_text = "Close Plot "# (Stop Server)
    else:
        # STATIC FILE MODE: Just closes the browser tab/window
        js_logic = """
        function closePlot() {
            // STATIC FILE MODE: Close the tab/window directly
            console.log("Static file mode detected. Closing window.");
            window.close();
        }
        """
        button_text = "Close Plot"# (Close Tab)"
    
    # ----------------------------------------------------
    # NEW STEP: Inject Shutdown Button into the HTML
    # ----------------------------------------------------
    
    # Define the HTML/CSS for the close button
    shutdown_button_html = f"""
    <style>
        .close-button {{
            position: fixed;
            bottom: 15px;
            right: 15px;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            color: white;
            background-color: #3b82f6; /* Changed to a standard blue for clarity */
            border: none;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
            transition: background-color 0.3s;
            z-index: 1000;
        }}
        .close-button:hover {{
            background-color: #2563eb;
        }}
    </style>
    <button class="close-button" onclick="closePlot()">{button_text}</button>
    <script>
        {js_logic}
    </script>
    """
    
    # Read the existing Plotly HTML
    html_content = tmp_path.read_text(encoding='utf-8')
    
    # Inject the button and script right before the closing </body> tag
    html_content = html_content.replace('</body>', shutdown_button_html + '</body>')
    
    # Rewrite the file with the new content
    tmp_path.write_text(html_content, encoding='utf-8')
    return tmp_path

if __name__ == '__main__':
    # This block is for testing the plotting logic, assuming a working launch_browser
    show_static(MockBuffer())