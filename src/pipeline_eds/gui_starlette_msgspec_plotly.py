# src/pipeline/gui_starlette_msgspec_plotly.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware
import msgspec
import threading
import time
from threading import Lock

from pipeline_eds.server.web_utils import launch_browser  # Your WSL2 browser helper

# --- Shared plot buffer ---
plot_buffer = None  # Will be set by run_gui()
buffer_lock = Lock()

# -----------------------------
# Msgspec validation decorator
# -----------------------------
def msgspec_validate(req_model: type = None, res_model: type = None):
    def decorator(fn):
        async def wrapper(request, *args, **kwargs):
            input_data = None
            if req_model:
                body_bytes = await request.body()
                try:
                    input_data = msgspec.json.decode(body_bytes, type=req_model)
                except msgspec.ValidationError as e:
                    return JSONResponse({"error": str(e)}, status_code=400)

            result = await fn(request, input_data, *args, **kwargs) if req_model else await fn(request, *args, **kwargs)

            if res_model:
                try:
                    validated = res_model(**result) if isinstance(result, dict) else res_model(result)
                    # Convert msgspec.Struct into plain dicts for JSONResponse
                    plain_dict = msgspec.json.decode(msgspec.json.encode(validated))
                    return JSONResponse(plain_dict)
                except msgspec.ValidationError as e:
                    return JSONResponse({"error": str(e)}, status_code=500)
            else:
                return result

        return wrapper
    return decorator

# -----------------------------
# Msgspec models
# -----------------------------
class Series(msgspec.Struct):
    x: list[float]
    y: list[float]
    unit: str | None = None  # optional, default None

"""
# Manual version (for internal use with .asdict())
class Series:
    def __init__(self, x=None, y=None, unit=None):
        self.x = x or []
        self.y = y or []
        self.unit = unit

    def asdict(self):
        return {"x": self.x, "y": self.y, "unit": self.unit}
"""

class PlotData(msgspec.Struct):
    __root__: dict[str, Series]

# -----------------------------
# HTML template
# -----------------------------
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
            for (const [label, series] of Object.entries(data.__root__)) {
                traces.push({ x: series.x, y: series.y, name: label, mode: 'lines+markers', type: 'scatter' });
            }
            Plotly.newPlot('live-plot', traces, { margin: { t: 30 } });
        }

        setInterval(updatePlot, 2000);
        updatePlot();
    </script>
</body>
</html>
"""

# -----------------------------
# Route handlers
# -----------------------------
async def index(request):
    return HTMLResponse(HTML_TEMPLATE)

@msgspec_validate(res_model=PlotData)
async def get_data(request):
    if plot_buffer is None:
        return JSONResponse({"__root__": {}})
    with buffer_lock:
        raw_data = plot_buffer.get_all()

    # Convert to msgspec.Struct objects
    series_data = {key: Series(**value) for key, value in raw_data.items()}
    #series_data = {
    #    k: Series(x=values["x"], y=values["y"], unit=values.get("unit"))
    #    for k, v in raw_data.items()
    #}
    return {"__root__": series_data}

# -----------------------------
# Starlette app
# -----------------------------
routes = [Route("/", index), Route("/data", get_data)]
app = Starlette(routes=routes)
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# -----------------------------
# Browser launcher for WSL2
# -----------------------------
def open_browser(port):
    time.sleep(1)
    try:
        launch_browser(f"http://127.0.0.1:{port}")
    except Exception:
        print(f"Open your browser manually: http://127.0.0.1:{port}")

# -----------------------------
# GUI runner
# -----------------------------
def run_gui(buffer, port=8000):
    global plot_buffer
    plot_buffer = buffer
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    print("Starting Starlette + Uvicorn app...")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info", reload=False)

# -----------------------------
# Demo buffer
# -----------------------------
class DummyBuffer:
    def get_all(self):
        return {
            "Series1": {"x": [1, 2, 3], "y": [4, 5, 6]},
            "Series2": {"x": [1, 2, 3], "y": [7, 8, 9]},
        }

if __name__ == "__main__":
    run_gui(DummyBuffer())
