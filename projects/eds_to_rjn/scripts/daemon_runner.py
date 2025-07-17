#projects/eds_to_rjndaemon_runner.py
import schedule, time
import logging
from datetime import datetime

from src.pipeline.api.eds import EdsClient
from src.pipeline.api.rjn import RjnClient
from src.pipeline import helpers
from src.pipeline.env import SecretsYaml
from src.pipeline.projectmanager import ProjectManager
from src.pipeline.queriesmanager import QueriesManager
from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url

logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG)


def run_hourly_tabular_trend_eds_to_rjn():
    #test_connection_to_internet()

    project_name = 'eds_to_rjn' # project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    queries_manager = QueriesManager(project_manager)
    queries_file_path_list = project_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    logger.debug(f"queries_file_path_list = {queries_file_path_list}")

    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list)
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered,'zd')
    secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    #sessions_eds = {}

    api_secrets_m = helpers.get_nested_config(secrets_dict, ["eds_apis", "Maxson"])
    session_maxson = EdsClient.login_to_session(api_url = api_secrets_m["url"],
                                      username = api_secrets_m["username"],
                                      password = api_secrets_m["password"])
    session_maxson.custom_dict = api_secrets_m
    #sessions_eds.update({"Maxson":session_maxson})
    if False:
        api_secrets_s = helpers.get_nested_config(secrets_dict, ["eds_apis", "WWTP"])
        session_stiles = EdsClient.login_to_session(api_url = api_secrets_s["url"],
                                        username = api_secrets_s["username"],
                                        password = api_secrets_s["password"])
        session_stiles.custom_dict = api_secrets_s
        #sessions_eds.update({"WWTP":session_stiles})

    api_secrets_r = helpers.get_nested_config(secrets_dict, ["contractor_apis","RJN"])
    
    session_rjn = RjnClient.login_to_session(api_url = api_secrets_r["url"],
                                       client_id = api_secrets_r["client_id"],
                                       password = api_secrets_r["password"])
    if session_rjn is not None:
        session_rjn.custom_dict = api_secrets_r
    else:
        logger.warning("RJN session not established. Skipping RJN-related data transmission.")
    #for key, session in sessions_eds.items():

    key = "Maxson"
    #session = sessions_eds[key] 
    point_list = [row['iess'] for row in queries_defaultdictlist_grouped_by_session_key.get(key,[])]
    rjn_siteid_list = [row['rjn_siteid'] for row in queries_defaultdictlist_grouped_by_session_key.get(key,[])]
    rjn_entityid_list = [row['rjn_entityid'] for row in queries_defaultdictlist_grouped_by_session_key.get(key,[])]

    # Discern the time range to use
    starttime = queries_manager.get_most_recent_successful_timestamp(api_id="RJN")
    logger.info(f"queries_manager.get_most_recent_successful_timestamp(), key = {'RJN'}")
    logger.info(f"starttime = {starttime}")
    endtime = helpers.get_now_time()

    api_url = session_maxson.custom_dict["url"]
    request_id = EdsClient.create_tabular_request(session_maxson, api_url, starttime, endtime, points=point_list)
    EdsClient.wait_for_request_execution_session(session_maxson, api_url, request_id)
    results = EdsClient.get_tabular_trend(session_maxson, request_id, point_list)
    #results = EdsClient.get_tabular_mod(session_maxson, request_id, point_list)
    session_maxson.post(api_url + 'logout', verify=False)
    #print(f"len(results) = {len(results)}")
    
    for idx, rows in enumerate(results):
        #print(f"rows = {rows}")
        timestamps = []
        values = []
        entity_id = rjn_entityid_list[idx],
        project_id = rjn_siteid_list[idx],
        
        for row in rows:
            print(f"row = {row}")
            #EdsClient.print_point_info_row(row)

            dt = datetime.fromtimestamp(row["ts"])
            timestamp_str = helpers.round_time_to_nearest_five_minutes(dt).strftime('%Y-%m-%d %H:%M:%S')

            timestamps.append(timestamp_str)
            values.append(round(row["value"], 2))

        if timestamps and values:
            
            if session_rjn is not None:
                base_url = session_rjn.custom_dict["url"]
                
                # Send data to RJN
                print(f"row = {row}")
                rjn_data_transmission_succeeded = RjnClient.send_data_to_rjn2(
                    session_rjn,
                    base_url = session_rjn.custom_dict["url"],
                    entity_id = entity_id,
                    project_id = project_id,
                    timestamps=[timestamp_str],
                    values=[round(row["value"], 2)]
                )
                if rjn_data_transmission_succeeded:
                    queries_manager.update_success(api_id="RJN", success_time=endtime)
                
            else:
                logger.warning("Skipping RJN transmission loop — session_rjn not established.")
                queries_manager.update_attempt(api_id="RJN")  # Optional: track that an attempt happened
                logger.info(f"key = {'RJN'}")

def setup_schedules():
    testing = True
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
    else:
        print("Usage options: \n"
        "poetry run python -m projects.eds_to_rjn.scripts.daemon_runner main \n"
        "poetry run python -m projects.eds_to_rjn.scripts.daemon_runner once ")
