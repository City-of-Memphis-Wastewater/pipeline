from datetime import datetime
import logging
import requests
import time
from pprint import pprint
from pathlib import Path
import os
import mysql.connector
from functools import lru_cache

from src.pipeline.env import SecretConfig
from src.pipeline.workspace_manager import WorkspaceManager
from src.pipeline import helpers
from src.pipeline.decorators import log_function_call

logger = logging.getLogger(__name__)

class EdsClient:

    @staticmethod
    def get_license(session,api_url:str):
        response = session.get(api_url + 'license', json={}, verify=False).json()
        return response

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
    def get_tabular_trend(session, req_id, point_list):
        #print(f"point_list = {point_list}")
        results = [[] for _ in range(len(point_list))]
        while True:
            api_url = session.custom_dict['url']
            response = session.get(f'{api_url}trend/tabular?id={req_id}', verify=False).json()
            
            for chunk in response:
                if chunk['status'] == 'TIMEOUT':
                    raise RuntimeError('timeout')

                for idx, samples in enumerate(chunk['items']):
                    for sample in samples:
                        #print(f"sample = {sample}")
                        structured = {
                            "ts": sample[0],          # Timestamp
                            "value": sample[1],       # Measurement value
                            "quality": sample[2],       # Optional units or label
                        }
                        results[idx].append(structured)

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
    def create_tabular_request(session: object, api_url: str, starttime: int, endtime: int, points: list):
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

    @staticmethod
    def access_database_files_locally(
        session_key: str, starttime: int, endtime: int, point: list[int]
    ) -> list[list[dict]]:
        """
        Access MariaDB data directly by querying all MyISAM tables with .MYD files
        modified in the given time window, filtering by sensor ids in 'point'.

        Returns a list (per sensor id) of dicts with keys 'ts', 'value', 'quality'.
        """

        logger.info("Accessing MariaDB directly — local SQL mode enabled.")
        workspace_name = 'eds_to_rjn'
        workspace_manager = WorkspaceManager(workspace_name)
        secrets_dict = SecretConfig.load_config(secrets_file_path=workspace_manager.get_configs_secrets_file_path())
        full_config = secrets_dict["eds_dbs"][session_key]
        conn_config = {k: v for k, v in full_config.items() if k != "storage_path"}

        results = []

        try:
            conn = mysql.connector.connect(**conn_config)
            cursor = conn.cursor(dictionary=True)

            most_recent_table = get_most_recent_table(cursor, 'stiles')
            if not most_recent_table:
                logger.warning("No recent tables found.")
                return [[] for _ in point]

            # Verify the 'ts' column exists in the most recent table
            if not table_has_ts_column(conn, most_recent_table, db_type="mysql"):
                logger.warning(f"Skipping table '{most_recent_table}': no 'ts' column.")
                return [[] for _ in point]

            for point_id in point:
                logger.debug(f"Querying for sensor id {point_id}")

                query = f"""
                    SELECT ts, ids, tss, stat, val FROM `{most_recent_table}`
                    WHERE ts BETWEEN %s AND %s AND ids = %s
                    ORDER BY ts ASC
                """
                #cursor.execute(query, (starttime, endtime))
                cursor.execute(query, (starttime, endtime, point_id))
                
                full_rows = []
                for row in cursor:
                    quality_flags = decode_stat(row["stat"])
                    quality_code = quality_flags[0][2] if quality_flags else "N"
                    full_rows.append({
                        "ts": row["ts"],
                        "value": row["val"],
                        "quality": quality_code,
                    })

                # Sort final results in case rows came unordered
                full_rows.sort(key=lambda x: x["ts"])
                results.append(full_rows)


        except mysql.connector.errors.DatabaseError as db_err:
            if "Can't connect to MySQL server" in str(db_err):
                logger.error("Local database access failed: Please run this code on the proper EDS server where the local MariaDB is accessible.")
                # Optionally:
                print("ERROR: This code must be run on the proper EDS server for local database access to work.")
                return [[] for _ in point]  # return list of empty lists, one per point
            else:
                raise  # re-raise other DB errors
        except Exception as e:
            logger.error(f"Unexpected error accessing local database: {e}")
            raise
        finally:
            # cleanup cursor/connection if they exist
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

        logger.info(f"Successfully retrieved data for {len(point)} point(s)")
        return results
        
            
def table_has_ts_column_(cursor, table_name, db_type = "mysql"):
    if db_type =="sqlite":
    
        cursor 
        cursor.execute(f"PRAGMA table_info({table_name});")
        return any(row[1] == "ts" for row in cursor.fetchall())
    elif db_type =="mysql":
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE 'ts'")
                    
    else: 
        raise ValueError(f"Unsupported database type: {db_type}")

