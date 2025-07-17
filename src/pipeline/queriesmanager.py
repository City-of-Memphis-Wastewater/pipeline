import os
import toml
from datetime import datetime
import json
import csv
from collections import defaultdict
import logging

from src.pipeline import helpers

logger = logging.getLogger(__name__)
'''
Goal:
Set up to use the most recent query:
use-most-recently-edited-query-file = true # while true, this will ignore the files variable list and instead use a single list of the most recent files
'''

class QueriesManager:
    def __init__(self, project_manager: object):
        self.project_manager = project_manager
        logger.info(f"QueriesManager using project: {self.project_manager.project_name}")
        if not project_manager:
            raise ValueError("project_manager must be provided and not None.")
        self.project_manager = project_manager

    
    def load_tracking(self):
        file_path = self.project_manager.get_timestamp_success_file_path()
        try:
            data = helpers.load_json(file_path)
            logger.info(f"Tracking data loaded: {data}")
            return data
        except FileNotFoundError:
            return {}
        
    def save_tracking(self,data):
        file_path = self.project_manager.get_timestamp_success_file_path()
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_most_recent_successful_timestamp(self,api_id):
        print("QueriesManager.get_most_recent_successful_timestamp()")
        data = self.load_tracking()
        if data == {}:
            # if no stored value is found, assume you will go back one hour
            from datetime import timedelta
            delta = int(helpers.round_time_to_nearest_five_minutes(timedelta(hours = 1).total_seconds()))
            starttime = helpers.get_now_time() - delta 
        else:
            # if a stored most-recent value is found, use it as the starttime for your a tabular trend request, etc.
            starttime = helpers.round_time_to_nearest_five_minutes(datetime.fromisoformat(data[api_id]["timestamps"]["last_success"]))
            starttime = int(starttime.timestamp())
        return starttime
    
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



