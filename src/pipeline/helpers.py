import json
import toml
from datetime import datetime
import inspect
import types
import os
import logging

logger = logging.getLogger(__name__)


def load_json(filepath):
    if not os.path.exists(filepath):
        logger.warning(f"[load_json] File not found: {filepath}")
        return {}

    if os.path.getsize(filepath) == 0:
        logger.warning(f"[load_json] File is empty: {filepath}")
        return {}

    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"[load_json] Failed to decode JSON in {filepath}: {e}")
        return {}


def load_toml(filepath):
    # Load TOML data from the file
    with open(filepath, 'r') as f:
        dic_toml = toml.load(f)
    return dic_toml

def round_datetime_to_nearest_past_five_minutes(dt: datetime) -> datetime:
    #print(f"dt = {dt}")
    allowed_minutes = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    # Find the largest allowed minute <= current minute
    rounded_minute = max(m for m in allowed_minutes if m <= dt.minute)
    return dt.replace(minute=rounded_minute, second=0, microsecond=0)

def get_now_time_rounded() -> int:
    nowtime = round_datetime_to_nearest_past_five_minutes(datetime.now())
    print(f"rounded nowtime = {nowtime}")
    nowtime =  int(nowtime.timestamp())+300
    return nowtime

def function_view(globals_passed=None):
    # Use the calling frame to get info about the *caller* module
    caller_frame = inspect.stack()[1].frame
    if globals_passed is None:
        globals_passed = caller_frame.f_globals

    # Get filename → basename only (e.g., 'calls.py')
    filename = os.path.basename(caller_frame.f_code.co_filename)

    print(f"Functions defined in {filename}:")

    for name, obj in list(globals_passed.items()):
        if isinstance(obj, types.FunctionType):
            if getattr(obj, "__module__", None) == globals_passed.get('__name__', ''):
                print(f"  {name}")
    print("\n")

def get_nested_config(dct: dict, keys: list[str]):
    """Retrieve nested dict value by keys list; raise KeyError with full path if missing."""
    current = dct
    for key in keys:
        try:
            current = current[key]
        except KeyError as e:
            full_path = " -> ".join(keys)
            raise KeyError(f"Missing required configuration at path: {full_path}") from e
    return current

def human_readable(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")

def iso(ts):
    return datetime.fromtimestamp(ts).isoformat()


if __name__ == "__main__":
    function_view()
    get_now_time_rounded()