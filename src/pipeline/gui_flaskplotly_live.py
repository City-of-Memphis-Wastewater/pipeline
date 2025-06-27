from flask import Flask, render_template_string, jsonify
import plotly.graph_objs as go
#from plotly.utils import PlotlyJSONEncoder
from threading import Lock
#import time
#import json 

app = Flask(__name__)
plot_buffer = None  # Will be set by run_gui()
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
            //const layout = JSON.parse(`{{ layout | safe }}`);
            //Plotly.newPlot('live-plot', traces, layout);
            Plotly.newPlot('live-plot', traces, { margin: { t: 30 } });
        }

        setInterval(updatePlot, 2000);  // Refresh every 2 seconds
        updatePlot();  // Initial load
    </script>
</body>
</html>
"""
'''
plot_layout = go.Layout(
    xaxis=dict(
        title="Time",
        type="date",  # Enables date parsing
        tickformat="%H:%M:%S"  # e.g., 14:35:00
    ),
    yaxis=dict(title="Value"),
    margin=dict(l=40, r=20, t=40, b=40),
    height=400
)
layout_json = json.dumps(plot_layout, cls=PlotlyJSONEncoder)
'''
@app.route("/")
def index():
    #return render_template_string(HTML_TEMPLATE, layout=layout_json)
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
