#workspaces/eds_to_rjn/scripts/daemon_runner.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
# import schedule # not used - now we use Microsoft Task Scheduler # left here for reference. (was 1.2.2 at time of poetry remove, schedule==1.2.2 ; python_version >= "3.8" and python_version < "3.15")
import time
import logging
import csv
from datetime import datetime

from pipeline.api.eds import EdsClient, identify_relevant_tables
from pipeline.api.rjn import RjnClient
from pipeline import helpers
from pipeline.env import SecretConfig
from pipeline.workspace_manager import WorkspaceManager
from pipeline.queriesmanager import QueriesManager
from pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_col
from pipeline.time_manager import TimeManager
from pipeline.security_and_config import SecurityAndConfig

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#def save_tabular_trend_data_to_log_file(project_id, entity_id, endtime: int, workspace_manager, timestamps: list[int], values: list[float]):
def save_tabular_trend_data_to_log_file(project_id, entity_id, endtime, workspace_manager, timestamps, values):
    ### save file for log
    timestamps_str = [TimeManager(ts).as_formatted_date_time() for ts in timestamps]
    endtime_iso = TimeManager(endtime).as_safe_isoformat_for_filename()
    filename = f"rjn_data_{project_id}_{entity_id}_{endtime_iso}.csv"
    log_dir = workspace_manager.get_logs_dir()
    filepath = log_dir / filename
    logger.info(f"filepath = {filepath}")

    with open(filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "value"])  # Header
        #for ts, val in zip(timestamps, values):
        for ts, val in zip(timestamps_str, values):
            writer.writerow([ts, val])
            
