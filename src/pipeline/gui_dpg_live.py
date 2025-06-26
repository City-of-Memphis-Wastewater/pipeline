import time
import logging
from dearpygui import dearpygui as dpg

logger = logging.getLogger(__name__)

def run_gui(data_dictdict):
    dpg.create_context()
    dpg.configure_app(docking=True, docking_space=True)

    with dpg.window(label="Live Plot", width=600, height=400):
        dpg.add_text("Real-Time Plotting")
        with dpg.plot(label="Live 2D Plot", height=300, width=580):
            dpg.add_plot_legend()
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_axis")
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Value", tag="y_axis")

            # Create one line series per label in data_dictdict
            series_tags = {}
            for label in data_dictdict.keys():
                tag = f"series_{label}"
                dpg.add_line_series([], [], label=label, tag=tag, parent=y_axis)
                series_tags[label] = tag

    def update_plot():
        for label, series in data_dictdict.items():
            x_vals = series["x"]
            y_vals = series["y"]
            if label not in series_tags:
                # dynamically add new lines
                tag = f"series_{label}"
                dpg.add_line_series(x_vals, y_vals, label=label, tag=tag, parent=y_axis)
                series_tags[label] = tag
            else:
                dpg.set_value(series_tags[label], [x_vals, y_vals])

        dpg.set_frame_callback(dpg.get_frame_count() + 10, update_plot)

    update_plot()  # kick off first update

    dpg.create_viewport(title='Live Pipeline Plot', width=800, height=500)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
