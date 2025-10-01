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

buffer_lock = threading.Lock()  # Optional, if you want thread safety

# A simple HTTP server that serves files from the current directory.
# We suppress logging to keep the Termux console clean.
class PlotServer(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    
def show_static(plot_buffer):
    """
    Renders the current contents of plot_buffer as a static HTML plot.
    Does not listen for updates.
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
        # On Termux/Linux, use xdg-open for the URL
        if is_termux():
            subprocess.run(['xdg-open', tmp_url], check=True)
        
        # On Windows/other systems, use webbrowser (which handles xdg-open fallback often)
        else: 
            webbrowser.open(tmp_url)
        print(f"Successfully opened {tmp_url}")

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
