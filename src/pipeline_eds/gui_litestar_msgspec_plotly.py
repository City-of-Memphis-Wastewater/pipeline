# src/pipeline_eds/gui_litestar_msgspec_plotly.py

from litestar import Litestar, get
from litestar.response import HTMLResponse, JSONResponse
from threading import Lock, Thread
import uvicorn
import time
import webbrowser
import msgspec
from msgspec import Struct

# ----------------------------
# Data Models using msgspec
# ----------------------------
class Point(Struct):
    x: float
    y: float

class Series(Struct):
    label: str
    points: list[Point]

    def to_dict(self):
        # Convert to format expected by Plotly: { "x": [...], "y": [...] }
        return {
            "x": [p.x for p in self.points],
            "y": [p.y for p in self.points],
        }

# ----------------------------
# Global state
# ----------------------------
plot_buffer: list[Series] = []  # Thread-safe list of Series
buffer_lock = Lock()

# ----------------------------
# HTML Frontend
# ----------------------------
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

        setInterval(updatePlot, 2000);
        updatePlot();
    </script>
</body>
</html>
"""

# ----------------------------
# Litestar route handlers
# ----------------------------
@get("/")
async def index() -> HTMLResponse:
    return HTMLResponse(HTML_TEMPLATE)

@get("/data")
async def get_data() -> JSONResponse:
    with buffer_lock:
        # Convert Series list to Plotly-compatible dict
        data = {s.label: s.to_dict() for s in plot_buffer}
    return JSONResponse(data)

# ----------------------------
# Browser launcher
# ----------------------------
def open_browser(port: int):
    time.sleep(1)  # Wait for server to start
    webbrowser.open(f"http://127.0.0.1:{port}")

# ----------------------------
# Run server
# ----------------------------
def run_gui(buffer: list[Series], port: int = 8000):
    global plot_buffer
    plot_buffer = buffer

    # Start browser thread
    Thread(target=open_browser, args=(port,), daemon=True).start()

    # Start Litestar server with Uvicorn
    uvicorn.run(
        "src.pipeline_eds.gui_litestar_msgspec_plotly:app",
        host="127.0.0.1",
        port=port,
        log_level="info"
    )

# ----------------------------
# Litestar app
# ----------------------------
app = Litestar(route_handlers=[index, get_data])

if __name__ == "__main__":
    # Example: populate buffer with some dummy data
    from random import random

    points = [Point(x=i, y=random()) for i in range(10)]
    series1 = Series(label="Sensor A", points=points)
    series2 = Series(label="Sensor B", points=[Point(x=i, y=random()) for i in range(10)])

    buffer = [series1, series2]

    run_gui(buffer, port=8000)
