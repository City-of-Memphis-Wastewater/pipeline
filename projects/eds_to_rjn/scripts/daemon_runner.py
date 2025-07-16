#projects/eds_to_rjndaemon_runner.py
import schedule, time
import logging
import datetime
from ..code import collector, storage, aggregator, sanitizer
from src.pipeline.api.eds import EdsClient
from src.pipeline.api.rjn import RjnClient
from src.pipeline import helpers
#from .main import get_rjn_tokens_and_headers
from src.pipeline.env import SecretsYaml
from src.pipeline.projectmanager import ProjectManager
from src.pipeline.queriesmanager import QueriesManager
from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url
logger = logging.getLogger(__name__)

def run_live_cycle():
    logger.info("Running live cycle...")
    #test_connection_to_internet()  

    project_name = 'eds_to_rjn' # project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    sessions = {}

    try:
        api_secrets = secrets_dict["eds_apis"]["Maxson"]
    except KeyError as e:
        raise KeyError(f"Missing required configuration for eds_apis['Maxson']: {e}")


    session_maxson = EdsClient.login_to_session(api_url = api_secrets["url"],
                                      username = api_secrets["username"],
                                      password = api_secrets["password"])
    
    session_maxson.custom_dict = api_secrets
    sessions.update({"Maxson":session_maxson})

    ## inject this code for testing

    api_secrets_r = helpers.get_nested_config(secrets_dict, ["contractor_apis","RJN"])
    
    session_rjn = RjnClient.login_to_session(api_url = api_secrets_r["url"],
                                       client_id = api_secrets_r["client_id"],
                                       password = api_secrets_r["password"])
    if session_rjn is not None:
        session_rjn.custom_dict = api_secrets_r
        sessions.update({"RJN":session_rjn})
    else:
        logger.warning("RJN session not established. Skipping RJN-related data transmission.")
    
    queries_file_path_list = project_manager.get_default_query_file_paths_list()
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list)
    #print(f"queries_dictlist_unfiltered = {queries_dictlist_unfiltered}")
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered,'zd')
    #print(f"queries_defaultdictlist_grouped_by_session_key = {queries_defaultdictlist_grouped_by_session_key}")
    #for key, session in sessions.items():
    key = "Maxson"
    session = sessions[key] 

    queries_dictlist_filtered_by_session_key = queries_defaultdictlist_grouped_by_session_key.get(key,[])        
    data = collector.collect_live_values(session, queries_dictlist_filtered_by_session_key) # need a way to for the eds_api method refernce to land on the other end
    #print(f"data = {data}")
    if len(data)==0:
        print("No data retrieved via collector.collect_live_values(). Skipping storage.store_live_values()")
    else:
        storage.store_live_values(data, project_manager.get_aggregate_dir() / "live_data.csv") # project_manager.get_live_data_csv_file

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
    #queries_plus_responses_filtered_by_session_key should probably be  nested dictionaries rather than flattened rows, with keys for discerning source (localquery vs EDS vs RJN)
    queries_plus_responses_filtered_by_session_key = collector.collect_live_values(session, queries_dictlist_filtered_by_session_key) # This returns everything known plus everything recieved. It is glorious. It is complete. It is not sanitized.
    #data_sanitized_for_printing = sanitizer.sanitize_data_for_printing(queries_plus_responses_filtered_by_session_key)
    data_sanitized_for_aggregated_storage = sanitizer.sanitize_data_for_aggregated_storage(queries_plus_responses_filtered_by_session_key)
    
    point_list = [row['iess'] for row in queries_defaultdictlist_grouped_by_session_key.get(key,[])]

    # Discern the time range to use
    starttime = queries_manager.get_most_recent_successful_timestamp(api_id=key)
    endtime = helpers.get_now_time()

    api_url = session.custom_dict["url"]
    request_id = EdsClient.create_tabular_request(session, api_url, starttime, endtime, points=point_list)
    EdsClient.wait_for_request_execution_session(session, api_url, request_id)
    results = EdsClient.get_tabular_mod(session, request_id, point_list)
    #session.post(api_url + 'logout', verify=False)
    if session_rjn is not None:
        for row in data_sanitized_for_aggregated_storage:
            EdsClient.print_point_info_row(row)

            #print(f"queries_dictlist_filtered_by_session_key = {queries_dictlist_filtered_by_session_key}")
            #print(f"queries_plus_responses_filtered_by_session_key = {queries_plus_responses_filtered_by_session_key}")

            # Process timestamp
            
            #for row in queries_plus_responses_filtered_by_session_key:
            dt = datetime.datetime.fromtimestamp(row["ts"])
            rounded_dt = helpers.round_time_to_nearest_five_minutes(dt)
            timestamp = rounded_dt
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
            # Send data to RJN
            
            RjnClient.send_data_to_rjn2(
                session_rjn,
                base_url = session_rjn.custom_dict["url"],
                project_id=row["rjn_siteid"],
                entity_id=row["rjn_entityid"],
                timestamps=[timestamp_str],
                values=[round(row["value"], 2)]
            )
    else:
        logger.warning("Skipping RJN transmission loop — session_rjn not established.")