def run_hourly_tabular_trend_eds_to_rjn(test = False):


    #test_connection_to_internet()

    workspace_name = 'eds_to_rjn' # workspace_name = WorkspaceManager.identify_default_workspace_name()
    workspace_manager = WorkspaceManager(workspace_name)
    queries_manager = QueriesManager(workspace_manager)
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    logger.debug(f"queries_file_path_list = {queries_file_path_list}")

    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list)
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_col(queries_dictlist_unfiltered,'zd')
    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    sessions_eds = {}

    # --- Prepare Maxson session_eds
    base_url_maxson = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("url").rstrip("/")
    session_maxson = EdsClient.login_to_session(api_url = base_url_maxson,
                                                username = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("username"),
                                                password = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("password"))
    session_maxson.base_url = base_url_maxson
    session_maxson.zd = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("zd")
    sessions_eds.update({"Maxson":session_maxson})


    # --- Prepare Stiles session_eds
    try:
        # REST API access fails due to firewall blocking the port
        # So, alternatively, if this fails, encourage direct MariaDB access, with files at E:\SQLData\stiles\
        base_url_stiles = secrets_dict.get("eds_apis", {}).get("WWTP", {}).get("url").rstrip("/")
        session_stiles = EdsClient.login_to_session(api_url = base_url_stiles,
                                                    username = secrets_dict.get("eds_apis", {}).get("WWTP", {}).get("username"),
                                                    password = secrets_dict.get("eds_apis", {}).get("WWTP", {}).get("password"))
        session_stiles.base_url = base_url_stiles
        session_stiles.zd = secrets_dict.get("eds_apis", {}).get("WWTP", {}).get("zd")
        sessions_eds.update({"WWTP":session_stiles})
    except:
        session_stiles = None # possible reduntant for login_to_session() output 
    sessions_eds.update({"WWTF":session_stiles})

    base_url_rjn = secrets_dict.get("contractor_apis", {}).get("RJN", {}).get("url").rstrip("/")
    session_rjn = RjnClient.login_to_session(api_url = base_url_rjn,
                                    client_id = secrets_dict.get("contractor_apis", {}).get("RJN", {}).get("client_id"),
                                    password = secrets_dict.get("contractor_apis", {}).get("RJN", {}).get("password"))
    if session_rjn is None:
        logger.warning("RJN session not established. Skipping RJN-related data transmission.\n")
        if test is False:
            return
    else:
        logger.info("RJN session established successfully.")
        session_rjn.base_url = base_url_rjn
    
    # Discern the time range to use
    starttime = queries_manager.get_most_recent_successful_timestamp(api_id="RJN")
    logger.info(f"queries_manager.get_most_recent_successful_timestamp(), key = {'RJN'}")
    endtime = helpers.get_now_time_rounded(workspace_manager)
    starttime_ts = TimeManager(starttime).as_unix()
    endtime_ts = TimeManager(endtime).as_unix() 
    logger.info(f"starttime = {starttime}")
    logger.info(f"endtime = {endtime}")
    
    #key = "Maxson"
    #session = sessions_eds[key] 

    ## To do: start using pandas, for the sake of clarity of manipulation 15 Aug 2025
    for key_eds, session_eds in sessions_eds.items():
        point_list = [row['iess'] for row in queries_defaultdictlist_grouped_by_session_key.get(key_eds,[])]
        point_list_sid = [row['sid'] for row in queries_defaultdictlist_grouped_by_session_key.get(key_eds,[])]
        
        rjn_projectid_list = [row['rjn_projectid'] for row in queries_defaultdictlist_grouped_by_session_key.get(key_eds,[])]
        rjn_entityid_list = [row['rjn_entityid'] for row in queries_defaultdictlist_grouped_by_session_key.get(key_eds,[])]
        
        
        if session_eds is None and not EdsClient.this_computer_is_an_enterprise_database_server(secrets_dict, key_eds):
            logger.warning(f"Skipping EDS session for {key_eds} — session_eds is None and this computer is not an enterprise database server.")
            continue
        
        # Fallback, if API Access fails.
        if session_eds is None and EdsClient.this_computer_is_an_enterprise_database_server(secrets_dict, key_eds):
            relevant_tables = identify_relevant_tables(key_eds, starttime_ts, endtime_ts, secrets_dict)
            results = EdsClient.access_database_files_locally(key_eds, starttime_ts, endtime_ts, point=point_list_sid, tables=relevant_tables)
        else:
            api_url = session_eds.base_url
            request_id = EdsClient.create_tabular_request(session_eds, api_url, starttime_ts, endtime_ts, points=point_list)
            logger.info(f"request_id = {request_id}")
            EdsClient.wait_for_request_execution_session(session_eds, api_url, request_id)
            results = EdsClient.get_tabular_trend(session_eds, request_id, point_list)
            #results = EdsClient.get_tabular_mod(session_eds, request_id, point_list)
            session_eds.post(f'{api_url}/logout', verify=False)
        #print(f"len(results) = {len(results)}")
        
        for idx, iess in enumerate(point_list):
            #print(f"rows = {rows}")
            timestamps = []
            values = []
            entity_id = rjn_entityid_list[idx]
            project_id = rjn_projectid_list[idx]
            print(f"/nentity_id = {entity_id}")
            print(f"iess = {iess}")
            print(f"project_id = {project_id}")
            
            for row in results[idx]:
                #print(f"row = {row}")
                #EdsClient.print_point_info_row(row)

                dt = datetime.fromtimestamp(row["ts"])
                timestamp_str = helpers.round_datetime_to_nearest_past_five_minutes(dt).isoformat(timespec='seconds')
                #if row['quality'] == 'G':
                timestamps.append(timestamp_str)
                value = round(row["value"],5)
                # QUICK AND DIRTY CONVERSION FOR WWTF WETWELL LEVEL TO FEET 
                if iess == "M310LI.UNIT0@NET0":
                    value = (value/12)+181.25 # convert inches of wetwell to feet above mean sealevel
                values.append(value) # unrounded values fail to post

            logger.info(f"len(timestamps) = {len(timestamps)}")
            if len(timestamps)>0:
                logger.info(f"timestamps[0] = {timestamps[0]}")
                logger.info(f"timestamps[-1] = {timestamps[-1]}")
            else:
                logger.info(f"No timestamps retrieved. Transmission to RJN skipped for {iess}.")
            if timestamps and values:
            
                # Send data to RJN
                if not test:
                    rjn_data_transmission_succeeded = RjnClient.send_data_to_rjn(
                        session_rjn,
                        base_url = session_rjn.base_url,
                        entity_id = entity_id,
                        project_id = project_id,
                        timestamps=timestamps,
                        values=values
                    )
                
                    if rjn_data_transmission_succeeded:
                        queries_manager.update_success(api_id="RJN", success_time=endtime)
                        logger.info(f"RJN data transmission succeeded for entity_id {entity_id}, project_id {project_id}.")
                        save_tabular_trend_data_to_log_file(project_id, entity_id, endtime, workspace_manager,timestamps, values)
                else:
                    print("[TEST] RjnClient.send_data_to_rjn() skipped")
            
                    
def setup_schedules():
    """
    Defunct. Use Microsoft Task Scheduler to call iterative runs.
    """
    testing = False
    if not testing:
        schedule.every().hour.do(run_hourly_tabular_trend_eds_to_rjn)
    else:
        schedule.every().second.do(run_hourly_tabular_trend_eds_to_rjn)

def main():
    #logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    task_scheduler_is_ready_to_handle_hourly_task_scheduling = True
    if task_scheduler_is_ready_to_handle_hourly_task_scheduling:
        run_hourly_tabular_trend_eds_to_rjn()
    else:
        setup_schedules()

def start_daemon():
    """
    Defunct. Use Microsoft Task Scheduler to call iterative runs.
    """
    logging.info(f"Daemon started at {datetime.now()} and running...")
    setup_schedules()
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "default"

    if cmd == "main":
        main()
    elif cmd == "once":
        run_hourly_tabular_trend_eds_to_rjn()
    elif cmd == "test":
        run_hourly_tabular_trend_eds_to_rjn(test=True)
    else:
        print("Usage options: \n"
        "poetry run python -m workspaces.eds_to_rjn.scripts.daemon_runner main \n"
        "poetry run python -m workspaces.eds_to_rjn.scripts.daemon_runner once \n"
        "poetry run python -m workspaces.eds_to_rjn.scripts.daemon_runner test ")
