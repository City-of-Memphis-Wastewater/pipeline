#workspaces/eds_to_rjndaemon_runner.py
import schedule, time
import logging
import csv
from datetime import datetime

from src.pipeline.api.eds import EdsClient, identify_relevant_tables
from src.pipeline.api.rjn import RjnClient
from src.pipeline import helpers
from src.pipeline.env import SecretConfig
from src.pipeline.workspace_manager import WorkspaceManager
from src.pipeline.queriesmanager import QueriesManager
from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url
from src.pipeline.time_manager import TimeManager

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

    workspace_name = 'eds_to_rjn' # workspace_name = WorkspaceManager.identify_default_workspace()
    workspace_manager = WorkspaceManager(workspace_name)
    queries_manager = QueriesManager(workspace_manager)
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    logger.debug(f"queries_file_path_list = {queries_file_path_list}")

    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list)
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered,'zd')
    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    sessions_eds = {}

    # --- Prepare Maxson session_eds
    api_secrets_m = helpers.get_nested_config(secrets_dict, ["eds_apis", "Maxson"])
    session_maxson = EdsClient.login_to_session(api_url = api_secrets_m["url"],
                                      username = api_secrets_m["username"],
                                      password = api_secrets_m["password"])
    session_maxson.custom_dict = api_secrets_m
    sessions_eds.update({"Maxson":session_maxson})


    # --- Prepare Stiles session_eds
    try:
        # REST API access fails due to firewall blocking the port
        # So, alternatively, if this fails, encourage direct MariaDB access, with files at E:\SQLData\stiles\
        api_secrets_s = helpers.get_nested_config(secrets_dict, ["eds_apis", "WWTF"])
        session_stiles = EdsClient.login_to_session(api_url = api_secrets_s["url"],
                                        username = api_secrets_s["username"],
                                        password = api_secrets_s["password"])
        session_stiles.custom_dict = api_secrets_s
    except:
        session_stiles = None # possible reduntant for login_to_session() output 
    sessions_eds.update({"WWTF":session_stiles})

    api_secrets_r = helpers.get_nested_config(secrets_dict, ["contractor_apis","RJN"])
    
    session_rjn = RjnClient.login_to_session(api_url = api_secrets_r["url"],
                                       client_id = api_secrets_r["client_id"],
                                       password = api_secrets_r["password"])
    if session_rjn is not None:
        session_rjn.custom_dict = api_secrets_r
    else:
        logger.warning("RJN session not established. Skipping RJN-related data transmission.\n")
    
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
        if session_eds is None and EdsClient.this_computer_is_an_enterprise_database_server(secrets_dict, key_eds):
            relevant_tables = identify_relevant_tables(key_eds, starttime_ts, endtime_ts, secrets_dict)
            results = EdsClient.access_database_files_locally(key_eds, starttime_ts, endtime_ts, point=point_list_sid, tables=relevant_tables)
        else:
            api_url = session_eds.custom_dict["url"]
            request_id = EdsClient.create_tabular_request(session_eds, api_url, starttime_ts, endtime_ts, points=point_list)
            EdsClient.wait_for_request_execution_session(session_eds, api_url, request_id)
            results = EdsClient.get_tabular_trend(session_eds, request_id, point_list)
            #results = EdsClient.get_tabular_mod(session_eds, request_id, point_list)
            session_eds.post(api_url + 'logout', verify=False)
        #print(f"len(results) = {len(results)}")
        
        for idx, iess in enumerate(point_list):
            #print(f"rows = {rows}")
            timestamps = []
            values = []
            entity_id = rjn_entityid_list[idx]
            project_id = rjn_projectid_list[idx]
            print(f"entity_id = {entity_id}")
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
                logger.info("No timestamps retrieved. Transmission to RJN skipped for this point.")
            if timestamps and values:
                
                base_url = api_secrets_r["url"]
                
                # Send data to RJN
                if not test:
                    rjn_data_transmission_succeeded = RjnClient.send_data_to_rjn2(
                        session_rjn,
                        base_url = base_url,
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
                    print("[TEST] RjnClient.send_data_to_rjn2() skipped")
            
                    
def setup_schedules():
    testing = False
    if not testing:
        schedule.every().hour.do(run_hourly_tabular_trend_eds_to_rjn)
    else:
        schedule.every().second.do(run_hourly_tabular_trend_eds_to_rjn)

def main():
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