def other():
    from src.pipeline.queriesmanager import QueriesManager
    from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url
    
    project_name = 'eds_to_rjn' # project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    queries_manager = QueriesManager(project_manager)
    queries_file_path_list = project_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # you can edit your queries files here
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered,'zd')
    logger.debug(f"queries_file_path_list = {queries_file_path_list}")

    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list)
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered,'zd')
    
    ## Establish `sessions` dictonary to hold the various authenticated sessions.
    ## `sessions` is not a key-ring; it's a door-ring.
    ## It tells you all the doors it already knows the keys too.
    ## I used the variable `sessions` to capture the multiplicity potention of singular instance objects of the `requests.Session` class.
    sessions = {}

    secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    

    api_secrets_m = helpers.get_nested_config(secrets_dict, ["eds_apis", "Maxson"])
    session_maxson = EdsClient.login_to_session(api_url = api_secrets_m["url"],
                                      username = api_secrets_m["username"],
                                      password = api_secrets_m["password"])
    session_maxson.custom_dict = api_secrets_m
    sessions.update({"Maxson":session_maxson})

    #secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    api_secrets_r = helpers.get_nested_config(secrets_dict, ["contractor_apis","RJN"])
    
    session_rjn = RjnClient.login_to_session(api_url = api_secrets_r["url"],
                                       client_id = api_secrets_r["client_id"],
                                       password = api_secrets_r["password"])
    if session_rjn is not None:
        session_rjn.custom_dict = api_secrets_r
        sessions.update({"RJN":session_rjn})
    else:
        logger.warning("RJN session not established. Skipping RJN-related data transmission.")

    for key, session in sessions.items():
        # Discern which queries to use
        point_list = [row['iess'] for row in queries_defaultdictlist_grouped_by_session_key.get(key,[])]

        # Discern the time range to use
        starttime = queries_manager.get_most_recent_successful_timestamp(api_id=key)
        endtime = helpers.get_now_time()

        api_url = session.custom_dict["url"]
        request_id = EdsClient.create_tabular_request(session, api_url, starttime, endtime, points=point_list)
        EdsClient.wait_for_request_execution_session(session, api_url, request_id)
        results = EdsClient.get_tabular_mod(session, request_id, point_list)
        session.post(api_url + 'logout', verify=False)
        #queries_manager.update_success(api_id=key) # not appropriate here in demo without successful transmission to 3rd party API

        for idx, iess in enumerate(point_list):
            print('\n{} samples:'.format(iess))
            for s in results[idx]:
                print('{} {} {}'.format(datetime.datetime.fromtimestamp(s[0]), round(s[1],2), s[2]))
def run_hourly_cycle_defunt(): 
    print("Running hourly cycle...")
    project_name = 'eds_to_rjn' # project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    
    ## Establish `sessions` dictonary to hold the various authenticated sessions.
    ## `sessions` is not a key-ring; it's a door-ring.
    ## It tells you all the doors it already knows the keys too.
    ## I used the variable `sessions` to capture the multiplicity potention of singular instance objects of the `requests.Session` class.
    sessions = {}

    secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    
    api_secrets_m = helpers.get_nested_config(secrets_dict, ["eds_apis", "Maxson"])
    session_maxson = EdsClient.login_to_session(api_url = api_secrets_m["url"],
                                      username = api_secrets_m["username"],
                                      password = api_secrets_m["password"])
    session_maxson.custom_dict = api_secrets_m
    sessions.update({"Maxson":session_maxson})

    #secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    api_secrets_r = helpers.get_nested_config(secrets_dict, ["contractor_apis","RJN"])
    
    session_rjn = RjnClient.login_to_session(api_url = api_secrets_r["url"],
                                       client_id = api_secrets_r["client_id"],
                                       password = api_secrets_r["password"])
    if session_rjn is not None:
        session_rjn.custom_dict = api_secrets_r
        sessions.update({"RJN":session_rjn})
    else:
        logger.warning("RJN session not established. Skipping RJN-related data transmission.")
    
    
    #rjn_api, headers_rjn = get_rjn_tokens_and_headers(secrets_dict)
    #
    aggregator.aggregate_and_send(session_rjn=session_rjn,
                                  data_file = project_manager.get_aggregate_dir() / "live_data.csv",
                                  checkpoint_file = project_manager.get_aggregate_dir() / "sent_data.csv"
                                  )
    
