import time
import logging
from pprint import pprint
from pathlib import Path
from datetime import datetime

from pipeline.security_and_config import SecurityAndConfig, get_base_url_config_with_prompt
from pipeline.api.eds.rest.client import EdsRestClient
from pipeline import helpers
from pipeline.decorators import log_function_call
from pipeline.time_manager import TimeManager

logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)


@log_function_call(level=logging.DEBUG) 
def _demo_eds_start_session_CoM_WWTPs():
    
    workspace_name = WorkspaceManager.identify_default_workspace_name()
    workspace_manager = WorkspaceManager(workspace_name)

    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    sessions = {}

    base_url_maxson = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("url").rstrip("/")
    session_maxson = EdsRestClient.login_to_session(api_url = base_url_maxson,
                                                username = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("username"),
                                                password = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("password"))
    session_maxson.base_url = base_url_maxson
    session_maxson.zd = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("zd")

    sessions.update({"Maxson":session_maxson})

    # Show example of what it would be like to start a second session (though Stiles API port 43084 is not accesible at this writing)
    if False:
        base_url_stiles = secrets_dict.get("eds_apis", {}).get("WWTF", {}).get("url").rstrip("/")
        session_stiles = EdsRestClient.login_to_session(api_url = base_url_stiles ,username = secrets_dict.get("eds_apis", {}).get("WWTF", {}).get("username"), password = secrets_dict.get("eds_apis", {}).get("WWTF", {}).get("password"))
        session_stiles.base_url = base_url_stiles
        session_stiles.zd = secrets_dict.get("eds_apis", {}).get("WWTF", {}).get("zd")
        sessions.update({"WWTF":session_stiles})

    return workspace_manager, sessions

@log_function_call(level=logging.DEBUG)
def demo_eds_print_point_live_alt():
    from pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_col

    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # A scripter can edit their queries file names here - they do not need to use the default.
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_col(queries_dictlist_unfiltered,'zd')
    
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
        point_data = EdsRestClient.get_points_live(session,iess)
        if point_data is None:
            raise ValueError(f"No live point returned for iess {iess}")
        else:
            row.update(point_data) 
        EdsRestClient.print_point_info_row(row)

@log_function_call(level=logging.DEBUG)
def demo_eds_print_point_live():
    from pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_col
    from workspaces.eds_to_rjn.code import collector
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # A scripter can edit their queries file names here - they do not need to use the default.
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_col(queries_dictlist_unfiltered)
    
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
        EdsRestClient.print_point_info_row(row)

@log_function_call(level=logging.DEBUG)
def demo_eds_plot_point_live():
    from threading import Thread

    from pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_col
    from workspaces.eds_to_rjn.code import collector, sanitizer
    from pipeline.plotbuffer import PlotBuffer
    from pipeline import gui_mpl_live

    # Initialize the workspace based on configs and defaults, in the demo initializtion script
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    
    data_buffer = PlotBuffer()

    # Load queries
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # A scripter can edit their queries file names here - they do not need to use the default.
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_col(queries_dictlist_unfiltered)
    
    key = "Maxson"
    session = sessions[key]
    queries_maxson = queries_defaultdictlist_grouped_by_session_key.get(key,[])

    def collect_loop():
        while True:
            responses = collector.collect_live_values(session, queries_maxson)
            for row in responses:
                label = f"{row.get('shortdesc')} ({row.get('un')})" 
                ts = row.get("ts")
                ts = helpers.iso(row.get("ts")) # dpg is out, mpl is in. plotly is way, way in.
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

    from pipeline.queriesmanager import QueriesManager, load_query_rows_from_csv_files, group_queries_by_col
    from workspaces.eds_to_rjn.code import collector
    from pipeline.plotbuffer import PlotBuffer
    from pipeline import gui_starlette_msgspec_plotly

    # Initialize the workspace based on configs and defaults, in the demo initializtion script
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()

    queries_manager = QueriesManager(workspace_manager)
    
    data_buffer = PlotBuffer()

    # Load queries
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # A scripter can edit their queries file names here - they do not need to use the default.
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_col(queries_dictlist_unfiltered)
    
    key = "Maxson"
    session = sessions[key]
    queries_maxson = queries_defaultdictlist_grouped_by_session_key.get(key,[])

    def collect_loop():
        while True:
            responses = collector.collect_live_values(session, queries_maxson)
            for row in responses:
                
                #ts = TimeManager(row.get("ts")).as_formatted_time()
                ts = TimeManager(row.get("ts")).as_iso()
                #ts = helpers.iso(row.get("ts"))
                av = row.get("value")
                un = row.get("un")
                # QUICK AND DIRTY CONVERSION FOR WWTF WETWELL LEVEL TO FEET 
                if row.get('iess') == "M310LI.UNIT0@NET0":
                    av = (av/12)+181.25 # convert inches of wetwell to feet above mean sealevel
                    un = "FT"
                label = f"{row.get('shortdesc')} ({un})" 
                if ts is not None and av is not None:
                    data_buffer.append(label, ts, av)
                    #logger.info(f"Live: {label} → {av} @ {ts}")
                    logger.info(f"Live: {label} {round(av,2)} {un}")
            time.sleep(1)
    if False:
        EdsRestClient.load_historic_data()
    collector_thread = Thread(target=collect_loop, daemon=True)
    collector_thread.start()

    # Now run the GUI in the main thread
    if False:
        gui_starlette_msgspec_plotly.run_gui(data_buffer, port=find_open_port(8082))

