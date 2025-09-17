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
    yanchor="top",
    y=0.1,
    xanchor="left",
    x=0.0
    ))

    # Write to a temporary HTML file
    # Use Path to handle the temporary file path
    tmp_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode='w', encoding='utf-8')
    
    # Write the plot to the file
    pyo.plot(fig, filename=tmp_file.name, auto_open=False)
    tmp_file.close()

    # Create a Path object from the temporary file's name
    tmp_path = Path(tmp_file.name)
    
    # Use Path attributes to get the directory and filename
    tmp_dir = tmp_path.parent
    tmp_filename = tmp_path.name

    # Change the current working directory to the temporary directory.
    # This is necessary for the SimpleHTTPRequestHandler to find the file.
    # pathlib has no direct chdir equivalent, so we still use os.
    os.chdir(str(tmp_dir))

    # If running in Windows, open the file directly
    if not is_termux():
        webbrowser.open(f"file://{tmp_file.name}")
        return

    # Start a temporary local server in a separate, non-blocking thread
    PORT = 8000
    server_address = ('', PORT)
    try:
        httpd = http.server.HTTPServer(server_address, PlotServer)
        # Setting daemon=True ensures the server thread will exit when the main program does
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
    except OSError as e:
        print(f"Error starting server on port {PORT}: {e}")
        print("This is likely because another process is using the port.")
        print("Please try again later or manually navigate to the file.")
        print(f"File path: {tmp_path}")
        return

    # Construct the local server URL
    tmp_url = f'http://localhost:{PORT}/{tmp_filename}'
    print(f"Plot server started. Opening plot at:\n{tmp_url}")
    
    # Open the local URL in the browser
    webbrowser.open(tmp_url)
    
    # Keep the main thread alive for a moment to allow the browser to open.
    # The server will run in the background until the script is manually terminated.
    print("\nPlot displayed. Press Ctrl+C to exit this script and stop the server.")
    try:
        while server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting.")
        httpd.shutdown()
        # Clean up the temporary file on exit
        if tmp_path.exists():
            tmp_path.unlink()
