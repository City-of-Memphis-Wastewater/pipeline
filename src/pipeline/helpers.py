from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import json
import toml
from datetime import datetime
import inspect
import types
import os
import logging
import socket
import re
import zipfile
from pathlib import Path

from pipeline.time_manager import TimeManager

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

#def round_datetime_to_nearest_past_five_minutes(dt: datetime) -> datetime:
def round_datetime_to_nearest_past_five_minutes(dt):
    #print(f"dt = {dt}")
    allowed_minutes = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    # Find the largest allowed minute <= current minute
    rounded_minute = max(m for m in allowed_minutes if m <= dt.minute)
    return dt.replace(minute=rounded_minute, second=0, microsecond=0)

def get_now_time_rounded():# -> int:
    '''
    workspace_manager is (was) included here so that references can be made to the configured timezone
    '''
    logger.debug(f"helpers.get_now_time_rounded(workspace_manager)")
    nowtime = round_datetime_to_nearest_past_five_minutes(datetime.now())
    logger.debug(f"rounded nowtime = {nowtime}")
    nowtime_local =  int(nowtime.timestamp())+300
    nowtime_local = TimeManager(nowtime_local).as_datetime()
    if False:
        try:
            config = load_toml(workspace_manager.get_configuration_file_path())
            timezone_config = config["settings"]["timezone"]
        except:
            timezone_config = "America/Chicago"
        nowtime_utc = TimeManager.from_local(nowtime_local, zone_name = timezone_config).as_unix()
        logger.debug(f"return nowtime_utc")
        return nowtime_utc
    else:
        logger.debug(f"return nowtime_local")
        return TimeManager(nowtime_local).as_unix() # nowtime_utc

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


def check_if_zip(file_path: str | Path) -> bool:
    """Checks if the file at the given path is a valid ZIP archive."""
    try:
        return zipfile.is_zipfile(file_path)
    except Exception:
        # Handle cases where the path might be invalid, or other unexpected errors
        return False



def human_readable(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")

def iso(ts):
    return datetime.fromtimestamp(ts).isoformat()

def get_lan_ip_address_of_current_machine():
    """Get the LAN IP address of the current machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to be reachable; just picks the active interface
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()
        
def nice_step(delta_sec: int) -> int:
    """
    Return a "nice" step in seconds (1,2,5,10,15,30,60,120,...)
    """
    nice_numbers = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600, 7200, 14400, 28800, 86400]
    target_step = delta_sec // 400  # aim for ~400 points
    # find the smallest nice_number >= target_step
    for n in nice_numbers:
        if n >= target_step:
            return n
    return nice_numbers[-1]



def sanitize_date_input(date_str: str) -> str:
    '''Sanitize date input strings by adding spaces where needed, to overcome error in fuzzy date parsing by the pendulum library.'''
    # 1. Add space between letters and numbers
    date_str = re.sub(r'([A-Za-z])(\d)', r'\1 \2', date_str)
    # 2. Ensure a space after commas
    date_str = re.sub(r',\s*', ', ', date_str)
    # 3. Normalize multiple spaces
    date_str = re.sub(r'\s+', ' ', date_str).strip()
    return date_str
    
if __name__ == "__main__":
    function_view()
    # Example
    sanitize_date_input("December12,2024")  # -> "December 12,2024"
