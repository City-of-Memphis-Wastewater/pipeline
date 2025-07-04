#projects/eds_to_rjndaemon_runner.py
import schedule, time
import logging
import datetime
from ..code import collector, storage, aggregator, sanitizer
from src.pipeline.api.eds import login_to_session # actually generalized beyond EDS
from .main import get_rjn_tokens_and_headers
from src.pipeline.env import SecretsYaml
from src.pipeline.projectmanager import ProjectManager
from src.pipeline.queriesmanager import QueriesManager
from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url

def run_live_cycle():
    logging.info("Running live cycle...")
    #test_connection_to_internet()  

    project_name = 'eds_to_rjn' # project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    sessions = {}

    try:
        api_secrets = secrets_dict["eds_apis"]["Maxson"]
    except KeyError as e:
        raise KeyError(f"Missing required configuration for eds_apis['Maxson']: {e}")


    session_maxson = login_to_session(api_url = api_secrets["url"],
                                      username = api_secrets["username"],
                                      password = api_secrets["password"])
    
    session_maxson.custom_dict = api_secrets
    sessions.update({"Maxson":session_maxson})
    
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
        storage.store_live_values(data, project_manager.get_aggregate_dir()+"\live_data.csv") # project_manager.get_live_data_csv_file

def run_hourly_cycle(): 
    print("Running hourly cycle...")
    project_name = 'eds_to_rjn' # project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    rjn_api, headers_rjn = get_rjn_tokens_and_headers(secrets_dict)
    #
    aggregator.aggregate_and_send(data_file = project_manager.get_aggregate_dir()+"\live_data.csv",
                                  checkpoint_file = project_manager.get_aggregate_dir()+"\sent_data.csv",
                                  rjn_base_url=rjn_api.config['url'],
                                  headers_rjn=headers_rjn)
    
def run_hourly_cycle_manual(): 
    print("Running RJN upload, with manual file slection ...")
    project_name = 'eds_to_rjn' # project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    print("project_manager, created.")
    print("secrets_file_path, established.")
    secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    print("secrets_dict, created.")
    rjn_api, headers_rjn = get_rjn_tokens_and_headers(secrets_dict)
    #
    print("rjn_api & headers_rjn, created.")
    data_file_manual = str(input("CSV filepath (like \live_data.csv), paste: "))
    aggregator.aggregate_and_send(data_file = data_file_manual,
                                  #checkpoint_file = project_manager.get_aggregate_dir()+"\sent_data.csv",
                                  checkpoint_file = "",
                                  rjn_base_url=rjn_api.config['url'],
                                  headers_rjn=headers_rjn)
    
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

def setup_schedules():
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
    else:
        print("Usage options: \n"
        "poetry run python -m projects.eds_to_rjn.scripts.daemon_runner main \n"
        "poetry run python -m projects.eds_to_rjn.scripts.daemon_runner live \n"
        "poetry run python -m projects.eds_to_rjn.scripts.daemon_runner hourly")