def table_has_ts_column__(cursor, table_name, db_type="mysql"):
    if db_type == "sqlite":
        cursor.execute(f"PRAGMA table_info({table_name});")
        return any(row[1] == "ts" for row in cursor.fetchall())

    elif db_type == "mysql":
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE 'ts'")
        return cursor.fetchone() is not None  # ✅ Return True if found, False if not

    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def table_has_ts_column(conn, table_name, db_type="mysql"):
    if db_type == "sqlite":
        # your sqlite logic here
        pass
    elif db_type == "mysql":
        with conn.cursor() as cur:
            cur.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE 'ts'")
            result = cur.fetchall()
            return len(result) > 0
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    
def identify_relevant_MyISM_tables(session_key: str, starttime: int, endtime: int, secrets_dict: dict) -> list:
    #
    #  to your table storage
    storage_dir = secrets_dict["eds_dbs"][session_key]["storage_path"]
    
    # Collect matching table names based on file mtime
    matching_tables = []

    if False:
        for fname in os.listdir(storage_dir):
            fpath = os.path.join(storage_dir, fname)
            if not os.path.isfile(fpath):
                continue
            mtime = os.path.getmtime(fpath)
            if starttime <= mtime <= endtime:
                table_name, _ = os.path.splitext(fname)
                if 'pla' in table_name: 
                    matching_tables.append(table_name)

    '''
    # Instead of os.path.join + isfile + getmtime every time...
    # Use `os.scandir`, which gives all of that in one go and is much faster:
    with os.scandir(storage_dir) as it:
        for entry in it:
            if entry.is_file():
                mtime = entry.stat().st_mtime
                if starttime <= mtime <= endtime and 'pla' in entry.name:
                    table_name, _ = os.path.splitext(entry.name)
                    matching_tables.append(table_name)
    '''
    # Efficient, sorted, filtered scan
    sorted_entries = sorted(
        (entry for entry in os.scandir(storage_dir) if entry.is_file()),
        key=lambda e: e.stat().st_mtime,
        reverse=True
    )

    for entry in sorted_entries:
        mtime = entry.stat().st_mtime
        if starttime <= mtime <= endtime and 'pla' in entry.name:
            table_name, _ = os.path.splitext(entry.name)
            matching_tables.append(table_name)


    #print("Matching tables:", matching_tables)
    return matching_tables
def get_most_recent_table(cursor, db_name, prefix='pla_'):
    query = f"""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME LIKE %s
        ORDER BY TABLE_NAME DESC
        LIMIT 1;
    """
    cursor.execute(query, (db_name, f'{prefix}%'))
    result = cursor.fetchone()
    return result['TABLE_NAME'] if result else None


@lru_cache()
def get_stat_alarm_definitions():
    """
    Returns a dictionary where each key is the bitmask integer value from the EDS alarm types,
    and each value is a tuple: (description, quality_code).

    | Quality Flag | Meaning      | Common Interpretation                            |
    | ------------ | ------------ | ------------------------------------------------ |
    | `G`          | Good         | Value is reliable/valid                          |
    | `B`          | Bad          | Value is invalid/unreliable                      |
    | `U`          | Uncertain    | Value may be usable, but not guaranteed accurate |
    | `S`          | Substituted  | Manually entered or filled in                    |
    | `N`          | No Data      | No value available                               |
    | `Q`          | Questionable | Fails some validation                            |

    Source: eDocs/eDocs%203.8.0%20FP3/Index/en/OPH070.pdf

    """
    return {
        1: ("ALMTYPE_RETURN", "G"),
        2: ("ALMTYPE_SENSOR", "B"),
        4: ("ALMTYPE_HIGH", "G"),
        8: ("ALMTYPE_HI_WRS", "G"),
        16: ("ALMTYPE_HI_BET", "G"),
        32: ("ALMTYPE_HI_UDA", "G"),
        64: ("ALMTYPE_HI_WRS_UDA", "G"),
        128: ("ALMTYPE_HI_BET_UDA", "G"),
        256: ("ALMTYPE_LOW", "G"),
        512: ("ALMTYPE_LOW_WRS", "G"),
        1024: ("ALMTYPE_LOW_BET", "G"),
        2048: ("ALMTYPE_LOW_UDA", "G"),
        4096: ("ALMTYPE_LOW_WRS_UDA", "G"),
        8192: ("ALMTYPE_LOW_BET_UDA", "G"),
        16384: ("ALMTYPE_SP_ALM", "B"),
        32768: ("ALMTYPE_TIME_OUT", "U"),
        65536: ("ALMTYPE_SID_ALM", "U"),
        131072: ("ALMTYPE_ALARM", "B"),
        262144: ("ALMTYPE_ST_CHG", "G"),
        524288: ("ALMTYPE_INCR_ALARM", "G"),
        1048576: ("ALMTYPE_HIGH_HIGH", "G"),
        2097152: ("ALMTYPE_LOW_LOW", "G"),
        4194304: ("ALMTYPE_DEVICE", "U"),
    }
