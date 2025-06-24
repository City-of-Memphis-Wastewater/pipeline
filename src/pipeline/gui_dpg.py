import logging
from dearpygui import dearpygui as dpg
from pathlib import Path

# Setup logging as usual
import src.pipeline.logging_setup as logging_setup
logging_setup.setup_logging()
logger = logging.getLogger()
console_handler = next(h for h in logger.handlers if getattr(h, 'name', '') == 'console')
file_handler = next(h for h in logger.handlers if getattr(h, 'name', '') == 'file')

LAYOUT_FILE = Path("config/layout.dpgini")

def save_layout_callback():
    dpg.save_init_file(str(LAYOUT_FILE))
    print(f"Layout saved to {LAYOUT_FILE}")

def set_handler_level(handler, level_name):
    level = getattr(logging, level_name.upper(), None)
    if level is None:
        dpg.log_error(f"Invalid level: {level_name}")
        return
    handler.setLevel(level)
    dpg.log_info(f"Set {handler.name} handler level to {level_name}")

def on_console_level_change(sender, data):
    set_handler_level(console_handler, dpg.get_value(sender))

def on_file_level_change(sender, data):
    set_handler_level(file_handler, dpg.get_value(sender))

if __name__ == "__main__":
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
        with dpg.plot(label="Simple 2D Plot", tag = "plot_2D", height=300, width=500):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="X Axis")
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Y Axis")
            
            # Example line series data
            x_data = [0, 1, 2, 3, 4, 5]
            y_data = [0, 1, 4, 9, 16, 25]
            dpg.add_line_series(x_data, y_data, label="y = x^2", parent=y_axis)

    with dpg.viewport_menu_bar():
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="Save Layout", callback=save_layout_callback)
            dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())

    dpg.create_viewport(title='Pipeline', width=1100, height=450)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
