from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import plotly.graph_objs as go
import plotly.offline as pyo
import webbrowser
import tempfile
import threading
from pyhabitat import on_termux
import http.server
import time
from pathlib import Path
import os
import subprocess
from urllib.parse import urlparse
import signal

from pipeline.web_utils import launch_browser
from pipeline.plottools import normalize, normalize_ticks, get_ticks_array_n


PLOTLY_THEME = 'seaborn'
"""
COLORS = [
    'rgba(31, 119, 180, 0.7)',  # #1f77b4
    'rgba(255, 127, 14, 0.7)',  # #ff7f0e
    'rgba(44, 160, 44, 0.7)',  # #2ca02c
    'rgba(214, 39, 40, 0.7)',  # #d62728
    'rgba(148, 103, 189, 0.7)', # #9467bd
    'rgba(140, 86, 75, 0.7)',  # #8c564b
    'rgba(227, 119, 194, 0.7)', # #e377c2
    'rgba(127, 127, 127, 0.7)', # #7f7f7f
    'rgba(188, 189, 34, 0.7)',  # #bcbd22
    'rgba(23, 190, 207, 0.7)'  # #17becf
] """  
COLORS = []
font_size = 20 if on_termux() else 14


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
            "Series Alpha": {"x": [1, 2, 3, 4], "y": [7, 13, 7, 9], "unit": "MGD"},
            "Series Beta": {"x": [1, 2, 3, 4], "y": [10, 20, 15, 25], "unit": "MG/L"},
            "Series Gamma": {"x": [1, 2, 3, 4], "y": [5, 12, 11, 10], "unit": "MGD"},
            "Series Delta": {"x": [1, 2, 3, 4], "y": [12, 17, 14, 20], "unit": "MG/L"},
            "Series Epison": {"x": [1, 2, 3, 4], "y": [4500, 3000, 13000, 8000], "unit": "KW"},
            "Series Zeta": {"x": [1, 2, 3, 4], "y": [5000, 4000, 12000, 9000], "unit": "KW"},
        }
#plot_buffer = MockBuffer()


def assess_unit_stats(data):
    """
    For curves with shared units, determine the overall min/max for the shared axis
    """
    # --- PASS 1: AGGREGATE DATA RANGES PER UNIT ---
    # We must loop through all data first to find the true min/max for each unit.
    unit_stats = {}
    for label, series in data.items():
        unit = series["unit"]
        #y_data = np.array(series["y"], dtype="float")
        y_data = [float(x) for x in series["y"]]
        
        #if not np.any(y_data): continue # Skip empty series

        #current_min, current_max = np.min(y_data), np.max(y_data)
        current_min, current_max = min(y_data), max(y_data)
        
        if unit not in unit_stats:
            unit_stats[unit] = {"min": current_min, "max": current_max}
        else:
            # Update the min/max for this unit if needed
            unit_stats[unit]["min"] = min(unit_stats[unit]["min"], current_min)
            unit_stats[unit]["max"] = max(unit_stats[unit]["max"], current_max)
    return unit_stats

def assess_layout_updates(unit_stats):
    # --- BUILD AXES BASED ON AGGREGATED STATS ---
    # Now that we have the final range for each unit, create the axes.
    axis_counter = 0
    layout_updates = {}
    unit_to_axis_index = {}  # enables a new axis to be made for each unique unit
    for unit, stats in unit_stats.items():
        unit_to_axis_index[unit] = axis_counter
        layout_key = 'yaxis' if axis_counter == 0 else f'yaxis{axis_counter + 1}'
        
        layout_updates[layout_key] = build_y_axis(
            y_min=stats["min"], 
            y_max=stats["max"],
            axis_index=axis_counter,
            axis_label=f"{unit}",
            tick_count=10
        )
        axis_counter += 1
    return layout_updates, unit_to_axis_index

def y_normalize_global(y_original,unit_stats, unit=None):
    # Get the global min/max for this trace's unit
    global_min = unit_stats[unit]["min"]
    global_max = unit_stats[unit]["max"]

    # VISUAL NORMALIZATION: Normalize using the GLOBAL range for the unit.
    # This ensures all traces on the same axis share the same scale.
    if global_max == global_min:
        #y_normalized = np.zeros_like(y_original)
        y_normalized = [0.0] * len(y_original)
        
    else:
        #y_normalized = (y_original - global_min) / (global_max - global_min)
        range_val = global_max - global_min
        y_normalized = [
            (y_val - global_min) / range_val
            for y_val in y_original
        ]
    return y_normalized