@log_function_call(level=logging.DEBUG)    
def demo_eds_plot_trend():
    pass

@log_function_call(level=logging.DEBUG)
def demo_eds_print_point_export():
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    session_maxson = sessions["Maxson"]

    point_export_decoded_str = EdsRestClient.get_points_export(session_maxson)
    pprint(point_export_decoded_str)
    return point_export_decoded_str

@log_function_call(level=logging.DEBUG)
def demo_eds_save_point_export():
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    session_maxson = sessions["Maxson"]

    point_export_decoded_str = EdsRestClient.get_points_export(session_maxson)
    export_path = workspace_manager.get_exports_file_path(filename = 'export_eds_points_neo.txt')
    EdsRestClient.save_points_export(point_export_decoded_str, export_path = export_path)
    print(f"Export file saved to: \n{export_path}") 


@log_function_call(level=logging.DEBUG)
def demo_eds_print_tabular_trend():
    
    from pipeline.queriesmanager import QueriesManager
    from pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_col
    
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    
    queries_manager = QueriesManager(workspace_manager)
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    logger.debug(f"queries_file_path_list = {queries_file_path_list}")
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # you can edit your queries files here
    
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_col(queries_dictlist_unfiltered,'zd')
    
    for key, session in sessions.items():
        # Discern which queries to use
        point_list = [row['iess'] for row in queries_defaultdictlist_grouped_by_session_key.get(key,[])]

        # Discern the time range to use
        starttime = queries_manager.get_most_recent_successful_timestamp(api_id="Maxson")
        endtime = helpers.get_now_time_rounded(workspace_manager)

        api_url = str(session.base_url) 
        request_id = EdsRestClient.create_tabular_request(session, api_url, starttime, endtime, points=point_list)
        EdsRestClient.wait_for_request_execution_session(session, api_url, request_id)
        results = EdsRestClient.get_tabular_trend(session, request_id, point_list)
        session.post(f"{api_url}'/logout", verify=False)
        #
        for idx, iess in enumerate(point_list):
            print('\n{} samples:'.format(iess))
            for s in results[idx]:
                #print('{} {} {}'.format(datetime.fromtimestamp(s['ts']), round(s['value'],2), s['quality']))
                print('{} {} {}'.format(datetime.fromtimestamp(s['ts']), s['value'], s['quality']))
        queries_manager.update_success(api_id=key) # not appropriate here in demo without successful transmission to 3rd party API

@log_function_call(level=logging.DEBUG)
def demo_eds_print_license():
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    session_maxson = sessions["Maxson"]

    response = EdsRestClient.get_license(session_maxson, api_url = session_maxson.base_url)
    pprint(response)
    return response

@log_function_call(level=logging.DEBUG)
def demo_eds_ping():
    from pipeline.calls import call_ping
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    session_maxson = sessions["Maxson"]
    response = call_ping(session_maxson.base_url)



if __name__ == "__main__":

    '''
    - auto id current function name. solution: decorator, @log_function_call
    - print only which vars succeed
    '''
    import sys
    from pipeline.logging_setup import setup_logging
    from pipeline.api.eds.rest.graphics import demo_eds_save_graphics_export
    from pipeline.api.eds.database import demo_eds_local_database_access

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
    elif cmd == "demo-point-export":
        #demo_eds_print_point_export()
        demo_eds_save_point_export()
    elif cmd =="demo-db":
        demo_eds_local_database_access()
    elif cmd == "demo-trend":
        demo_eds_print_tabular_trend()
    elif cmd == "ping":
        demo_eds_ping()
    elif cmd == "export-graphics":
        demo_eds_save_graphics_export()
    elif cmd == "license":
        demo_eds_print_license()
    else:
        print("Usage options: \n" 
        "poetry run python -m pipeline.api.eds.rest.demo demo-point-export \n"
        "poetry run python -m pipeline.api.eds.rest.demo demo-tabular-export \n"
        "poetry run python -m pipeline.api.eds.rest.demo demo-live \n"
        "poetry run python -m pipeline.api.eds.rest.demo demo-live-alt \n"  
        "poetry run python -m pipeline.api.eds.rest.demo demo-trend \n"
        "poetry run python -m pipeline.api.eds.rest.demo demo-plot-live \n"
        "poetry run python -m pipeline.api.eds.rest.demo demo-webplot-live \n"
        "poetry run python -m pipeline.api.eds.rest.demo demo-plot-trend \n"
        "poetry run python -m pipeline.api.eds.rest.demo demo-db \n"
        "poetry run python -m pipeline.api.eds.rest.demo ping \n"
        "poetry run python -m pipeline.api.eds.rest.demo license \n"
        "poetry run python -m pipeline.api.eds.rest.demo export-graphics \n"
        "poetry run python -m pipeline.api.eds.rest.demo access-workspace")