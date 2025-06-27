from flask import Flask, render_template_string, jsonify
import plotly.graph_objs as go
from threading import Lock
import time

app = Flask(__name__)
plot_buffer = None  # Will be set by run_gui()
buffer_lock = Lock()

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Live Plot</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
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

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/data")
def get_data():
    with buffer_lock:
        data = plot_buffer.get_all()  # Expected to be a dict of {label: {"x": [...], "y": [...]}}
    return jsonify(data)

def run_gui(buffer, port=5000):
    global plot_buffer
    plot_buffer = buffer
    app.run(debug=False, port=port, use_reloader=False)