def build_y_axis(y_min, y_max,axis_index,axis_label,tick_count = 10):
    # Normalize the data and get min/max for original scale
    
    # Define the original tick values for each axis
    
    original_ticks = get_ticks_array_n(y_min,y_max,tick_count)
    
    # Calculate the normalized positions for the original ticks
    ticktext = [f"{t:.0f}" for t in original_ticks]
    tickvals=normalize_ticks(original_ticks, y_min, y_max) # Normalized positions

    pos = (0.0025*axis_index**2)+(axis_index)*0.1
    overlaying_prop = "y" if axis_index > 0 else None
    
    #pos = (axis_index)
    #pos= 0
    yaxis_dict=dict(
        title=dict(text=axis_label, standoff=10), # Use dict for better control
        #overlaying="y", # or "no", no known difference # suppress
        overlaying = overlaying_prop,
        side="left",
        anchor="free", 
        position = pos,
        #range=[0, 1], # Set the axis range to the normalized data range
        #range = [-0.05, 1.05], # Set range for normalized data [0,1] with a little padding
        tickmode='array',
        tickvals = tickvals,
        ticktext=ticktext,           # Original labels
        showgrid=(axis_index == 0), # Show grid only for the first (leftmost) y-axis
        gridcolor='#e0e0e0',
        #zeroline=False)
        zeroline=False,
        layer = "above traces") # or "above_traces"
        #layer = "below traces") # or "below_traces"
    
    return yaxis_dict
# --- Modified show_static Function ---

def show_static(plot_buffer)->"go.Plotly":
    """
    Renders the current contents of plot_buffer as a static HTML plot.
    - Data is visually normalized, but hover-text shows original values.
    - Each curve gets its own y-axis, evenly spaced horizontally.
    """
    def handle_exit(signum, frame):
        print("\nSignal received. Shutting down server...")
        if httpd:
            httpd.shutdown()
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    if plot_buffer is None:
        print("plot_buffer is None")
        return

    with buffer_lock:
        data = plot_buffer.get_all()
        
    if not data:
        print("plot_buffer is empty")
        return
    
    unit_stats = assess_unit_stats(data)
    #print(f"unit_stats = {unit_stats}")
    layout_updates, unit_to_axis_index = assess_layout_updates(unit_stats)
    #print(f"unit_to_axis_index = {unit_to_axis_index}")
    traces = []
    
    for i, (label, series) in enumerate(data.items()):
        
        #y_original = np.array(series["y"],dtype="float")
        y_original = [float(x) for x in series["y"]]
        unit = series["unit"]
        # 1. VISUAL NORMALIZATION: Normalize y-data for plotting
        #y_normalized , y_min, y_max = normalize(y_original)
        #if y_original.size == 0: continue
        if len(y_original)==0: continue
        y_normalized = y_normalize_global(y_original,unit_stats, unit)
        
        current_axis_idx = unit_to_axis_index[unit]
        axis_id = 'y' if current_axis_idx == 0 else f'y{current_axis_idx+1}' # This is the Plotly trace axis *name* ('y1', 'y2', etc.)
            
        scatter_trace = go.Scatter(
            x=series["x"],
            y=y_normalized,  # Use normalized data for visual plotting
            mode="lines+markers",
            name=label,
            yaxis=axis_id, # Link this trace to its specific y-axis using the expected plotly jargon (e.g. 'y', 'y1', 'y2', 'y3', etc.) 
            ##line=dict(color=COLORS[i % len(COLORS)],width=2,),
            ##marker=dict(color=COLORS[i % len(COLORS)],size=6,symbol='circle'),
        
            # 2. NUMERICAL ACCURACY: Store original data for hover info
            customdata=y_original,
            hovertemplate=(
                f"<b>{label}</b><br>"
                "X: %{x}<br>"
                "Y: %{customdata:.4f}<extra></extra>" # Display original Y from customdata
            ),
            opacity=1.0
        )       
        traces.append(scatter_trace)

    # --- Figure Creation and Layout Updates ---
    final_layout = {
        #'title': "EDS Data Plot (Static)", # shows large on mobile, not very useful
        'template':PLOTLY_THEME,
        'showlegend': True,
        # Set the plot area to span the full width of the figure as requested
        'xaxis': dict(domain=[0.0, 1.0], title="Time"),
        'font':dict(size=font_size),
        'legend': dict(
            yanchor="auto",
            y=0.01,
            xanchor="auto",
            x=0.98, # Position legend in the top-left corner
            bgcolor='rgba(255, 255, 255, 0.1)', # semi transparent background
            bordercolor='grey',
            borderwidth=1,
            #title="Curves"
        ),
        'margin': dict(l=5, r=5, t=5, b=5) # Add on;y a little padding around the whole figure - this increases the size compared to the default
    }

    # --- File Generation and Display ---
    final_layout.update(layout_updates)
    fig = go.Figure(data=traces, layout=go.Layout(final_layout))
    
    #return fig # for making free simpleguiweb consume
    # REMOVE THIS LINE TO REVERT

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
    on_termux_mode = on_termux()
    tmp_path = inject_buttons(tmp_path, is_server_mode=on_termux_mode)

    
    os.chdir(str(tmp_dir))

    # If running in Windows, open the file directly
    if not on_termux():
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
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception as e:
                print(f"Failed to delete temp file: {e}")
    # NOTE: You might need a cleanup mechanism for this temporary file.

    
    return fig

    

