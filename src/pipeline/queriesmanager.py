import os
import toml
from datetime import datetime
import json
import csv
from collections import defaultdict
import logging

from src.pipeline import helpers
from src.pipeline.time_manager import TimeManager

logger = logging.getLogger(__name__)
'''
Goal:
Set up to use the most recent query:
use-most-recently-edited-query-file = true # while true, this will ignore the files variable list and instead use a single list of the most recent files
'''

class QueriesManager:
    def __init__(self, workspace_manager: object):
        self.workspace_manager = workspace_manager
        logger.info(f"QueriesManager using project: {self.workspace_manager.workspace_name}")
        if not workspace_manager:
            raise ValueError("workspace_manager must be provided and not None.")
        self.workspace_manager = workspace_manager

    
    def load_tracking(self):
        file_path = self.workspace_manager.get_timestamp_success_file_path()
        try:
            #logger.info({"Trying to load tracking file at": file_path})
            logger.info({
                "event": "Loading tracking file",
                "path": str(file_path)
            })
            data = helpers.load_json(file_path)
            #logger.info({"Tracking data loaded": data})
            logger.info({
                "event": "Tracking data loaded",
                "data": data
            })

            return data
        except FileNotFoundError:
            return {}
        
    def save_tracking(self,data):
        file_path = self.workspace_manager.get_timestamp_success_file_path()
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_most_recent_successful_timestamp(self, api_id) -> int:
        print("QueriesManager.get_most_recent_successful_timestamp()")
        from pipeline.helpers import load_toml
        try:
            config = load_toml(self.workspace_manager.get_configuration_file_path())
            timezone_config = config["settings"]["timezone"]
        except:
            timezone_config = "America/Chicago"
            
        data = self.load_tracking()
        
        if not data:
            # No stored value found — go back one hour from now, rounded down to nearest 5 minutes
            one_hour_ago_local = TimeManager.now().as_unix() - 3600  # now - 1 hour in unix seconds
            one_hour_ago_local = TimeManager(one_hour_ago_local).as_datetime()
            #one_hour_ago_utc = TimeManager.from_local(one_hour_ago_local, zone_name = timezone_config)
            tm = TimeManager(one_hour_ago_local).round_down_to_nearest_five()
        else:
            # Stored value found — parse ISO timestamp and round down to nearest 5 minutes
            last_success_iso = TimeManager(data[api_id]["timestamps"]["last_success"]).as_datetime()
            #last_success_utc = TimeManager.from_local(last_success_iso, zone_name = timezone_config).as_datetime()
            tm = TimeManager(last_success_iso).round_down_to_nearest_five()
            
        return tm

    
    def update_success(self,api_id,success_time=None):
        # This should be called when data is definitely transmitted to the target API. 
        # A confirmation algorithm might be in order, like calling back the data and checking it against the original.
        data = self.load_tracking()
        if api_id not in data:
            data[api_id] = {"timestamps": {}}
        #now = success_time or datetime.now().isoformat()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data[api_id]["timestamps"]["last_success"] = now
        data[api_id]["timestamps"]["last_attempt"] = now
        self.save_tracking(data)

    def update_attempt(self, api_id):
        data = self.load_tracking()
        if api_id not in data:
            logger.info(f"Creating new tracking entry for {api_id}")
            data[api_id] = {"timestamps": {}}
        #now = datetime.now().isoformat()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data[api_id]["timestamps"]["last_attempt"] = now
        self.save_tracking(data)
        logger.info(f"Updated last_attempt for {api_id}: {now}")

def load_query_rows_from_csv_files(csv_paths_list):
    queries_dictlist_unfiltered = []
    for csv_path in csv_paths_list:
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                queries_dictlist_unfiltered.append(row)
    return queries_dictlist_unfiltered

def group_queries_by_api_url(queries_array,grouping_var_str='zd'):
    queries_array_grouped = defaultdict(list)
    for row in queries_array:
        api_id = row[grouping_var_str] 
        queries_array_grouped[api_id].append(row)
    return queries_array_grouped

if __name__ ==  "__main__":
    pass



