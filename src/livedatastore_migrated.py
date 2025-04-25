'''
Title: ingestion.py (borrowed from MaxOps)
Author: Clayton Bennett
Created: 05 March 2025
'''

from pathlib import Path
import csv
import json
import toml
from datetime import datetime, timedelta
from app.directories import Directories


def ensure_dir():
    # Ensure the export directory exists
    if not Directories.EXPORT_DIR_INTERMEDIATE.exists():
        Directories.EXPORT_DIR_INTERMEDIATE.mkdir(parents=True)

def local_save_data_overview_hourly(data: dict):
    save_data_to_csv(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "overview_hourly_data.csv")
    save_data_to_json(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "overview_hourly_data.json")
    save_data_to_toml(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "overview_hourly_data.toml")

def local_save_data_daily(data: dict):
    save_data_to_csv(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "daily_data.csv")
    save_data_to_json(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "daily_data.json")
    save_data_to_toml(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "daily_data.toml")

def local_save_data_outfall_daily(data: dict):
    save_data_to_csv(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "outfall_daily_data.csv")
    save_data_to_json(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "outfall_daily_data.json")
    save_data_to_toml(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "outfall_daily_data.toml")

def local_save_data_bod_daily(data: dict):
    save_data_to_csv(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "bod_daily_data.csv")
    save_data_to_json(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "bod_daily_data.json")
    save_data_to_toml(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "bod_daily_data.toml")

def local_save_data_basin_clarifier_hourly(data: dict):
    save_data_to_csv(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "basin_clarifier_hourly_data.csv")
    save_data_to_json(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "basin_clarifier_hourly_data.json")
    save_data_to_toml(data, file_path = Directories.EXPORT_DIR_INTERMEDIATE / "basin_clarifier_hourly_data.toml")

