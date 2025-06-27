import pygal
from datetime import datetime, timedelta
import random
from pathlib import Path


def generate_mock_data(num_points=24):
    now = datetime.now()
    times = [now - timedelta(hours=i) for i in reversed(range(num_points))]
    labels = [t.strftime("%H:%M") for t in times]

    data = {
        "Sensor A": [random.uniform(0, 10) for _ in times],
        "Sensor B": [random.uniform(2, 8) for _ in times],
    }
    return labels, data


def generate_svg_report(filename="report.svg"):
    labels, data = generate_mock_data()

    chart = pygal.Line(
        x_label_rotation=35,
        show_minor_x_labels=False,
        style=pygal.style.LightStyle,
        fill=True,
        show_legend=True,
        width=1000,
        height=400,
    )

    chart.title = "Hourly Sensor Readings"
    chart.x_labels = labels
    chart.x_labels_major = labels[::4]

    for label, values in data.items():
        chart.add(label, values)

    out_path = Path(filename).resolve()
    chart.render_to_file(out_path)
    print(f"✅ SVG report saved to: {out_path}")


if __name__ == "__main__":
    generate_svg_report()
