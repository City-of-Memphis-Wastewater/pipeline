import logging
from dearpygui import dearpygui as dpg
from pathlib import Path
import random

from src.pipeline import plotsvg
# Setup logging as usual
import src.pipeline.logging_setup as logging_setup
logging_setup.setup_logging()
logger = logging.getLogger()
console_handler = next(h for h in logger.handlers if getattr(h, 'name', '') == 'console')
file_handler = next(h for h in logger.handlers if getattr(h, 'name', '') == 'file')

LAYOUT_FILE = Path("config/layout.dpgini")
#Initial data
x_data = [i for i in range(10)]
y0_data = [random.random() for _ in range(10)]
y1_data = [random.random() for _ in range(10)]

plot_frozen = False # global, only appropriate for single-file GUI

def update_plot_data():
    global plot_frozen

    if plot_frozen:
        return
    # Simulate new data
    new_x = x_data[-1] + 1
    new_y0 = random.random()
    new_y1 = random.random()
    x_data.append(new_x)
    y0_data.append(new_y0)
    y1_data.append(new_y1)

    # Keep a fixed window of data for scrolling effect  
    if len(x_data) > 20:  
        x_data.pop(0)  
        y0_data.pop(0)
        y1_data.pop(0)  

    # Update the actual plot
    dpg.set_value("dynamic_line_series0", [x_data, y0_data])
    dpg.set_value("dynamic_line_series1", [x_data, y1_data])
    dpg.fit_axis_data("plot_2D_x_axis")  # <- if you tag your x axis
    dpg.fit_axis_data("plot_2D_y_axis")  # <- if you tag your y axis

def periodic_update():
    update_plot_data()
    dpg.set_frame_callback(dpg.get_frame_count() + 6, periodic_update)  # ≈100ms if ~60fps

def save_layout_callback():
    dpg.save_init_file(str(LAYOUT_FILE))
    print(f"Layout saved to {LAYOUT_FILE}")


def set_handler_level(handler, level_name):
    level = getattr(logging, level_name.upper(), None)
    if level is None:
        dpg.log_error(f"Invalid level: {level_name}")
        return
    handler.setLevel(level)
    #dpg.log_info(f"Set {handler.name} handler level to {level_name}")
    logger.info(f"Set {handler.name} handler level to {level_name}")

def on_console_level_change(sender, data):
    set_handler_level(console_handler, dpg.get_value(sender))

def on_file_level_change(sender, data):
    set_handler_level(file_handler, dpg.get_value(sender))

def freeze_plot_callback():
    global plot_frozen
    plot_frozen = True
    logger.info("Plot frozen")
    dpg.set_value("thaw_status", "Plot frozen")

def unfreeze_plot_callback():
    global plot_frozen
    plot_frozen = False
    logger.info("Plot unfrozen")
    dpg.set_value("thaw_status", "Plot unfrozen")

def save_plot_to_png_callback_dead():
    filename = "media/plot_output.png"
    dpg.export_image("plot_2D", filename=filename)
    logger.info(f"Plot saved to {filename}")
    dpg.set_value("status_text", f"Plot saved to {filename}")
    
def save_plot_to_png_callback_fail():
    #filename = f"plot_capture_{int(time.time())}.png"
    filename = "media/plot_output.png"
    dpg.take_screenshot(filename=filename)
    print(f"Viewport screenshot saved to: {filename}")

def save_plot_to_png_callback_nope():
    # Create a unique filename
    filename = f"plot_snapshot_{dpg.get_frame_count()}.png"
    # Render plot widget to an image file
    try:
        dpg.capture_item("plot_2D", filename=filename)
        print(f"Plot saved to: {filename}")
    except Exception as e:
        print(f"Failed to save plot: {e}")

def save_plot_to_png_callback(sender, app_data, user_data):
    filename = "media/plot_output.svg"
    plotsvg(data_dictdict, title = "Plot 2D", filename=filename)
    logger.info(f"Plot saved to {filename}")
    dpg.set_value("status_text", f"Plot saved to {filename}")


dpg.create_context()  # <<<<< This is required before windows/widgets


# Enable docking globally for the viewport
dpg.configure_app(docking=True, docking_space=True)
# Load layout if it exists
if LAYOUT_FILE.exists():
    dpg.configure_app(init_file=str(LAYOUT_FILE), load_init_file=True)
    
with dpg.window(label = "Logging Settings"):
    dpg.add_text("Adjust log levels dynamically")
    
    dpg.add_combo(label="Console Log Level", items=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default_value=logging.getLevelName(console_handler.level),
            callback=on_console_level_change)
            
    dpg.add_combo(label="File Log Level", items=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default_value=logging.getLevelName(file_handler.level),
            callback=on_file_level_change)
        
with dpg.window(label="2D Plot Viewport", width=600, height=400):
    dpg.add_text("", tag="thaw_status")
    with dpg.plot(label="Simple 2D Plot", tag = "plot_2D", height=300, width=500):
        dpg.add_plot_legend()
        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="X Axis", tag = "plot_2D_x_axis")
        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Y Axis", tag = "plot_2D_y_axis")
        
        # Example line series data
        #x_data = [0, 1, 2, 3, 4, 5]
        #y0_data = [0, 1, 4, 9, 16, 25]
        dpg.add_line_series(x_data, y0_data, label="Y0", tag="dynamic_line_series0", parent=y_axis)
        dpg.add_line_series(x_data, y1_data, label="Y1", tag="dynamic_line_series1", parent=y_axis)

        # Initialize the plot series  
        dpg.set_value("dynamic_line_series0", [x_data, y0_data])
        dpg.set_value("dynamic_line_series1", [x_data, y1_data])
    dpg.add_button(label="Freeze", callback=freeze_plot_callback)
    dpg.add_button(label="Unfreeze", callback=unfreeze_plot_callback)
    dpg.add_button(label="Save Chart to PNG", callback=save_plot_to_png_callback)
    dpg.add_button(label = "Copy Values For Spreadsheet Pasting")
    dpg.add_button(label = "Adjust Time")
    dpg.add_button(label = "Adjust Queries")

with dpg.viewport_menu_bar():
    with dpg.menu(label="File"):
        dpg.add_menu_item(label="Save Layout", callback=save_layout_callback)
        dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())



# Set up a timer to update the plot every 100ms
dpg.set_frame_callback(dpg.get_frame_count() + 6, periodic_update)

dpg.create_viewport(title='Pipeline', width=1100, height=550)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()




