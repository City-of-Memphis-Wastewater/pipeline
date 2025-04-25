'''
Title: ingestion.py
Author: Clayton Bennett
Created: 13 March 2025

Purpose: Take all raw submissions and convert to hourly structured submissions.
Provide a template to be filled.
'''
import numpy as np
import pandas as pd
import json
import toml
from datetime import datetime
#import schedule
import time
import pprint
from collections import defaultdict, OrderedDict
from app.directories import Directories


def convert_timestamps(data):
    """Converts timestamp strings to datetime objects."""
    for entry in data:
        if 'timestamp_entry_ISO' in entry and entry['timestamp_entry_ISO'] is not None:
            entry['timestamp_entry_ISO'] = datetime.strptime(entry['timestamp_entry_ISO'], "%Y-%m-%dT%H:%M:%S")
        if 'timestamp_intended_ISO' in entry and entry['timestamp_intended_ISO'] is not None:
            entry['timestamp_intended_ISO'] = datetime.strptime(entry['timestamp_intended_ISO'], "%Y-%m-%dT%H:%M:%S")
        if 'timestamp_ISO' in entry and entry['timestamp_ISO'] is not None:
            #print(f"entry = {entry}")
            entry['timestamp_ISO'] = datetime.strptime(entry['timestamp_ISO'], "%Y-%m-%dT%H:%M:%S")
    return data

def group_by_hour_most_recent_non_null_(data):
    """Groups data by hour, keeps the most recent values, and includes a list of all operators."""
    hourly_data = defaultdict(lambda: {'operators': []})
    for entry in data:
        if entry['timestamp_entry_ISO'] is not None:
            hour = entry['timestamp_entry_ISO'].replace(minute=0, second=0, microsecond=0)
            # Add operator to the list of operators, including null values and emtpy strings
            if 'operator' in entry:
                hourly_data[hour]['operators'].append(entry['operator'])
            
            # Store the most recent non-null entry for each hour
            # Key null values if there are no others for the key, so that all keys are passed
            if hour not in hourly_data:
                hourly_data[hour] = {key: None for key in entry.keys()}  # Ensure all keys are initialized
                hourly_data[hour].update(entry)
            else:
                for key, value in entry.items():
                    if entry[key] is not None or hourly_data[hour].get(key) is None:
                        hourly_data[hour][key] = entry[key]
    # Convert the defaultdict to a regular list of dictionaries
    result = []
    for hour, data in hourly_data.items():
        data['timestamp_ISO'] = hour.isoformat()
        data.pop('timestamp_entry_ISO', None)
        data.pop('timestamp_intended_ISO', None)
        data.pop('source', None)
        data.pop('operator', None)
        result.append(data)
    return result

