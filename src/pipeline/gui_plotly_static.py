# src/pipeline/gui_plotly_static.py

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
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9

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
            "Series Alpha": {"x": [1, 2, 3, 4], "y": [10, 20, 15, 25]},
            "Series Beta": {"x": [1, 2, 3, 4], "y": [5, 12, 18, 10]},
        }
#plot_buffer = MockBuffer()
    
def show_static(plot_buffer):
    """
    Renders the current contents of plot_buffer as a static HTML plot.
    Does not listen for updates.
    launches a temporary server that can be shut down via a button on the plot page.
    """
    if plot_buffer is None:
        print("plot_buffer is None")
        return

    with buffer_lock:
        data = plot_buffer.get_all()

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    traces = []
    for i, (label, series) in enumerate(data.items()):
        scatter_trace = go.Scatter(
            x=series["x"],
            y=series["y"],
            mode="lines+markers",
            name=label,
        )
        # Explicitly set the line and marker color using update()
        # This is a robust way to ensure the properties are set
        
        scatter_trace.update(
            line=dict(
                color=colors[i],
                width=2
            ),
            marker=dict(
                color=colors[i],
                size=10,
                symbol='circle'
            )
        )   
        traces.append(scatter_trace)

    layout = go.Layout(
        title="EDS Data Plot (Static)",
        margin=dict(t=40),
        #colorway=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    )

    fig = go.Figure(data=traces, layout=layout)

    # Update the layout to position the legend at the top-left corner
    fig.update_layout(legend=dict(
    yanchor="auto",
    y=0.0,
    xanchor="auto",
    x=0.0,
    bgcolor='rgba(255, 255, 255, 0.1)',  # Semi-transparent background
    bordercolor='black',
    
    ))

    # Write to a temporary HTML file
    # Use Path to handle the temporary file path
    tmp_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode='w', encoding='utf-8')
    
    # Write the plot to the file
    #pyo.plot(fig, filename=tmp_file.name, auto_open=False)
    # Write the plot to the file while forcing the entire Plotly JS library (about 3MB) to be included in the HTML file
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