from datetime import datetime
import logging
import requests
import time

from src.pipeline import helpers
from src.pipeline.decorators import log_function_call
from pprint import pprint

class EdsClient:

    @staticmethod
    def get_license(session,api_url:str):
        response = session.get(api_url + 'license', json={}, verify=False).json()
        return response

    @staticmethod
    def print_point_info_row_og(row):
        # use this when unpacking after bulk retrieval, not during retrieving
        try:
            print(f'''iess:{row["iess"]}, dt:{datetime.fromtimestamp(row["ts"])}, un:{row["un"]}, av:{round(row["value"],2)}, {row["shortdesc"]}''')
        except:
            print(f'''iess:{row["iess"]}, dt:{datetime.fromtimestamp(row["ts"])}, un:{row["un"]}, av:{round(row["value"],2)}''')

    @staticmethod
    def print_point_info_row(row):
        # Desired keys to print, with optional formatting
        keys_to_print = {
            "iess": lambda v: f"iess:{v}",
            "ts": lambda v: f"dt:{datetime.fromtimestamp(v)}",
            "un": lambda v: f"un:{v}",
            "value": lambda v: f"av:{round(v, 2)}",
            "shortdesc": lambda v: str(v),
        }

        parts = []
        for key, formatter in keys_to_print.items():
            try:
                parts.append(formatter(row[key]))
            except (KeyError, TypeError, ValueError):
                continue  # Skip missing or malformed values

        print(", ".join(parts))

    @staticmethod
    def get_points_live_mod(session, iess: str):
        # please make this session based rather than header based
        "Access live value of point from the EDS, based on zs/api_id value (i.e. Maxson, WWTF, Server)"
        api_url = str(session.custom_dict["url"]) 

        query = {
            'filters' : [{
            'iess': [iess],
            'tg' : [0, 1],
            }],
            'order' : ['iess']
            }
        response = session.post(api_url + 'points/query', json=query, verify=False).json()
        #print(f"response = {response}")
        
        if response is None:
            return None
        
        points_datas = response.get("points", [])
        if not points_datas:
            raise ValueError(f"No data returned for iess='{iess}': len(points) == 0")
        elif len(points_datas) != 1:
            raise ValueError(f"Expected exactly one point, got {len(points_datas)}")
        else:
            point_data = points_datas[0] # You expect exactly one point usually
            #print(f"point_data = {point_data}")
        return point_data  
    
    @staticmethod
    def get_tabular_mod(session, req_id, point_list):
        results = [[] for _ in range(len(point_list))]
        while True:
            api_url = session.custom_dict['url']
            response = session.get(f'{api_url}trend/tabular?id={req_id}', verify=False).json()
            for chunk in response:
                if chunk['status'] == 'TIMEOUT':
                    raise RuntimeError('timeout')

                for idx, samples in enumerate(chunk['items']):
                    results[idx] += samples
                    
                if chunk['status'] == 'LAST':
                    return results
    
    @staticmethod
    def get_points_export(session,iess_filter:str=''):
        api_url = session.custom_dict["url"]
        zd = session.custom_dict["zd"]
        order = 'iess'
        query = '?zd={}&iess={}&order={}'.format(zd, iess_filter, order)
        request_url = api_url + 'points/export' + query
        response = session.get(request_url, json={}, verify=False)
        #print(f"Status Code: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}, Body: {response.text[:500]}")
        decoded_str = response.text
        return decoded_str

    @staticmethod
    def save_points_export(decoded_str, export_file_path):
        lines = decoded_str.strip().splitlines()

        with open(export_file_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")  # Save each line in the text file
    
    @staticmethod
    def login_to_session(api_url, username, password):
        session = requests.Session()

        data = {'username': username, 'password': password, 'type': 'script'}
        response = session.post(api_url + 'login', json=data, verify=False).json()
        #print(f"response = {response}")
        session.headers['Authorization'] = 'Bearer ' + response['sessionId']
        return session
    
    @staticmethod
    def create_tabular_request(session, api_url, starttime, endtime, points):
        data = {
            'period': {
                'from': starttime, 
                'till': endtime, # must be of type int, like: int(datetime(YYYY, MM, DD, HH).timestamp()),
            },

            'step': 300, # five minutes
            'items': [{
                'pointId': {'iess': p},
                'shadePriority': 'DEFAULT',
                'function': 'AVG'
            } for p in points],
        }
        response = session.post(api_url + 'trend/tabular', json=data, verify=False).json()
        #print(f"response = {response}")
        return response['id']

    @staticmethod
    def wait_for_request_execution_session(session, api_url, req_id):
        st = time.time()
        while True:
            time.sleep(1)
            res = session.get(f'{api_url}requests?id={req_id}', verify=False).json()
            status = res[str(req_id)]
            if status['status'] == 'FAILURE':
                raise RuntimeError('request [{}] failed: {}'.format(req_id, status['message']))
            elif status['status'] == 'SUCCESS':
                break
            elif status['status'] == 'EXECUTING':
                print('request [{}] progress: {:.2f}\n'.format(req_id, time.time() - st))

        print('request [{}] executed in: {:.3f} s\n'.format(req_id, time.time() - st))


def fetch_eds_data_row(session, iess):
    point_data = EdsClient.get_points_live_mod(session, iess)
    return point_data

@log_function_call(level=logging.DEBUG) 
def _demo_eds_start_session_maxson():
    from src.pipeline.env import SecretsYaml
    from src.pipeline.projectmanager import ProjectManager
    project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)

    secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    sessions = {}

    api_secrets_m = helpers.get_nested_config(secrets_dict, ["eds_apis","Maxson"])
    session_maxson = EdsClient.login_to_session(api_url = api_secrets_m["url"],
                                                username = api_secrets_m["username"],
                                                password = api_secrets_m["password"])
    session_maxson.custom_dict = api_secrets_m
    sessions.update({"Maxson":session_maxson})

    # Show example of what it would be like to start a second session (though Stiles API port 43084 is not accesible at this writing)
    if False:
        session_stiles = EdsClient.login_to_session(api_url = secrets_dict["eds_apis"]["WWTF"]["url"] ,username = secrets_dict["eds_apis"]["WWTF"]["username"], password = secrets_dict["eds_apis"]["WWTF"]["password"])
        session_stiles.custom_dict = secrets_dict["eds_apis"]["WWTF"]
        sessions.update({"WWTF":session_stiles})

    return project_manager, sessions