def group_by_hour_most_recent_non_null(data):
    """
    Groups data by hour, keeps the most recent non-null values, and includes a list of all operators.
    """
    # Convert the data to a Pandas DataFrame
    df = pd.DataFrame(data)

    # Ensure timestamp_entry_ISO is a datetime object
    df['timestamp_entry_ISO'] = pd.to_datetime(df['timestamp_entry_ISO'], errors='coerce')

    # Create an hour column by rounding down the timestamps to the hour
    df['hour'] = df['timestamp_intended_ISO'].dt.floor('h')

    # Group by hour
    df = df.groupby('hour', as_index=False).apply(
        lambda group: pd.Series({
            **{col: group[col].dropna().iloc[-1] if not group[col].dropna().empty else None for col in group.columns},
            'operators': list(group['operator'])
        })
    )
    # Cleanup - reset index and drop unnecessary columns
    # Reorder the dictionary
    # data = {'timestamp_ISO': data.pop('timestamp_ISO'), **data}  # new order
    
    # Specify the column to prioritize
    column_to_move_to_beginning = "timestamp_ISO"

    # Reorder the columns
    df['timestamp_ISO'] = df['hour'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    df = df.drop(columns=['hour', 'timestamp_entry_ISO', 'timestamp_intended_ISO', 'source', 'operator'], errors='ignore')
    df = df[[column_to_move_to_beginning] + [col for col in df.columns if col != column_to_move_to_beginning]]
    df = df.reset_index(drop=True)
    df = df.replace({pd.NA: None, np.nan: None})
    # Convert the result back to a list of dictionaries
    return df.to_dict(orient='records')

def group_by_hour_collapsed(data):
    """
    Groups data by hour, keeps a list of all values for each key, and adds the timesamp_ISO key to represent the rounded down hour.
    """
    # Convert the data to a Pandas DataFrame
    df = pd.DataFrame(data)

    # Ensure timestamp_entry_ISO is a datetime object
    df['timestamp_entry_ISO'] = pd.to_datetime(df['timestamp_entry_ISO'], errors='coerce')

    # Create an hour column by rounding down the timestamps to the hour
    df['hour'] = df['timestamp_intended_ISO'].dt.floor('h')

    # Group by hour
    df = df.groupby('hour', as_index=False).apply(
        lambda group: pd.Series({
            str(key+"s"): list(group[key]) for key in group.columns  # Dynamically generate keys from columns
        })
        )
        # Specify the column to prioritize
    column_to_move_to_beginning = "timestamp_ISO"

    # Reorder the columns
    df['timestamp_ISO'] = df['hour'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    df = df.drop(columns=['hour', 'timestamp_entry_ISO', 'timestamp_intended_ISO', 'source', 'operator'], errors='ignore')
    df = df.drop(columns=['hours'], errors='ignore')
    df = df[[column_to_move_to_beginning] + [col for col in df.columns if col != column_to_move_to_beginning]]
    df = df.reset_index(drop=True)
    df = df.replace({pd.NA: None, np.nan: None})
    return df.to_dict(orient='records')

def check_for_Timestamp(data):
    for i,d in enumerate(data):
        print(i,d)


def serialize_datetimes(data):
    """Converts datetime objects back to strings."""
    for entry in data:
        if 'timestamp_ISO' in entry:
            #print(f"'timestamp_ISO' in entry")
            if isinstance(entry['timestamp_ISO'], datetime):
                #print(f"isinstance(entry['timestamp_ISO'], datetime) == True")
                entry['timestamp_ISO'] = entry['timestamp_ISO'].isoformat()
            else:
                pass
                #print(type(entry['timestamp_ISO']))
                #print(entry['timestamp_ISO'])
            
        if 'timestamp_intended_ISO' in entry:
            #print(f"'timestamp_intended_ISO' in entry")
            if isinstance(entry['timestamp_intended_ISO'], datetime):
                entry['timestamp_intended_ISO'] = entry['timestamp_intended_ISO'].isoformat()

        if 'timestamp_entry_ISO' in entry:
            #print(f"'timestamp_entry_ISO' in entry")
            if isinstance(entry['timestamp_entry_ISO'], datetime):
                entry['timestamp_entry_ISO'] = entry['timestamp_entry_ISO'].isoformat()

        if 'timestamp_ISOs' in entry:
            #print(f"'timestamp_ISOs' in entry")
            if isinstance(entry['timestamp_ISOs'], datetime):
                #print(f"isinstance(entry['timestamp_ISOs'], datetime) == True")
                entry['timestamp_ISOs'] = entry['timestamp_ISOs'].isoformat()
            else:
                pass
                #print(type(entry['timestamp_ISOs']))
                #print(entry['timestamp_ISOs'])
        if 'timestamp_intended_ISOs' in entry:
            #print(f"'timestamp_intended_ISOs' in entry")
            if isinstance(entry['timestamp_intended_ISOs'], datetime):
                entry['timestamp_intended_ISOs'] = entry['timestamp_intended_ISOs'].isoformat()
            elif isinstance(entry['timestamp_intended_ISOs'], list):
                for i,e in enumerate(entry['timestamp_intended_ISOs']):
                    entry['timestamp_intended_ISOs'][i] = entry['timestamp_intended_ISOs'][i].isoformat()
                #print(entry['timestamp_intended_ISOs'])
            else:
                pass
                #print(type(entry['timestamp_intended_ISOs']))
                #print(entry['timestamp_intended_ISOs'])
        if 'timestamp_entry_ISOs' in entry:
            #print(f"'timestamp_entry_ISOs' in entry")
            if isinstance(entry['timestamp_entry_ISOs'], datetime):
                entry['timestamp_entry_ISOs'] = entry['timestamp_entry_ISOs'].isoformat()
            elif isinstance(entry['timestamp_entry_ISOs'], list):
                for i,e in enumerate(entry['timestamp_entry_ISOs']):
                    entry['timestamp_entry_ISOs'][i] = entry['timestamp_entry_ISOs'][i].isoformat()
                #print(entry['timestamp_entry_ISOs'])
            else:
                pass
                #print(type(entry['timestamp_entry_ISOs']))
                #print(entry['timestamp_entry_ISOs'])
    return data

def save_to_json(data, filename):
    """Saves the structured data to a JSON file."""
    # Convert datetime objects to strings
    data = serialize_datetimes(data)
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def save_to_toml(data, filename):
    """Saves the structured data to a JSON file."""
    # Convert datetime objects to strings
    data = serialize_datetimes(data)
    with open(filename, 'w') as file:
        toml.dump(data, file)

class IntermediateExport:
    dict_intermediate_export_objects = None
    @classmethod
    def make_dict_intermediate_export_objects(cls):
        cls.dict_intermediate_export_objects = {}
    @classmethod
    def update_dict_intermediate_export_objects(cls,
                                                key,
                                                filename_semistructured,
                                                filename_collapsed,
                                                filename_structured):
            ie_o = IntermediateExport(
                key,
                filename_semistructured = filename_semistructured,
                filename_collapsed = filename_collapsed,
                filename_structured = filename_structured)

            cls.dict_intermediate_export_objects.update({key:ie_o})

    def __init__(self,key,filename_semistructured,filename_collapsed,filename_structured):
        self.key = key
        self.filename_semistructured = filename_semistructured
        self.filename_collapsed = filename_collapsed
        self.filename_structured = filename_structured

    @staticmethod
    def load_intermediate_export_data(intermediate_export_filename):
        # Load JSON data from the file
        with open(intermediate_export_filename, 'r') as file:
            loaded_intermediate_data = json.load(file)
            # Convert timestamps to datetime objects
            loaded_intermediate_data = convert_timestamps(loaded_intermediate_data)
        return loaded_intermediate_data

    @staticmethod
    def ingest_data_to_structured_hourly_single(key,loaded_intermediate_data,structured_export_filename):
        hourly_data_most_recent = group_by_hour_most_recent_non_null(loaded_intermediate_data)
        #hourly_data_collapsed = group_by_hour_collapsed(loaded_intermediate_data)
        
        save_to_json(hourly_data_most_recent, structured_export_filename)

        basename = structured_export_filename.name
        basename_toml = basename.replace(".json",".toml") 
        toml_file = structured_export_filename.with_name(basename_toml)
        #save_to_toml(hourly_data_most_recent, toml_file)

        print(f"Ingestion to structure complete for {key}.")

    @staticmethod
    def ingest_data_to_collapsed_hourly_list(key,loaded_intermediate_data, collapsed_export_filename):
        hourly_data_collapsed = group_by_hour_collapsed(loaded_intermediate_data) # comparable to overview-hourly-form=
        #check_for_Timestamp(hourly_data_collapsed)
        save_to_json(hourly_data_collapsed, collapsed_export_filename)
        basename = collapsed_export_filename.name
        basename_toml = basename.replace(".json",".toml") 
        toml_file = collapsed_export_filename.with_name(basename_toml)
        #save_to_toml(hourly_data_collapsed, toml_file)
        print(f"Ingestion to collapsed export complete for {key}.")
        
    @staticmethod
    def scheduled_run():
        # Schedule the ingestion to run every hour
        intermediate_export_filenames_hourly = (Directories.EXPORT_DIR_INTERMEDIATE /"basin_clarifier_hourly_data.json", Directories.EXPORT_DIR_INTERMEDIATE /"overview_hourly_data.json")
        intermediate_export_filenames_hourly = (Directories.EXPORT_DIR_INTERMEDIATE /"overview_hourly_data.json")
        structured_export_filename = Directories.EXPORT_DIR_INTERMEDIATE /'structured_data.json'
        for f in intermediate_export_filenames_hourly:
            #print(f)
            schedule.every().hour.do(ingest_data(f,structured_export_filename))

        print("Scheduler started. Ingestion will run every hour.")

        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)

    @staticmethod
    def run_now():
        # Run ingestion now
        # how can i find all instances of a class in python
        IntermediateExport.make_dict_intermediate_export_objects()
        IntermediateExport.update_dict_intermediate_export_objects(
            key = "basin_clarifier_hourly",
            filename_semistructured = Directories.EXPORT_DIR_INTERMEDIATE / "basin_clarifier_hourly_data.json",
            filename_collapsed = Directories.EXPORT_DIR_COLLAPSED / "basin_clarifier_hourly_collapsed_data.json",
            filename_structured = Directories.EXPORT_DIR_STRUCTURED / 'basin_clarifier_hourly_structured_data.json'
            )
        IntermediateExport.update_dict_intermediate_export_objects(
            key = "overview_hourly",
            filename_semistructured = Directories.EXPORT_DIR_INTERMEDIATE / "overview_hourly_data.json",
            filename_collapsed = Directories.EXPORT_DIR_COLLAPSED / "overview_hourly_collapsed_data.json",
            filename_structured = Directories.EXPORT_DIR_STRUCTURED / 'overview_hourly_structured_data.json'
            )
        IntermediateExport.update_dict_intermediate_export_objects(
            key = "outfall_daily",
            filename_semistructured = Directories.EXPORT_DIR_INTERMEDIATE / "outfall_daily_data.json",
            filename_collapsed = Directories.EXPORT_DIR_COLLAPSED / "outfall_daily_collapsed_data.json",
            filename_structured = Directories.EXPORT_DIR_STRUCTURED / 'outfall_daily_structured_data.json'
            )
        IntermediateExport.update_dict_intermediate_export_objects(
            key = "bod_daily",
            filename_semistructured = Directories.EXPORT_DIR_INTERMEDIATE / "bod_daily_data.json",
            filename_collapsed = Directories.EXPORT_DIR_COLLAPSED / "bod_daily_collapsed_data.json",
            filename_structured = Directories.EXPORT_DIR_STRUCTURED / 'bod_daily_structured_data.json'
            )
        for ie_o in IntermediateExport.dict_intermediate_export_objects.values():
            #ingest_data_to_structure(ie_o.filename_semistructured,ie_o.filename_structured)
            loaded_intermediate_data = IntermediateExport.load_intermediate_export_data(ie_o.filename_semistructured)
            IntermediateExport.ingest_data_to_structured_hourly_single(ie_o.key,loaded_intermediate_data,ie_o.filename_structured)
            IntermediateExport.ingest_data_to_collapsed_hourly_list(ie_o.key,loaded_intermediate_data,ie_o.filename_collapsed)
            print(f"{ie_o.filename_semistructured} ingested to {ie_o.filename_structured}")
        
if __name__ == "__main__":
    IntermediateExport.scheduled_run()

"""
Other values that are calculated:
RAS
Underflow
RAS = underflow- total WAS
"""