def save_data_to_csv(data: dict, file_path):
    """Save hourly data to a CSV file."""
    ensure_dir()

    # Write or append to the CSV file
    with open(file_path, mode="a+", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Write the header if the file is empty
        if file_path.stat().st_size == 0:
            writer.writerow([key for key in data.keys()])
        else:
            
            # check if existing headers/keys match data.keys()
            csvfile.seek(0)
            reader = csv.reader(csvfile)
            try:
                column_headers = next(reader)
                if column_headers == list(data.keys()):
                    print("The existing CSV column names match data.keys()")
                else:
                    print("\nWARNING: The existing CSV column names DO NOT match data.keys()")
                    print("\n\tKeys have changed in an existing CSV export file. \n\tOpen and read the relevant CSV export file. \n\tCheck the creation date of the file. \n\tIf possible delete the file and let a new one be generated\n")
                    ## Write a row of the altered column names
                    writer.writerow([key for key in data.keys()])

            except StopIteration:
                print("ERROR: The file appears to be empty, but stat() reported otherwise.")
                        # Write the data
        write_dict(writer, data)
    print(f"Data saved to {file_path}")
    
def write_dict(writer, data):
    """
    Writes all keys and values from a dictionary to a CSV file using the writer object.
    
    Args:
        writer: A csv.writer object.
        data: A dictionary containing key-value pairs to write.
    """
    writer.writerow([value for key, value in data.items()])

def save_data_to_json(data: dict, file_path):
    """Save hourly data to a JSON file."""
    ensure_dir()

    # Append the data to the JSON file
    if file_path.exists():
        with open(file_path, mode="r+", encoding="utf-8") as jsonfile:
            existing_data = json.load(jsonfile)
            existing_data.append(data)
            jsonfile.seek(0)
            json.dump(existing_data, jsonfile, indent=4)
    else:
        with open(file_path, mode="w", encoding="utf-8") as jsonfile:
            json.dump([data], jsonfile, indent=4)

    print(f"Data saved to {file_path}")

def save_data_to_toml(data: dict, file_path):
    """
    Save hourly data to a TOML file.

    Parameters:
        data (dict): Dictionary containing hourly data fields such as
                     'timestamp', 'flow_rate', 'cod', and 'water_quality'.

    Example data:
        {
            "timestamp": "2025-03-05T13:00:00",
            "flow_rate": 120.5,
            "cod": 38.1,
            "water_quality": "good"
        }
    """
    ensure_dir()
    # Load existing data from the TOML file if it exists
    existing_data = {}
    if file_path.exists():
        with open(file_path, mode="r", encoding="utf-8") as tomlfile:
            existing_data = toml.load(tomlfile)

    # Add the new entry to the existing data
    if "overview_hourly_data" not in existing_data:
        existing_data["overview_hourly_data"] = []
    existing_data["overview_hourly_data"].append(data)

    # Save the updated data back to the TOML file
    with open(file_path, mode="w", encoding="utf-8") as tomlfile:
        toml.dump(existing_data, tomlfile)

    print(f"Data saved to {file_path}")
    
def log_export_operation(message: str):
    """Log operations in export.log."""
    file_path = Directories.EXPORT_DIR_INTERMEDIATE / "export.log"
    with open(file_path, mode="a", encoding="utf-8") as logfile:
        logfile.write(f"{message}\n")

def list_export_files():
    """
    Lists all files in the export directory.

    Returns:
        list: A list of file names in the export directory.
    """
    if EXPORT_DIR.exists() and EXPORT_DIR.is_dir():
        # Return a list of file names (not paths) in the directory
        return [file.name for file in EXPORT_DIR.iterdir() if file.is_file()]
    return []  # Return an empty list if the directory doesn't exist or is empty

def clear_export_directory():
    """
    Clears all files in the export directory.

    Returns:
        bool: True if the files were successfully deleted, False if the directory does not exist.
    """
    if EXPORT_DIR.exists() and EXPORT_DIR.is_dir():
        try:
            # Iterate through and delete each file in the directory
            for file in EXPORT_DIR.iterdir():
                if file.is_file():
                    file.unlink()  # Delete the file
            return True  # Return True when the directory is successfully cleared
        except Exception as e:
            print(f"Error clearing export directory: {e}")  # Handle unexpected errors
            return False
    return False  # Return False if the directory does not exist

def nowtime():
    now_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    return now_time
    
def time_minus_one_day(time_str = nowtime()):
    time_datetime = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
    # Subtract a day using timedelta
    yesterday_datetime = time_datetime - timedelta(days=1)
    # Format the result back to the original format
    return yesterday_datetime.strftime("%Y-%m-%dT%H:%M:%S")

def time_minus_one_hour(time_str = nowtime()):
    time_datetime = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
    # Subtract a day using timedelta
    yesterhour_datetime = time_datetime - timedelta(hours=1)
    # round down to the top of the hour, for clarity 
    yesterhour_datetime = yesterhour_datetime.replace(minute=0, second=0, microsecond=0)
    # Format the result back to the original format
    return yesterhour_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    
def time_plus_one_day(time_str = nowtime()):
    time_datetime = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
    # Subtract a day using timedelta
    yesterday_datetime = time_datetime + timedelta(days=1)
    # Format the result back to the original format
    return yesterday_datetime.strftime("%Y-%m-%dT%H:%M:%S")

def time_plus_one_hour(time_str = nowtime()):
    time_datetime = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
    # Subtract a day using timedelta
    yesterhour_datetime = time_datetime + timedelta(hours=1)
    # round down to the top of the hour, for clarity 
    yesterhour_datetime = yesterhour_datetime.replace(minute=0, second=0, microsecond=0)
    # Format the result back to the original format
    return yesterhour_datetime.strftime("%Y-%m-%dT%H:%M:%S")

def expected_length(timestamp):
    long_enogh_to_be_in_ISO_time = (len(timestamp)>=16) # "%Y-%m-%dT%H:%M:%S" or "%Y-%m-%dT%H:%M"
    short_enough_to_be_an_hour = (len(timestamp)<=2) # 14
    return  long_enogh_to_be_in_ISO_time or short_enough_to_be_an_hour

def special_word(timestamp):
    return timestamp.strip()=="now"

# === Command: Sanitize Time ===
def sanitize_time(timestamp):
    #print(f"timestamp = {timestamp}")
    #print(f"bool = {timestamp=='now'}")
    # Check and handle the timestamp, if it has minutes but not seconds
    if not(expected_length(timestamp)) and not(special_word(timestamp)):
        raise ValueError("Invalid time value.")
    try:
        # Attempt to parse the timestamp with the "%Y-%m-%dT%H:%M" format (up to minutes)
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")
        print(f"Original timestamp is valid (up to minutes): {timestamp}")
        
        # Add ":00" for seconds if it doesn't have them
        if len(timestamp) == 16:  # Length for "%Y-%m-%dT%H:%M"
            timestamp = f"{timestamp}:00"
            print(f"Updated timestamp with seconds: {timestamp}")
    except ValueError:
        pass
    try:
        # Check if the formatted string is already ISO 8601
        # Parse the string back to a datetime object to validate it
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
        iso8601 = True
    except:
        iso8601 = False

    if iso8601:
        return timestamp
    elif timestamp == "now" or timestamp is None:
        # overwrite
        #print("timestamp is 'now', attempting to assign..")
        print(f"timestamp 'now' assigned as {timestamp}.")
        return nowtime()
    
    else: 
        try:
            # convert string from args.timestamp to an integer
            # This will fail is there are non-numeric characters in the string.
            return time_hour_explicit(int(float(timestamp))) 
        except Exception as e:
            print(f"A legimate time value was not offered. Null used: {e}")
        
def time_hour_explicit(hour_int):
    if hour_int<=24:
        # Assume today. Convert time to a rounded hour
        #now_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        now = datetime.now()
        timestamp = datetime(year = now.year,
                                month = now.month,
                                day = now.day,
                                hour = hour_int,
                                minute = 0,
                                second = 0).strftime("%Y-%m-%dT%H:%M:%S")
        
        return timestamp
    else:
        return False
    
def is_valid_number(value):
    """Helper function to validate numeric input."""
    if value == "":
        return True  # Allow empty string for None
    try:
        float(value)
        return True
    except ValueError:
        return False
def check_values_float(input_value):
    if input_value == "":
        return None
    elif not is_valid_number(input_value):
        raise ValueError("Non-numeric values entered.")
    else:
        return float(input_value)
        
def load_json(filepath):
    # Load JSON data from the file
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data