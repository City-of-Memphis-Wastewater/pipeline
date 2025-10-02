import numpy as np
import logging
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from threading import Thread

from pipeline import helpers
from pipeline.plotbuffer import PlotBuffer  # Adjust import path as needed
from pipeline.time_manager import TimeManager
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9



logger = logging.getLogger(__name__)

PADDING_RATIO = 0.25

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
    # Auto-locate ticks and auto-format dates
    locator = mdates.AutoDateLocator()
    formatter = mdates.AutoDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

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

def show_static(buffer: PlotBuffer):
    """
    Show a static matplotlib plot of the current PlotBuffer contents,
    with automatic date formatting based on time span.
    """
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("EDS Trend")
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")

    data = buffer.get_all()
    if not data:
        ax.text(0.5, 0.5, "No data to display", ha='center', va='center')
        plt.show()
        return

    for label, series in data.items():
        # Convert strings to datetime objects for better handling
        x_vals = [TimeManager(ts).as_datetime() for ts in series["x"]]
        y_vals = series["y"]

        ax.plot(x_vals, y_vals, marker='o', linestyle='-', label=label)

    # Let matplotlib auto-locate ticks and auto-format
    locator = mdates.AutoDateLocator()
    formatter = mdates.AutoDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    ax.legend()
    plt.tight_layout()
    plt.show()
