# pipeline/daemon/controller.py
import schedule, time, datetime, sys, os
from threading import Thread
from projects.eds_to_rjn.scripts import collector, storage, aggregator
from projects.eds_to_rjn.scripts.main import get_eds_maxson_token_and_headers, get_rjn_tokens_and_headers
from pipeline.env import SecretsYaml
from pipeline.projectmanager import ProjectManager
from pipeline.queriesmanager import QueriesManager
from pipeline.call import test_connection_to_internet

STATUS_FILE = "daemon_status.txt"
RUNNING_FLAG = "pipeline/daemon/daemon_running.flag"

def log_status(message: str):
    print(message)
    with open(STATUS_FILE, "a") as f:
        f.write(f"{datetime.datetime.now()}: {message}\n")

def run_live_cycle():
    log_status("Running live cycle...")
    project_name = 'eds_to_rjn'
    try:
        test_connection_to_internet()
        pm = ProjectManager(project_name)
        config = SecretsYaml.load_config(pm.get_configs_file_path("secrets.yaml"))
        qm = QueriesManager(pm)
        query_files = qm.get_query_file_paths()
        log_status(f"Using query file(s): {query_files}")
        eds_api, headers = get_eds_maxson_token_and_headers(config)

        for path in query_files:
            data = collector.collect_live_values(path, eds_api, "Maxson", headers)
            storage.store_live_values(data, pm.get_aggregate_dir() + "/live_data.csv")
    except Exception as e:
        log_status(f"Live cycle error: {e}")

def run_hourly_cycle():
    log_status("Running hourly cycle...")
    project_name = 'eds_to_rjn'
    try:
        pm = ProjectManager(project_name)
        config = SecretsYaml.load_config(pm.get_configs_file_path("secrets.yaml"))
        rjn_api, headers = get_rjn_tokens_and_headers(config)
        aggregator.aggregate_and_send(
            data_file=pm.get_aggregate_dir() + "/live_data.csv",
            checkpoint_file=pm.get_aggregate_dir() + "/sent_data.csv",
            rjn_base_url=rjn_api.config['url'],
            headers_rjn=headers
        )
    except Exception as e:
        log_status(f"Hourly cycle error: {e}")

def setup_schedules():
    now = datetime.datetime.now()
    next_run = now + datetime.timedelta(minutes=5 - now.minute % 5)
    schedule.every().day.at(next_run.strftime("%H:%M")).do(run_live_cycle)
    schedule.every(5).minutes.do(run_live_cycle)
    schedule.every().hour.at(":00").do(run_hourly_cycle)

def run_daemon():
    if os.path.exists(RUNNING_FLAG):
        log_status("Daemon already running.")
        return
    with open(RUNNING_FLAG, "w") as f:
        f.write("running")

    log_status("Daemon started.")
    setup_schedules()
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        log_status(f"Fatal error: {e}")
    finally:
        stop_daemon()

def stop_daemon():
    if os.path.exists(RUNNING_FLAG):
        os.remove(RUNNING_FLAG)
        log_status("Daemon stopped.")
    else:
        log_status("No daemon to stop.")

def daemon_status():
    return os.path.exists(RUNNING_FLAG)

def main_cli(command):
    if command == "-start":
        Thread(target=run_daemon).start()
    elif command == "-stop":
        stop_daemon()
    elif command == "-status":
        print("RUNNING" if daemon_status() else "STOPPED")
    else:
        print("Usage: python -m pipeline.daemon -start | -stop | -status")
