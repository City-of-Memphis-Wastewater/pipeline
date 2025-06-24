import logging
from dearpygui.core import *
from dearpygui.simple import *

# Setup logging as usual
import src.pipeline.logging_setup as logging_setup
logging_setup.setup_logging()
logger = logging.getLogger()
console_handler = next(h for h in logger.handlers if getattr(h, 'name', '') == 'console')
file_handler = next(h for h in logger.handlers if getattr(h, 'name', '') == 'file')

def set_handler_level(handler, level_name):
    level = getattr(logging, level_name.upper(), None)
    if level is None:
        log_error(f"Invalid level: {level_name}")
        return
    handler.setLevel(level)
    log_info(f"Set {handler.name} handler level to {level_name}")

def on_console_level_change(sender, data):
    set_handler_level(console_handler, get_value(sender))

def on_file_level_change(sender, data):
    set_handler_level(file_handler, get_value(sender))

with window("Logging Settings"):
    add_text("Adjust log levels dynamically")
    add_combo("Console Log Level", items=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
              default_value=logging.getLevelName(console_handler.level),
              callback=on_console_level_change)
    add_combo("File Log Level", items=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
              default_value=logging.getLevelName(file_handler.level),
              callback=on_file_level_change)

start_dearpygui()
