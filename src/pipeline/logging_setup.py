import os
import json
import logging.config

def setup_logging(config_file="config/logging.json"): # relative to root
    if not os.path.exists("logs"):
        os.makedirs("logs")
    with open(config_file, 'r') as f:
        config = json.load(f)
        logging.config.dictConfig(config)

# Dynamically set logging level, per handler, like when using a GUI
def set_handler_level(handler_name: str, level_name: str):
    logger = logging.getLogger()  # root logger
    level = getattr(logging, level_name.upper(), None)
    if level is None:
        raise ValueError(f"Invalid log level: {level_name}")
    
    for handler in logger.handlers:
        if handler.get_name() == handler_name:
            handler.setLevel(level)
            logging.info(f"Set {handler_name} handler level to {level_name}")
            break
    else:
        raise ValueError(f"Handler '{handler_name}' not found")