def inject_buttons(tmp_path: Path, is_server_mode: bool) -> Path:
    """
    Injects a shutdown button and corresponding JavaScript logic into the existing plot HTML file.
    The JavaScript logic is conditional based on whether a server is running (is_server_mode).

    Injects a darkmode button.

    Injects a button to hide the legend.
    """
    
    # The JavaScript logic for closing the plot, made conditional via Python f-string
    if is_server_mode:
        # SERVER MODE: Uses fetch to talk to the Python server's /shutdown endpoint
        js_close_logic = """
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
        button_text_close = "Close Plot "
    else:
        # STATIC FILE MODE: Just closes the browser tab/window
        js_close_logic = """
        function closePlot() {
            // STATIC FILE MODE: Close the tab/window directly 
            console.log("Static file mode detected. Closing window.");
            window.close();
        }
        """
        button_text_close = "Close Plot"
    # ----------------------------------------------------
    # JavaScript for Plotly-specific controls
    # ----------------------------------------------------
    js_plotly_logic = f"""
    let isLegendVisible = true;

    function getPlotlyDiv() {{
        /** Plotly plots are typically contained in the first div with the class 'js-plotly-plot' **/
        return document.querySelector('.js-plotly-plot');
    }}

    function toggleLegend() {{
        const plotDiv = getPlotlyDiv();
        if (!plotDiv) return;

        isLegendVisible = !isLegendVisible;
        const newVisibility = isLegendVisible;
        const button = document.getElementById('toggleLegendButton');
        
        /** Update the Plotly layout **/
        Plotly.relayout(plotDiv.id, {{
            'showlegend': newVisibility
        }});

        /** Update the button text **/
        button.textContent = newVisibility ? 'Hide Legend' : 'Show Legend';
    }}


    function toggleTheme() {{
        const body = document.body;
        const button = document.getElementById('toggleThemeButton');

        // Toggle classes between theme-dark (inverted) and theme-light (native)
        if (body.classList.contains('theme-light')) {{
            body.classList.remove('theme-light');
            body.classList.add('theme-dark');
        }} else {{
            body.classList.remove('theme-dark');
            body.classList.add('theme-light');
        }}

        // Update button text to reflect the NEW mode it will switch TO
        button.textContent = body.classList.contains('theme-light') ? 'Dark Mode' : 'Light Mode';
    }}

    // --- Initialization: Set button text based on initial class ---
    (function() {{
        const button = document.getElementById('toggleThemeButton');
        if (button) {{
            // We start with <body class="theme-dark">, so the button should offer to switch to 'Light Mode'.
            button.textContent = 'Light Mode';
        }}
    }})();
    // -------------------------------------------------------------
    """
    # ----------------------------------------------------
    # Inject Buttons into the HTML
    # ----------------------------------------------------
    
    # Define the HTML/CSS for all control buttons
    buttons_html = f"""
    <style>
        .control-button {{
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
            color: white;
            background-color: #3b82f6;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
            transition: background-color 0.3s;
            z-index: 1000;
            margin-left: 10px; /* Space between buttons */
        }}
        .control-button:hover {{
            background-color: #2563eb;
        }}
        #button-container {{
            position: fixed;
            bottom: 15px;
            right: 15px;
            display: flex;
            flex-direction: row-reverse; /* Arrange buttons from right (Close Plot) to left (Legend) */
            align-items: center;
        }}

        /* --- THEME STYLES --- */
        
        /* Transition for smooth visual changes */
        body, .js-plotly-plot {{
            transition: background-color 0.0s ease, color 0.0s ease, filter 0.0s ease;
        }}
        
        /* THEME DARK (Initial State) - Apply filter to invert the light Plotly output */
        body.theme-dark {{
            background-color: #111; /* Dark background for the page */
            color: #eee;
        }}
        body.theme-dark .js-plotly-plot {{
            /* Invert the colors of the light Plotly chart to make it dark */
            filter: invert(1) hue-rotate(180deg); 
            background-color: #111;
        }}

        /* THEME LIGHT (Toggled State) - Native Plotly look (seaborn is light) */
        body.theme-light {{
            background-color: #fafafa; /* Light background for the page */
            color: #222;
        }}
        body.theme-light .js-plotly-plot {{
            /* Remove filter to show native light Plotly colors */
            filter: none;
            background-color: #fafafa;
        }}


    </style>

    <div id="button-container">
        <button class="control-button" onclick="closePlot()">{button_text_close}</button>
        <button id="toggleThemeButton" class="control-button" onclick="toggleTheme()">Loading Theme...</button>
        <button id="toggleLegendButton" class="control-button" onclick="toggleLegend()">Hide Legend</button>
    </div>

    <script>
        {js_close_logic}
        {js_plotly_logic}
    </script>
    """

    # Read the existing Plotly HTML
    html_content = tmp_path.read_text(encoding='utf-8')
    

    # FIX: Replace <body> with <body class="theme-dark"> to trigger the dark (inverted) styles immediately
    html_content = html_content.replace('<body>', '<body class="theme-dark">')
    
    # Inject the button and script right before the closing </body> tag
    html_content = html_content.replace('</body>', buttons_html + '</body>')
    
    # Rewrite the file with the new content
    tmp_path.write_text(html_content, encoding='utf-8')
    return tmp_path

if __name__ == '__main__':
    # This block is for testing the plotting logic, assuming a working launch_browser
    show_static(MockBuffer())
