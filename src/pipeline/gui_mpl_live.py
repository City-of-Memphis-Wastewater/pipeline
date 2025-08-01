import numpy as np
import time
import logging
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pipeline import helpers
from src.pipeline.plotbuffer import PlotBuffer  # Adjust import path as needed
from src.pipeline.time_manager import TimeManager

logger = logging.getLogger(__name__)

PADDING_RATIO = 0.25

def compute_padded_bounds(data):
    all_x_vals = []
    all_y_vals = []

    for series in data.values():
        all_x_vals.extend(series["x"])
        all_y_vals.extend(series["y"])

    if not all_x_vals or not all_y_vals:
        return (0, 1), (0, 1)

    x_min, x_max = min(all_x_vals), max(all_x_vals)
    y_min, y_max = min(all_y_vals), max(all_y_vals)

    x_pad = max((x_max - x_min) * PADDING_RATIO, 1.0)
    y_pad = max((y_max - y_min) * PADDING_RATIO, 1.0)

    padded_x = (x_min - x_pad, x_max + x_pad)
    padded_y = (y_min - y_pad, y_max + y_pad)

    return padded_x, padded_y

def run_gui(buffer: PlotBuffer, update_interval_ms=1000):
    """
    Runs a matplotlib live updating plot based on the PlotBuffer content.
    `update_interval_ms` controls how often the plot refreshes (default 1000ms = 1s).
    """
    # plt.style.use('seaborn-darkgrid')
    plt.style.use('ggplot')  # matplotlib built-in style as a lightweight alternative

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("Live Pipeline Data")
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")

    lines = {}
    legend_labels = []

    def init():
        ax.clear()
        ax.set_title("Live Pipeline Data")
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        return []

    def update(frame):
        data = buffer.get_all()
        if not data:
            return []

        # Add/update lines for each series
        for label, series in data.items():
            x_vals = series["x"]
            y_vals = series["y"]
            # Decide how many ticks you want (e.g., max 6)
            num_ticks = min(6, len(x_vals))

            # Choose evenly spaced indices
            indices = np.linspace(0, len(x_vals) - 1, num_ticks, dtype=int)

            if label not in lines:
                # Create new line
                line, = ax.plot(x_vals, y_vals, label=label)
                lines[label] = line
                legend_labels.append(label)
                ax.legend()
            else:
                lines[label].set_data(x_vals, y_vals)

        # Adjust axes limits with padding
        padded_x, padded_y = compute_padded_bounds(data)
        ax.set_xlim(padded_x)
        ax.set_ylim(padded_y)

        # Format x-axis ticks as human readable time strings

        # Tick positions are x values at those indices
        #tick_positions = x_vals[indices]
        tick_positions = np.array(x_vals)[indices]
        tick_labels = [TimeManager(ts).as_formatted_time() for ts in tick_positions]
        # Convert UNIX timestamps to formatted strings on x-axis
        #xticks = ax.get_xticks()
        #xtick_labels = [TimeManager(x).as_formatted_time() for x in xticks]
        ax.set_xticks(tick_positions)
        #ax.set_xticklabels(xtick_labels, rotation=45, ha='right')
        ax.set_xticklabels(tick_labels, rotation=45, ha='right')

        return list(lines.values())

    ani = animation.FuncAnimation(
        fig,
        update,
        init_func=init,
        interval=update_interval_ms,
        blit=False  # blit=True can be tricky with multiple lines and dynamic axes
    )

    plt.tight_layout()
    plt.show()

