# src/pipeline/gui_fastapi_plotly_live.py

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from threading import Lock
import uvicorn
import time
import threading
import webbrowser

app = FastAPI()
plot_buffer = None  # Set externally
buffer_lock = Lock()

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Live Plot</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
</head>
<body>
    <h2>Live EDS Data Plot</h2>
    <div id="live-plot" style="width:90%;height:80vh;"></div>
    <script>
        async function fetchData() {
            const res = await fetch("/data");
            return await res.json();
        }

        async function updatePlot() {
            const data = await fetchData();
            const traces = [];

            for (const [label, series] of Object.entries(data)) {
                traces.push({
                    x: series.x,
                    y: series.y,
                    name: label,
                    mode: 'lines+markers',
                    type: 'scatter'
                });
            }
            Plotly.newPlot('live-plot', traces, { margin: { t: 30 } });
        }

        setInterval(updatePlot, 2000);  // Refresh every 2 seconds
        updatePlot();  // Initial load
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_TEMPLATE

@app.get("/data", response_class=JSONResponse)
async def get_data():
    with buffer_lock:
        data = plot_buffer.get_all()  # Should return { label: {"x": [...], "y": [...]}, ... }
    return data

def open_browser(port):
    time.sleep(1)  # Give server a moment to start
    ## Open in a new Chrome window (if installed)
    ##chrome_path = webbrowser.get(using='windows-default')
    ##chrome_path.open_new(f"http://127.0.0.1:{port}")

    webbrowser.open(f"http://127.0.0.1:{port}")

def run_gui(buffer, port=8000):
    global plot_buffer
    plot_buffer = buffer
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    uvicorn.run("src.pipeline.gui_fastapi_plotly_live:app", host="127.0.0.1", port=port, log_level="info", reload=False)