def run_hourly_cycle_manual(): 
    print("Running RJN upload, with manual file slection ...")
    project_name = 'eds_to_rjn' # project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    print("project_manager, created.")
    print("secrets_file_path, established.")
    secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    print("secrets_dict, created.")
    #rjn_api, headers_rjn = get_rjn_tokens_and_headers(secrets_dict)
    #

    ## Establish `sessions` dictonary to hold the various authenticated sessions.
    ## `sessions` is not a key-ring; it's a door-ring.
    ## It tells you all the doors it already knows the keys too.
    ## I used the variable `sessions` to capture the multiplicity potention of singular instance objects of the `requests.Session` class.
    sessions = {}

    secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    
    api_secrets_m = helpers.get_nested_config(secrets_dict, ["eds_apis", "Maxson"])
    session_maxson = EdsClient.login_to_session(api_url = api_secrets_m["url"],
                                      username = api_secrets_m["username"],
                                      password = api_secrets_m["password"])
    session_maxson.custom_dict = api_secrets_m
    sessions.update({"Maxson":session_maxson})

    #secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    api_secrets_r = helpers.get_nested_config(secrets_dict, ["contractor_apis","RJN"])
    
    session_rjn = RjnClient.login_to_session(api_url = api_secrets_r["url"],
                                       client_id = api_secrets_r["client_id"],
                                       password = api_secrets_r["password"])
    logger.info(f"session_rjn = {session_rjn}")
    if session_rjn is not None:
        session_rjn.custom_dict = api_secrets_r
        sessions.update({"RJN":session_rjn})
    else:
        logger.warning("RJN session not established. Skipping RJN-related data transmission.")

    print("rjn_api & headers_rjn, created.")
    str(input("Would you like to manually declare the "))
    data_file_manual = str(input("CSV filepath (like live_data.csv), paste: "))
    data_file_auto = project_manager.get_aggregate_dir() / "live_data.csv",
    aggregator.aggregate_and_send(session_rjn = session_rjn,
                                  data_file = project_manager.get_aggregate_dir() / "live_data.csv", 
                                  #data_file = data_file_manual, # uncommented to choose to use the CLI input query.
                                  checkpoint_file = project_manager.get_aggregate_dir() / "sent_data.csv",
                                  #checkpoint_file = ""
                                  )
    
def defunct_setup_schedules():

    print("projects\eds_to_rjn\scripts\daemon_runner.py")
    # Get current time and round it to the next multiple of 5 minutes
    now = datetime.datetime.now()
    minutes_to_next_five = 5 - (now.minute % 5)
    next_run_time = now + datetime.timedelta(minutes=minutes_to_next_five)

    # Schedule the first run at the next multiple of 5 minutes
    schedule.every().day.at(next_run_time.strftime("%H:%M")).do(run_live_cycle)
    schedule.every(5).minutes.do(run_live_cycle)
    schedule.every().hour.at(":00").do(run_hourly_cycle)

def setup_schedules_defunct():
    print("projects\eds_to_rjn\scripts\daemon_runner.py")
    now = datetime.datetime.now()

    # Calculate how many minutes to the next 5-minute mark (05, 10, 15, etc.)
    minutes_to_next_five = 5 - (now.minute % 5)
    
    # Schedule the first task to run at the next 5-minute mark (e.g., hh:05:00, hh:10:00, ...)
    first_run_time = now + datetime.timedelta(minutes=minutes_to_next_five)
    first_run_time_str = first_run_time.strftime("%H:%M")
    
    # Schedule tasks to run every 5 minutes at the "hh:05, hh:10, hh:15, etc."
    schedule.every().day.at(first_run_time_str).do(run_live_cycle)  # First run time
    schedule.every(5).minutes.do(run_live_cycle)  # After first run, every 5 minutes
    
    # Log the next scheduled task
    print(f"Next live cycle scheduled at: {first_run_time_str}")

def setup_schedules():
    testing = True
    if not testing:
        schedule.every().hour.do(run_hourly_tabular_trend_eds_to_rjn)
    else:
        schedule.every().second.do(run_hourly_tabular_trend_eds_to_rjn)
        #schedule.every().min.do(run_hourly_tabular_trend_eds_to_rjn)

def main():
    print(f"Starting daemon_runner at {datetime.datetime.now()}...")
    #logging.info("Daemon started and running...")
    setup_schedules()
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "default"

    if cmd == "main":
        main()
    elif cmd == "live":
        run_live_cycle()
    elif cmd == "hourly":
        run_hourly_cycle()
    elif cmd == "start_hourly_eds_to_rjn" or cmd == "sher":
        run_hourly_tabular_trend_eds_to_rjn()
    else:
        print("Usage options: \n"
        "poetry run python -m projects.eds_to_rjn.scripts.daemon_runner main # ; [main] (sher) *currently* \n"
        "poetry run python -m projects.eds_to_rjn.scripts.daemon_runner live \n"
        #"poetry run python -m projects.eds_to_rjn.scripts.daemon_runner hourly \n"
        "poetry run python -m projects.eds_to_rjn.scripts.daemon_runner sher # ; [sher] (start_hourly_eds_to_rjn)")
