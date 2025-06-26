import time
import logging
from dearpygui import dearpygui as dpg
from pipeline import helpers
from src.pipeline.plotbuffer import PlotBuffer  # Assuming it's here

logger = logging.getLogger(__name__)

PADDING_RATIO = 0.25 
def compute_padded_bounds(data):

    all_x_vals = []
    all_y_vals = []

    for series in data.values():
        all_x_vals.extend(series["x"])
        all_y_vals.extend(series["y"])

    # Compute padded bounds
    x_min, x_max = min(all_x_vals), max(all_x_vals)
    y_min, y_max = min(all_y_vals), max(all_y_vals)

    x_pad = max((x_max - x_min) * PADDING_RATIO, 1.0)
    y_pad = max((y_max - y_min) * PADDING_RATIO, 1.0)

    padded_x = [x_min - x_pad, x_max + x_pad]
    padded_y = [y_min - y_pad, y_max + y_pad]

    return padded_x, padded_y

def apply_time_axis_ticks(data, last_tick_update):
    now = time.time()
    all_x_vals = []

    for series in data.values():
        all_x_vals.extend(series["x"])

    if now - last_tick_update[0] > 1.0:
        # set ticks here
            
        if all_x_vals:
            try:
                # Ensure values are unique and sorted to avoid DPG internal assertion
                unique_ts = sorted(set(all_x_vals))
                tick_count = min(6, len(unique_ts))
                interval = max(1, len(unique_ts) // tick_count)
                tick_vals = unique_ts[::interval]

                # Build ticks as list of (float, str)
                ticks = [(float(v), helpers.human_readable(v)) for v in tick_vals]
                if ticks:
                    dpg.set_axis_ticks("x_axis", ticks)
            except Exception as e:
                logger.warning(f"Failed to set x-axis ticks: {e}")
        
        last_tick_update[0] = now

def run_gui(buffer: PlotBuffer):
    dpg.create_context()
    dpg.configure_app(docking=True, docking_space=True)

    with dpg.theme() as transparent_theme:
        with dpg.theme_component(dpg.mvScatterSeries):
            # mvPlotCol_Line affects the marker outline; mvPlotCol_MarkerFill for fill
            dpg.add_theme_color(dpg.mvPlotCol_Line, (0, 0, 0, 0), category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, (0, 0, 0, 0), category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, (0, 0, 0, 0), category=dpg.mvThemeCat_Plots)


    with dpg.window(label="Live Plot", width=600, height=400):
        dpg.add_text("Real-Time Plotting")
        with dpg.plot(label="Live 2D Plot", height=300, width=580):
            dpg.add_plot_legend()
            #x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_axis")
            #y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Value", tag="y_axis")
            dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, label="Value", tag="y_axis")

            series_tags = {}  # tag per trace

    last_tick_update = [0]  # Mutable to persist across frames
    last_gui_update = [0]
    def update_plot():
        # throttle the speed to match the eds demo speed
        now = time.time()
        if now - last_gui_update[0] < 2.0:  # Only update once per second - if overactive, the frame will be scheduled to skip
            dpg.set_frame_callback(dpg.get_frame_count() + 10, update_plot)
            return
        last_gui_update[0] = now
        
        #print("Plot buffer:", buffer.get_all())
        data = buffer.get_all()
        if not data:
            dpg.set_frame_callback(dpg.get_frame_count() + 10, update_plot)
            return  # nothing to draw yet
        for label, series in data.items():
            x_vals = series["x"]
            y_vals = series["y"]

            if not x_vals or not y_vals:
                continue  # avoid feeding empty arrays to DPG

            
            # This infers that you can change which data is included without stopping the program.
            if label not in series_tags:
                tag = f"series_{label}"
                dpg.add_line_series(x_vals, y_vals, label=label, tag=tag, parent="y_axis")

                series_tags[label] = tag
            else:
                dpg.set_value(series_tags[label], [x_vals, y_vals])
        
        if True:
            padded_x, padded_y = compute_padded_bounds(data)
            # Add invisible scatter (once)
            #if "padding_scatter" not in series_tags:
            if not dpg.does_item_exist("padding_scatter"):

                dpg.add_scatter_series(
                    padded_x,
                    padded_y,
                    label=None,
                    tag="padding_scatter",
                    parent="y_axis",
                    show=False  # <-- Hides from legend
                )

                dpg.bind_item_theme("padding_scatter", transparent_theme)
                
            else:
                dpg.set_value("padding_scatter", [padded_x, padded_y])
                dpg.hide_item("padding_scatter")

            dpg.bind_item_theme("padding_scatter", transparent_theme)
            # Then call:
            dpg.configure_item("padding_scatter", show=True)
            dpg.fit_axis_data("x_axis")
            dpg.fit_axis_data("y_axis")

        elif False:
            # Allow user interaction again:
            dpg.set_axis_limits_auto("x_axis")
            dpg.set_axis_limits_auto("y_axis")

        if False:
            apply_time_axis_ticks(data)

        dpg.set_frame_callback(dpg.get_frame_count() + 10, update_plot) # only runs if the first callback did not

    update_plot()  # First update

    dpg.create_viewport(title='Live Pipeline Plot', width=800, height=500)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()