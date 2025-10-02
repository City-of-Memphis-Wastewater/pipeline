import os
import json
import logging.config
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9


def setup_logging(config_file="config/logging.json"): # relative to root
    if not os.path.exists("logs"):
        os.makedirs("logs")
    with open(config_file, 'r') as f:
        config = json.load(f)
        logging.config.dictConfig(config) 

# Dynamically set logging level, per handler, like when using a GUI
#def set_handler_level(handler_name: str, level_name: str):
def set_handler_level(handler_name, level_name):
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
    
# Custom JSON formatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(log_record, indent=4)
    
class PrettyJSONFormatter(logging.Formatter):
    def format(self, record):
        if isinstance(record.msg, (dict, list)):
            try:
                record.msg = json.dumps(record.msg, indent=2, ensure_ascii=False)
            except Exception:
                pass  # fallback to default formatting
        return super().format(record)