@log_function_call(level=logging.DEBUG)
def demo_eds_print_point_live_alt():
    from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url

    project_manager, sessions = _demo_eds_start_session_maxson()
    queries_file_path_list = project_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # A scripter can edit their queries file names here - they do not need to use the default.
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered,'zd')
    
    # for key, session in sessions.items(): # Given multiple sessions, cycle through each. 
    key = "Maxson"
    session = sessions[key]
    # Discern which queries to use, filtered by current session key.
    queries_dictlist_filtered_by_session_key = queries_defaultdictlist_grouped_by_session_key.get(key,[])
    
    logging.debug(f"queries_dictlist_unfiltered = {queries_dictlist_unfiltered}\n")
    logging.debug(f"queries_dictlist_filtered_by_session_key = {queries_dictlist_filtered_by_session_key}\n")
    logging.debug(f"queries_defaultdictlist_grouped_by_session_key = {queries_defaultdictlist_grouped_by_session_key}\n")

    for row in queries_dictlist_filtered_by_session_key:
        iess = str(row["iess"]) if row["iess"] not in (None, '', '\t') else None
        point_data = EdsClient.get_points_live_mod(session,iess)
        if point_data is None:
            raise ValueError(f"No live point returned for iess {iess}")
        else:
            row.update(point_data) 
        EdsClient.print_point_info_row(row)

