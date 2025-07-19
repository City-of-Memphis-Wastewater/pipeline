# main.py (or __main__.py)
from datetime import datetime
import csv
import sys
from pathlib import Path

from src.pipeline.time_manager import TimeManager


# Add the root project path so that 'src' can be found
ROOT = Path(__file__).resolve().parents[2]  # pipeline/projects/eds_to_rjn/scripts -> pipeline
sys.path.insert(0, str(ROOT))

from src.pipeline.env import SecretConfig
from src.pipeline.api.eds import EdsClient
from src.pipeline.api.rjn import RjnClient
from src.pipeline.calls import test_connection_to_internet
from src.pipeline import helpers

from src.pipeline.projectmanager import ProjectManager
from src.pipeline.api.rjn import RjnClient 


from ..code import collector, sanitizer
from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url


import logging

logging.basicConfig(level=logging.DEBUG)  # or INFO, WARNING, ERROR

logger = logging.getLogger()
logger.setLevel(logging.INFO)  

def main():
    sketch_daemon_runner_main()

def sketch_daemon_runner_main():
    #from . import daemon_runner
    from projects.eds_to_rjn.scripts import daemon_runner
    daemon_runner.main()

def sketch_maxson():
    test_connection_to_internet()

    project_name = 'eds_to_rjn' # project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    queries_file_path_list = project_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    logger.debug(f"queries_file_path_list = {queries_file_path_list}")
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list)
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered,'zd')
    secrets_dict = SecretConfig.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    sessions = {}

    api_secrets_m = helpers.get_nested_config(secrets_dict, ["eds_apis", "Maxson"])
    session_maxson = EdsClient.login_to_session(api_url = api_secrets_m["url"],
                                      username = api_secrets_m["username"],
                                      password = api_secrets_m["password"])
    session_maxson.custom_dict = api_secrets_m
    sessions.update({"Maxson":session_maxson})

    api_secrets_r = helpers.get_nested_config(secrets_dict, ["contractor_apis","RJN"])
    
    session_rjn = RjnClient.login_to_session(api_url = api_secrets_r["url"],
                                       client_id = api_secrets_r["client_id"],
                                       password = api_secrets_r["password"])
    if session_rjn is not None:
        session_rjn.custom_dict = api_secrets_r
        sessions.update({"RJN":session_rjn})
    else:
        logger.warning("RJN session not established. Skipping RJN-related data transmission.")
    #for key, session in sessions.items():
    key = "Maxson"
    session = sessions[key] 

    queries_dictlist_filtered_by_session_key = queries_defaultdictlist_grouped_by_session_key.get(key,[])
    # queries_plus_responses_filtered_by_session_key should probably be  nested dictionaries rather than flattened rows, with keys for discerning source (localquery vs EDS vs RJN)
    queries_plus_responses_filtered_by_session_key = collector.collect_live_values(session, queries_dictlist_filtered_by_session_key) # This returns everything known plus everything recieved. It is glorious. It is complete. It is not sanitized.
    data_sanitized_for_printing = sanitizer.sanitize_data_for_printing(queries_plus_responses_filtered_by_session_key)
    data_sanitized_for_aggregated_storage = sanitizer.sanitize_data_for_aggregated_storage(queries_plus_responses_filtered_by_session_key)

    for row in data_sanitized_for_aggregated_storage:
        EdsClient.print_point_info_row(row)

        #print(f"queries_dictlist_filtered_by_session_key = {queries_dictlist_filtered_by_session_key}")
        #print(f"queries_plus_responses_filtered_by_session_key = {queries_plus_responses_filtered_by_session_key}")

        # Process timestamp
        
        #for row in queries_plus_responses_filtered_by_session_key:
    
        dt = datetime.fromtimestamp(row["ts"])
        tm = TimeManager(dt).round_down_to_nearest_five()
        timestamp_str = tm.as_formatted_date_time()
    
        # Send data to RJN
        
        RjnClient.send_data_to_rjn2(
            session_rjn,
            base_url = session_rjn.custom_dict["url"],
            project_id=row["rjn_projectid"],
            entity_id=row["rjn_entityid"],
            timestamps=[timestamp_str],
            values=[round(row["value"], 5)]
        )


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "default"

    if cmd == "sketch":
        sketch_maxson()
    elif cmd == "daemon_runner":
        sketch_daemon_runner_main()
    else:
        print("Usage options: \n"
        "poetry run python -m projects.eds_to_rjn.scripts.main daemon_runner \n"
        "poetry run python -m projects.eds_to_rjn.scripts.main sketch")