def decode_stat(stat_value):
    '''
    Example:
    >>> decode_stat(8192)
    [(8192, 'ALMTYPE_LOW_BET_UDA', 'G')]

    >>> decode_stat(8192 + 2)
    [(2, 'ALMTYPE_SENSOR', 'B'), (8192, 'ALMTYPE_LOW_BET_UDA', 'G')]
    '''
    alarm_dict = get_stat_alarm_definitions()
    active_flags = []
    for bitmask, (description, quality) in alarm_dict.items():
        if stat_value & bitmask:
            active_flags.append((bitmask, description, quality))
    return active_flags


def fetch_eds_data_row(session, iess):
    point_data = EdsClient.get_points_live_mod(session, iess)
    return point_data

@log_function_call(level=logging.DEBUG) 
def _demo_eds_start_session_CoM_WWTPs():
    
    workspace_name = WorkspaceManager.identify_default_workspace()
    workspace_manager = WorkspaceManager(workspace_name)

    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_configs_secrets_file_path())
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

    return workspace_manager, sessions

@log_function_call(level=logging.DEBUG)
def demo_eds_print_point_live_alt():
    from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url

    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
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
    from workspaces.eds_to_rjn.code import collector
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
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
    from workspaces.eds_to_rjn.code import collector, sanitizer
    from src.pipeline.plotbuffer import PlotBuffer
    from src.pipeline import gui_mpl_live

    # Initialize the workspace based on configs and defaults, in the demo initializtion script
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    
    data_buffer = PlotBuffer()

    # Load queries
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
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
                #ts = helpers.human_readable(row.get("ts"))
                #ts = helpers.iso(row.get("ts")) #  dpg: TypeError: must be real number, not str
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

    from src.pipeline.queriesmanager import QueriesManager, load_query_rows_from_csv_files, group_queries_by_api_url
    from workspaces.eds_to_rjn.code import collector, sanitizer
    from src.pipeline.plotbuffer import PlotBuffer
    #from src.pipeline import gui_flaskplotly_live
    from src.pipeline import gui_fastapi_plotly_live

    # Initialize the workspace based on configs and defaults, in the demo initializtion script
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()

    queries_manager = QueriesManager(workspace_manager)
    
    data_buffer = PlotBuffer()

    # Load queries
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # A scripter can edit their queries file names here - they do not need to use the default.
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered)
    
    key = "Maxson"
    session = sessions[key]
    queries_maxson = queries_defaultdictlist_grouped_by_session_key.get(key,[])

    def load_historic_data_back_to_last_success():
        starttime = queries_manager.get_most_recent_successful_timestamp(api_id="Maxson")
        logger.info(f"queries_manager.get_most_recent_successful_timestamp(), key = {'Maxson'}")
        logger.info(f"starttime = {starttime}")
        endtime = helpers.get_now_time_rounded()

        point_list = [row['iess'] for row in queries_defaultdictlist_grouped_by_session_key.get(key,[])]
        api_url = session.custom_dict["url"]
        request_id = EdsClient.create_tabular_request(session, api_url, starttime, endtime, points=point_list)
        EdsClient.wait_for_request_execution_session(session, api_url, request_id)
        results = EdsClient.get_tabular_trend(session, request_id, point_list)
        logger.info(f"len(results) = {len(results)}")

        for idx, rows in enumerate(results):
            for row in rows:
                label = f"{row.get('rjn_entityid')} ({row.get('units')})"
                ts = helpers.iso(row.get("ts"))
                av = row.get("value")
                if ts is not None and av is not None:
                    data_buffer.append(label, ts, av)
                    logger.debug(f"Historic: {label} {round(av,2)} @ {ts}")
                    
        queries_manager.update_attempt("Maxson")

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
    if True:
        load_historic_data_back_to_last_success()
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
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    session_maxson = sessions["Maxson"]

    point_export_decoded_str = EdsClient.get_points_export(session_maxson)
    pprint(point_export_decoded_str)
    return point_export_decoded_str

@log_function_call(level=logging.DEBUG)
def demo_eds_save_point_export():
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    session_maxson = sessions["Maxson"]

    point_export_decoded_str = EdsClient.get_points_export(session_maxson)
    export_file_path = workspace_manager.get_exports_file_path(filename = 'export_eds_points_neo.txt')
    EdsClient.save_points_export(point_export_decoded_str, export_file_path = export_file_path)
    print(f"Export file saved to: \n{export_file_path}") 