@log_function_call(level=logging.DEBUG)
def demo_eds_print_point_live():
    from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url
    from projects.eds_to_rjn.code import collector
    project_manager, sessions = _demo_eds_start_session_maxson()
    queries_file_path_list = project_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # A scripter can edit their queries file names here - they do not need to use the default.
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered)
    
    # for key, session in sessions.items(): # Given multiple sessions, cycle through each. 
    key = "Maxson"
    session = sessions[key]
    queries_dictlist_filtered_by_session_key = queries_defaultdictlist_grouped_by_session_key.get(key,[])
    queries_plus_responses_filtered_by_session_key = collector.collect_live_values(session, queries_dictlist_filtered_by_session_key)
    # Discern which queries to use, filtered by current session key.

    logging.debug(f"queries_dictlist_unfiltered = {queries_dictlist_unfiltered}\n")
    logging.debug(f"queries_defaultdictlist_grouped_by_session_key = {queries_defaultdictlist_grouped_by_session_key}\n")
    logging.debug(f"queries_dictlist_filtered_by_session_key = {queries_dictlist_filtered_by_session_key}\n")
    logging.debug(f"queries_plus_responses_filtered_by_session_key = {queries_plus_responses_filtered_by_session_key}\n")
    
    for row in queries_plus_responses_filtered_by_session_key:
        EdsClient.print_point_info_row(row)

@log_function_call(level=logging.DEBUG)
def demo_eds_plot_point_live():
    from threading import Thread

    from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url
    from projects.eds_to_rjn.code import collector, sanitizer
    from src.pipeline.plotbuffer import PlotBuffer
    from src.pipeline import gui_mpl_live

    # Initialize the project based on configs and defaults, in the demo initializtion script
    project_manager, sessions = _demo_eds_start_session_maxson()
    
    data_buffer = PlotBuffer()

    # Load queries
    queries_file_path_list = project_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # A scripter can edit their queries file names here - they do not need to use the default.
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered)
    
    key = "Maxson"
    session = sessions[key]
    queries_maxson = queries_defaultdictlist_grouped_by_session_key.get(key,[])

    def collect_loop():
        while True:
            responses = collector.collect_live_values(session, queries_maxson)
            for row in responses:
                label = f"{row.get('shortdesc')} ({row.get('un')})" 
                ts = row.get("ts")
                #ts = helpers.iso(row.get("ts")) #  dpg: TypeError: must be real number, not str
                av = row.get("value")
                un = row.get("un")
                if ts is not None and av is not None:
                    data_buffer.append(label, ts, av)
                    #logger.info(f"Live: {label} → {av} @ {ts}")
                    logger.info(f"Live: {label} {round(av,2)} {un}")
            time.sleep(1)

    collector_thread = Thread(target=collect_loop, daemon=True)
    collector_thread.start()

    # Now run the GUI in the main thread
    #gui_dpg_live.run_gui(data_buffer)
    gui_mpl_live.run_gui(data_buffer)

@log_function_call(level=logging.DEBUG)
def demo_eds_webplot_point_live():
    from threading import Thread

    from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url
    from projects.eds_to_rjn.code import collector, sanitizer
    from src.pipeline.plotbuffer import PlotBuffer
    #from src.pipeline import gui_flaskplotly_live
    from src.pipeline import gui_fastapi_plotly_live

    # Initialize the project based on configs and defaults, in the demo initializtion script
    project_manager, sessions = _demo_eds_start_session_maxson()
    
    data_buffer = PlotBuffer()

    # Load queries
    queries_file_path_list = project_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # A scripter can edit their queries file names here - they do not need to use the default.
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered)
    
    key = "Maxson"
    session = sessions[key]
    queries_maxson = queries_defaultdictlist_grouped_by_session_key.get(key,[])

    def collect_loop():
        while True:
            responses = collector.collect_live_values(session, queries_maxson)
            for row in responses:
                label = f"{row.get('shortdesc')} ({row.get('un')})" 
                #ts = helpers.human_readable(row.get("ts"))
                ts = helpers.iso(row.get("ts"))
                av = row.get("value")
                un = row.get("un")
                if ts is not None and av is not None:
                    data_buffer.append(label, ts, av)
                    #logger.info(f"Live: {label} → {av} @ {ts}")
                    logger.info(f"Live: {label} {round(av,2)} {un}")
            time.sleep(1)

    collector_thread = Thread(target=collect_loop, daemon=True)
    collector_thread.start()

    # Now run the GUI in the main thread
    #gui_flaskplotly_live.run_gui(data_buffer)
    gui_fastapi_plotly_live.run_gui(data_buffer)


