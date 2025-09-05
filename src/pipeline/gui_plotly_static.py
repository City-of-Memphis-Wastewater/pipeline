# src/pipeline/gui_plotly_static.py

import plotly.graph_objs as go
import plotly.offline as pyo
import webbrowser
import tempfile
from threading import Lock

buffer_lock = Lock()  # Optional, if you want thread safety

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

    traces = []
    for label, series in data.items():
        traces.append(go.Scatter(
            x=series["x"],
            y=series["y"],
            mode="lines+markers",
            name=label
        ))

    layout = go.Layout(
        title="EDS Data Plot (Static)",
        margin=dict(t=40)
    )

    fig = go.Figure(data=traces, layout=layout)

    # Write to a temporary HTML file
    tmp_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    pyo.plot(fig, filename=tmp_file.name, auto_open=False)
    
    webbrowser.open(f"file://{tmp_file.name}")