@log_function_call(level=logging.DEBUG)
def demo_eds_print_tabular_trend():
    
    from src.pipeline.queriesmanager import QueriesManager
    from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url
    
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    
    queries_manager = QueriesManager(workspace_manager)
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    logger.debug(f"queries_file_path_list = {queries_file_path_list}")
    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list) # you can edit your queries files here
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered,'zd')
    
    for key, session in sessions.items():
        # Discern which queries to use
        point_list = [row['iess'] for row in queries_defaultdictlist_grouped_by_session_key.get(key,[])]

        # Discern the time range to use
        starttime = queries_manager.get_most_recent_successful_timestamp(api_id="Maxson")
        endtime = helpers.get_now_time_rounded()

        api_url = session.custom_dict["url"]
        request_id = EdsClient.create_tabular_request(session, api_url, starttime, endtime, points=point_list)
        EdsClient.wait_for_request_execution_session(session, api_url, request_id)
        results = EdsClient.get_tabular_trend(session, request_id, point_list)
        session.post(api_url + 'logout', verify=False)
        #
        for idx, iess in enumerate(point_list):
            print('\n{} samples:'.format(iess))
            for s in results[idx]:
                #print('{} {} {}'.format(datetime.fromtimestamp(s['ts']), round(s['value'],2), s['quality']))
                print('{} {} {}'.format(datetime.fromtimestamp(s['ts']), s['value'], s['quality']))
        queries_manager.update_success(api_id=key) # not appropriate here in demo without successful transmission to 3rd party API

@log_function_call(level=logging.DEBUG)
def demo_eds_local_database_access():
    from src.pipeline.queriesmanager import QueriesManager
    from src.pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_api_url
    workspace_name = 'eds_to_rjn' # workspace_name = workspace_manager.identify_default_workspace()
    workspace_manager = WorkspaceManager(workspace_name)
    queries_manager = QueriesManager(workspace_manager)
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    logger.debug(f"queries_file_path_list = {queries_file_path_list}")

    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list)
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_api_url(queries_dictlist_unfiltered,'zd')
    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_configs_secrets_file_path())
    sessions_eds = {}

    # --- Prepare Stiles session_eds

    session_stiles = None # assume the EDS API session cannot be established
    sessions_eds.update({"WWTF":session_stiles})


    key_eds = "WWTF"
    session_eds = session_stiles
    point_list = [row['iess'] for row in queries_defaultdictlist_grouped_by_session_key.get(key_eds,[])]

    # Discern the time range to use
    starttime = queries_manager.get_most_recent_successful_timestamp(api_id="WWTF")
    logger.info(f"queries_manager.get_most_recent_successful_timestamp(), key = {'WWTF'}")
    endtime = helpers.get_now_time_rounded()
    logger.info(f"starttime = {starttime}")
    logger.info(f"endtime = {endtime}")

    
    results = EdsClient.access_database_files_locally(key_eds, starttime, endtime, point=point_list)

    print(f"len(results) = {len(results)}")
    print(f"len(results[0]) = {len(results[0])}")
    print(f"len(results[1]) = {len(results[1])}")
    
    for idx, iess in enumerate(point_list):
        if results[idx]:
            #print(f"rows = {rows}")
            timestamps = []
            values = []
            
            for row in results[idx]:
                #print(f"row = {row}")
                #EdsClient.print_point_info_row(row)

                dt = datetime.fromtimestamp(row["ts"])
                timestamp_str = helpers.round_datetime_to_nearest_past_five_minutes(dt).isoformat(timespec='seconds')
                if row['quality'] == 'G':
                    timestamps.append(timestamp_str)
                    values.append(round(row["value"],5)) # unrounded values fail to post
            print(f"final row = {row}")
        else:
            print("No data rows for this point")

@log_function_call(level=logging.DEBUG)
def demo_eds_print_license():
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    session_maxson = sessions["Maxson"]

    response = EdsClient.get_license(session_maxson, api_url = session_maxson.custom_dict["url"])
    pprint(response)
    return response

@log_function_call(level=logging.DEBUG)
def demo_eds_ping():
    from src.pipeline.calls import call_ping
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
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
    elif cmd =="demo-db":
        demo_eds_local_database_access()
    elif cmd == "demo-trend":
        demo_eds_print_tabular_trend()
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
        "poetry run python -m pipeline.api.eds demo-db \n"
        "poetry run python -m pipeline.api.eds demo-ping \n"
        "poetry run python -m pipeline.api.eds demo-license")
    