@log_function_call(level=logging.DEBUG)    
def demo_eds_plot_trend():
    pass

@log_function_call(level=logging.DEBUG)
def demo_eds_print_point_export():
    project_manager, sessions = _demo_eds_start_session_maxson()
    session_maxson = sessions["Maxson"]

    point_export_decoded_str = EdsClient.get_points_export(session_maxson)
    pprint(point_export_decoded_str)
    return point_export_decoded_str

@log_function_call(level=logging.DEBUG)
def demo_eds_save_point_export():
    project_manager, sessions = _demo_eds_start_session_maxson()
    session_maxson = sessions["Maxson"]

    point_export_decoded_str = EdsClient.get_points_export(session_maxson)
    export_file_path = project_manager.get_exports_file_path(filename = 'export_eds_points_neo.txt')
    EdsClient.save_points_export(point_export_decoded_str, export_file_path = export_file_path)
    print(f"Export file saved to: \n{export_file_path}") 

@log_function_call(level=logging.DEBUG)
def demo_eds_print_trabular_trend():
    
    from src.pipeline.queriesmanager import QueriesManager
    from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url
    
    project_manager, sessions = _demo_eds_start_session_maxson()
    
    queries_manager = QueriesManager(project_manager)
    queries_file_path_list = project_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # you can edit your queries files here
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered,'zd')
    
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
                print('{} {} {}'.format(datetime.fromtimestamp(s[0]), round(s[1],2), s[2]))

@log_function_call(level=logging.DEBUG)
def demo_eds_print_license():
    project_manager, sessions = _demo_eds_start_session_maxson()
    session_maxson = sessions["Maxson"]

    response = EdsClient.get_license(session_maxson, api_url = session_maxson.custom_dict["url"])
    pprint(response)
    return response

@log_function_call(level=logging.DEBUG)
def demo_eds_ping():
    from src.pipeline.calls import call_ping
    project_manager, sessions = _demo_eds_start_session_maxson()
    session_maxson = sessions["Maxson"]

    api_url = session_maxson.custom_dict["url"]
    response = call_ping(api_url)

if __name__ == "__main__":

    '''
    - auto id current function name. solution: decorator, @log_function_call
    - print only which vars succeed
    '''
    import sys
    from src.pipeline.logging_setup import setup_logging
    cmd = sys.argv[1] if len(sys.argv) > 1 else "default"

    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("CLI started")

    if cmd == "demo-live":
        demo_eds_print_point_live()
    elif cmd == "demo-live-alt":
        demo_eds_print_point_live_alt()
    elif cmd == "demo-plot-live":
        demo_eds_plot_point_live()
    elif cmd == "demo-webplot-live":
        demo_eds_webplot_point_live()
    elif cmd == "demo-plot-trend":
        demo_eds_plot_trend()
    elif cmd == "demo-export":
        #demo_eds_print_point_export()
        demo_eds_save_point_export()
    elif cmd == "demo-trend":
        demo_eds_print_trabular_trend()
    elif cmd == "demo-ping":
        demo_eds_ping()
    elif cmd == "demo-license":
        demo_eds_print_license()
    else:
        print("Usage options: \n" 
        "poetry run python -m pipeline.api.eds demo-export \n"
        "poetry run python -m pipeline.api.eds demo-live \n"
        "poetry run python -m pipeline.api.eds demo-live-alt \n"  
        "poetry run python -m pipeline.api.eds demo-trend \n"
        "poetry run python -m pipeline.api.eds demo-plot-live \n"
        "poetry run python -m pipeline.api.eds demo-webplot-live \n"
        "poetry run python -m pipeline.api.eds demo-plot-trend \n"
        "poetry run python -m pipeline.api.eds demo-ping \n"
        "poetry run python -m pipeline.api.eds demo-license")
    