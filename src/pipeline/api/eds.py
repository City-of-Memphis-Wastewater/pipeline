from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
from datetime import datetime
import logging
import requests
from requests.exceptions import Timeout
import time
from pprint import pprint
from pathlib import Path
import os
import re
import inspect
import subprocess
import platform
import mysql.connector
from functools import lru_cache
import typer # for CLI


from pipeline.env import SecretConfig
from pipeline.workspace_manager import WorkspaceManager
from pipeline import helpers
from pipeline.decorators import log_function_call
from pipeline.time_manager import TimeManager

logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)

class EdsLoginException(Exception):
    """
    Custom exception raised when a login to the EDS API fails.

    This exception is used to differentiate between a simple network timeout
    and a specific authentication or API-related login failure.
    """

    def __init__(self, message: str = "Login failed for the EDS API. Check VPN and credentials."):
        """
        Initializes the EdsLoginException with a custom message.

        Args:
            message: A descriptive message for the error.
        """
        self.message = message
        super().__init__(self.message)

class EdsClient:

    @staticmethod
    def login_to_session(api_url, username, password, timeout=10):
        session = requests.Session()

        data = {'username': username, 'password': password, 'type': 'script'}
        response = session.post(f"{api_url}/login",
                                json=data,
                                verify=False,
                                timeout=timeout
                                )
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        json_response = response.json()
        #print(f"response = {response}")
        session.headers['Authorization'] = f"Bearer {json_response['sessionId']}"
        return session
    
    @staticmethod
    def login_to_session_with_api_credentials(api_credentials):
        """
        Like login_to_sessesion, plug with custom session attributes added to the session object.
        """
        # Expected to be used in terminal, so typer is acceptable, but should be scaled.
        session = None
        try:
            session = EdsClient.login_to_session(
                api_url=api_credentials.get("url"),
                username=api_credentials.get("username"),
                password=api_credentials.get("password"),
                timeout=10 # Add a 10-second timeout to the request
            )
            
            # --- Add custom session attributes to the session object ---
            session.base_url = api_credentials.get("url")
            session.zd = api_credentials.get("zd")
        except Timeout:
            typer.echo(
                typer.style(
                    "\nConnection to the EDS API timed out. Please check your VPN connection and try again.",
                    fg=typer.colors.RED,
                    bold=True,
                )
            )
            raise typer.Exit(code=1)
        except EdsLoginException as e:
            typer.echo(
                typer.style(
                    f"\nLogin failed for EDS API: {e}",
                    fg=typer.colors.RED,
                    bold=True,
                )
            )
            raise typer.Exit(code=1)
        
        return session
    
    @staticmethod
    def get_license(session,api_url:str):
        response = session.get(f'{api_url}/license', json={}, verify=False).json()
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
    def get_points_live_mod(session, iess):
        "Access live value of point from the EDS, based on zs/api_id value (i.e. Maxson, WWTF, Server)"
        api_url = str(session.base_url) 

        query = {
            'filters' : [{
            'iess': [iess],
            'tg' : [0, 1],
            }],
            'order' : ['iess']
            }
        response = session.post(f"{api_url}/points/query", json=query, verify=False).json()
        
        if not response or "points" not in response:
            return None

        points = response["points"]
        if len(points) != 1:
            raise ValueError(f"Expected 1 point for iess='{iess}', got {len(points)}")

        return points[0]

    @staticmethod
    def get_tabular_mod(session, req_id, point_list):
        results = [[] for _ in range(len(point_list))]
        while True:
            api_url = str(session.base_url) 
            response = session.get(f'{api_url}/trend/tabular?id={req_id}', verify=False).json()
            for chunk in response:
                if chunk['status'] == 'TIMEOUT':
                    raise RuntimeError('timeout')

                for idx, samples in enumerate(chunk['items']):
                    results[idx] += samples
                    
                if chunk['status'] == 'LAST':
                    return results

    @staticmethod
    def get_tabular_trend(session, req_id, point_list):
        # The raw from EdsClient.get_tabular_trend() is brought in like this: 
        #   sample = [1757763000, 48.93896783431371, 'G'] 
        results = [[] for _ in range(len(point_list))]
        while True:
            api_url = str(session.base_url) 
            response = session.get(f'{api_url}/trend/tabular?id={req_id}', verify=False).json()
            
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
    #def get_points_export(session,filter_iess:str=''):
    def get_points_export(session,filter_iess: list=None, zd: str =None) -> str: 
        """
        Retrieves point metadata from the API, filtering by a list of IESS values.

        Args:
            session (requests.Session): The active session object.
            filter_iess (list): A list of IESS strings to filter by. Currently only allows one input.
            zd (str): An optional zone directory to filter by.
        
        Returns:
            str: The raw text response from the API.
        """

        api_url = str(session.base_url) 

        # Use a dictionary to build the query parameters.
        # The `requests` library handles lists gracefully by repeating the key.
        params = {}
        
        # Add the Zone Directory (zd) if provided, otherwise use the session's zd.
        if zd:
            params['zd'] = zd
        else:
            params['zd'] = str(session.zd)

        # Add the list of IESS values if the list is not empty.
        # The 'requests' library will automatically format this as
        # ?iess=item1&iess=item2&...
        # 1. Check if filter_iess is a list and join it into a comma-separated string.
        # 2. Add the resulting string to params, which the API is likely expecting.
        #print(f"filter_iess = {filter_iess}")
        if filter_iess:
            if isinstance(filter_iess, list) and len(filter_iess) > 0:
                # Convert the list to a single string using a delimiter
                iess_string = ",".join(filter_iess) # Join with a space ","
                #iess_string = " ".join(filter_iess) # Join with a space " "
                params['iess'] = iess_string
            elif isinstance(filter_iess, str):
                # If it's already a string, use it directly
                params['iess'] = filter_iess
        # --- END OF FIX ---
        
        params['order'] = 'iess'
        #print(f"params = {params}")
        zd = str(session.zd)  
        #order = 'iess'
        #query = '?zd={}&iess={}&order={}'.format(zd, filter_iess, order)
        request_url = f"{api_url}/points/export" #+ query
        
        response = session.get(request_url, params=params, json={}, verify=False)
        #print(f"Status Code: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}, Body: {response.text[:500]}")
        decoded_str = response.text
        return decoded_str


    @staticmethod
    def get_points_metadata(session, filter_iess=None, zd=None):
        """
        Retrieves and parses point metadata into a dictionary.

        Args:
            session (requests.Session): The active session object.
            filter_iess (list): A list of IESS strings to filter by.
            zd (str): An optional zone directory to filter by.
        
        Returns:
            dict: A dictionary where keys are IESS strings and values are
                  dictionaries of the point's attributes.
                  Returns an empty dictionary on failure.
        """
        raw_export_str = EdsClient.get_points_export(session, filter_iess, zd)
        
        all_points_metadata = {}
        
        # Regex to find key='value' pairs. Handles single-quoted values.
        # This pattern is more robust than a simple split.
        pattern = re.compile(r"(\w+)='([^']*)'")
        for iess_value in filter_iess:
            # We must make a separate API call for each IESS.
            # Use the existing get_points_export function, but pass a single
            # IESS value in a list so the URL formatting remains consistent.
            raw_export_str = EdsClient.get_points_export(session, filter_iess=[iess_value], zd=zd)

            
            for line in raw_export_str.strip().splitlines():
                # We are only interested in lines that start with 'POINT'
                if line.strip().startswith('POINT '):
                    # Extract key-value pairs using the regex
                    attributes = dict(pattern.findall(line))
                    
                    # Double-check that the returned IESS matches the requested one
                    if attributes.get('IESS') == iess_value:
                        all_points_metadata[iess_value] = attributes
                        break # We found our point, so we can stop parsing this response
        
        return all_points_metadata
    # --- Example of how to use it ---
    # (Assuming you have a 'session' object and a list of iess values)
    #
    # iess_list_to_filter = ['M100FI.UNIT0@NET0', 'M119FI.UNIT0@NET0']
    # session = # ... your session object from login
    #
    # # Get the parsed dictionary
    # points_data = EdsClient.get_points_metadata(session, filter_iess=iess_list_to_filter)
    #
    # # Now you can easily access the unit for 'M100FI.UNIT0@NET0'
    # unit = points_data.get('M100FI.UNIT0@NET0', {}).get('UN')
    # print(f"The unit for M100FI.UNIT0@NET0 is: {unit}")
    #
    # # You can also iterate through the results
    # for iess, attributes in points_data.items():
    #     print(f"Point: {iess}, Description: {attributes.get('DESC')}, Unit: {attributes.get('UN')}")
    
    @staticmethod
    def save_points_export(decoded_str, export_path):
        lines = decoded_str.strip().splitlines()

        with open(export_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")  # Save each line in the text file
    

    
    @staticmethod
    #def create_tabular_request(session: object, api_url: str, starttime: int, endtime: int, points: list):
    def create_tabular_request_(session, api_url, starttime, endtime, points, step_seconds = 300):
        
        data = {
            'period': {
                'from': starttime, 
                'till': endtime, # must be of type int, like: int(datetime(YYYY, MM, DD, HH).timestamp()),
            },

            'step': step_seconds, # five minutes
            'items': [{
                'pointId': {'iess': p},
                'shadePriority': 'DEFAULT',
                'function': 'AVG'
            } for p in points],
        }
        try:
            response = session.post(f"{api_url}/trend/tabular", json=data, verify=False).json()
            return response['id']
            #print(f"response = {response}")
        except:
            #raise ValueError(f"JSON not returned with {inspect.currentframe().f_code.co_name} response")
            response = session.post(f"{api_url}/trend/tabular", json=data, verify=False)
            #print(f"response = {response}")

    @staticmethod
    def create_tabular_request(session, api_url, starttime, endtime, points, step_seconds=300):
        """
        Submit a tabular trend request. Returns request id on success, or None if failed.
        """

        data = {
            "period": {
                "from": starttime,
                "till": endtime,
            },
            "step": step_seconds,
            "items": [
                {
                    "pointId": {"iess": p},
                    "shadePriority": "DEFAULT",
                    "function": "AVG",
                }
                for p in points
            ],
        }

        try:
            res = session.post(f"{api_url}/trend/tabular", json=data, verify=False)
        except Exception as e:
            logger.error(f"Request failed to {api_url}/trend/tabular: {e}")
            return None

        if res.status_code != 200:
            logger.error(f"Bad status {res.status_code} from server: {res.text}")
            return None

        try:
            payload = res.json()
        except Exception:
            logger.error(f"Non-JSON response: {res.text}")
            return None

        req_id = payload.get("id")
        if not req_id:
            logger.error(f"No request id in response: {payload}")
            return None

        return req_id

    @staticmethod
    def wait_for_request_execution_session(session, api_url, req_id):
        st = time.time()
        while True:
            time.sleep(1)
            res = session.get(f'{api_url}/requests?id={req_id}', verify=False).json()
            status = res[str(req_id)]
            if status['status'] == 'FAILURE':
                raise RuntimeError('request [{}] failed: {}'.format(req_id, status['message']))
            elif status['status'] == 'SUCCESS':
                break
            elif status['status'] == 'EXECUTING':
                print('request [{}] progress: {:.2f}\n'.format(req_id, time.time() - st))

        print('request [{}] executed in: {:.3f} s\n'.format(req_id, time.time() - st))

    @staticmethod
    #def this_computer_is_an_enterprise_database_server(secrets_dict: dict, session_key: str) -> bool:
    def this_computer_is_an_enterprise_database_server(secrets_dict, session_key):
        """
        Check if the current computer is an enterprise database server.
        This is determined by checking if the ip address matches the configured EDS database key.
        """
        import socket
        from urllib.parse import urlparse
        from pipeline.helpers import get_lan_ip_address_of_current_machine
        # Check if the session_key exists in the secrets_dict
        url = secrets_dict["eds_apis"][session_key]["url"]
        parsed = urlparse(url)
        hostname = parsed.hostname  # Extract hostname from URL
        ip = socket.gethostbyname(hostname)
        bool_ip = (ip == get_lan_ip_address_of_current_machine())
        logger.info(f"Checking if this computer is enterprise database server: {bool_ip}")
        return bool_ip
    
    @staticmethod
    def get_graphics_list(session, api_url):
        """Return list of graphics from EDS session."""
        resp = session.get(f"{api_url}/graphics")  # api_url passed in
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_graphic_export(session, api_url, graphic_file):
        """Fetch a graphic as PNG bytes."""
        resp = session.get(f"{api_url}/graphics/{graphic_file}/export", params={"format": "png"})
        resp.raise_for_status()
        return resp.content

    @staticmethod
    def save_graphic_export(graphic_bytes, output_file_path):
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, "wb") as f:
            f.write(graphic_bytes)

    
    @staticmethod
    #def access_database_files_locally(
    #    session_key: str,
    #    starttime: int,
    #    endtime: int,
    #    point: list[int],
    #    tables: list[str] | None = None
    #) -> list[list[dict]]:
    def access_database_files_locally(
        session_key,
        starttime,
        endtime,
        point,
        tables
    ):
        """
        Access MariaDB data directly by querying all MyISAM tables with .MYD files
        modified in the given time window, filtering by sensor ids in 'point'.

        If 'tables' is provided, only query those tables; otherwise fall back to most recent table.
    

        Returns a list (per sensor id) of dicts with keys 'ts', 'value', 'quality'.
        """

        logger.info("Accessing MariaDB directly — local SQL mode enabled.")
        workspace_name = 'eds_to_rjn'
        workspace_manager = WorkspaceManager(workspace_name)
        secrets_dict = SecretConfig.load_config(secrets_file_path=workspace_manager.get_secrets_file_path())
        #full_config = secrets_dict["eds_dbs"][session_key]
        #conn_config = {k: v for k, v in full_config.items() if k != "storage_path"}
        
        conn_config = secrets_dict["eds_dbs"][session_key]
        results = []

        try:
            logger.info("Attempting: mysql.connector.connect(**conn_config)")
            conn = mysql.connector.connect(**conn_config)
            cursor = conn.cursor(dictionary=True)

            # Determine which tables to query
            if tables is None:
                most_recent_table = get_most_recent_table(cursor, session_key.lower())
                if not most_recent_table:
                    logger.warning("No recent tables found.")
                    return [[] for _ in point]
                tables_to_query = [most_recent_table]
            else:
                tables_to_query = tables

            for table_name in tables_to_query:
                if not table_has_ts_column(conn, table_name, db_type="mysql"):
                    logger.warning(f"Skipping table '{table_name}': no 'ts' column.")
                    continue

                for point_id in point:
                    #logger.info(f"Querying table {table_name} for sensor id {point_id}")
                    query = f"""
                        SELECT ts, ids, tss, stat, val FROM `{table_name}`
                        WHERE ts BETWEEN %s AND %s AND ids = %s
                        ORDER BY ts ASC
                    """
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
            # hitting this in termux
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
        

def table_has_ts_column(conn, table_name, db_type="mysql"):
    if db_type == "sqlite":
        with conn.cursor() as cur:
            # your sqlite logic here
            cur.execute(f"PRAGMA table_info({table_name});")
            return any(row[1] == "ts" for row in cur.fetchall())
        pass
    elif db_type == "mysql":
        with conn.cursor() as cur:
            cur.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE 'ts'")
            result = cur.fetchall()
            return len(result) > 0
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    
#def identify_relevant_MyISM_tables(session_key: str, starttime: int, endtime: int, secrets_dict: dict) -> list:
# 3.8-safe, no hints
def identify_relevant_MyISM_tables(session_key, starttime, endtime, secrets_dict):
    #
    # Use the secrets file to control where your database can be found
    try:
        storage_dir = secrets_dict["eds_dbs"][str(session_key+"-config")]["storage_path"]
    except:
        logging.warning(f"User the secrets.yaml file to set the local database folder. Something like, storage_path: 'E:/SQLData/wwtf/'")
        return []
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

def identify_relevant_tables(session_key, starttime, endtime, secrets_dict):
    try:
        conn_config = secrets_dict["eds_dbs"][session_key]
        conn = mysql.connector.connect(**conn_config)
        cursor = conn.cursor(dictionary=True)
        # Use INFORMATION_SCHEMA instead of filesystem
        #return get_ten_most_recent_tables(cursor, conn_config["database"])
        return get_n_most_recent_tables(cursor, conn_config["database"], n=80)
    except mysql.connector.Error:
        logger.warning("Falling back to filesystem scan — DB not accessible.")
        return identify_relevant_MyISM_tables(session_key, starttime, endtime, secrets_dict)

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

#def get_ten_most_recent_tables(cursor, db_name, prefix='pla_') -> list[str]:
def get_ten_most_recent_tables(cursor, db_name, prefix='pla_'):
    """
    Get the 10 most recent tables with the given prefix.
    Returns a LIST OF STRINGS, not a single string.
    """
    query = f"""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME LIKE %s
        ORDER BY TABLE_NAME DESC
        LIMIT 10;
    """
    cursor.execute(query, (db_name, f'{prefix}%'))
    results = cursor.fetchall()
    
    # Extract table names as individual strings
    table_names = [result['TABLE_NAME'] for result in results]
    
    logger.info(f"Found {len(table_names)} recent tables with prefix '{prefix}': {table_names}")
    return table_names  # This is a LIST of strings: ['pla_68a98310', 'pla_68a97500', ...]


def get_n_most_recent_tables(cursor, db_name, n, prefix='pla_'):
    """
    Get the 10 most recent tables with the given prefix.
    Returns a LIST OF STRINGS, not a single string.
    """
    query = f"""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME LIKE %s
        ORDER BY TABLE_NAME DESC
        LIMIT {n};
    """
    cursor.execute(query, (db_name, f'{prefix}%'))
    results = cursor.fetchall()
    
    # Extract table names as individual strings
    table_names = [result['TABLE_NAME'] for result in results]
    
    logger.info(f"Found {len(table_names)} recent tables with prefix '{prefix}': {table_names}")
    return table_names  # This is a LIST of strings: ['pla_68a98310', 'pla_68a97500', ...]


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
    
    workspace_name = WorkspaceManager.identify_default_workspace_name()
    workspace_manager = WorkspaceManager(workspace_name)

    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    sessions = {}

    base_url_maxson = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("url").rstrip("/")
    session_maxson = EdsClient.login_to_session(api_url = base_url_maxson,
                                                username = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("username"),
                                                password = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("password"))
    session_maxson.base_url = base_url_maxson
    session_maxson.zd = secrets_dict.get("eds_apis", {}).get("Maxson", {}).get("zd")

    sessions.update({"Maxson":session_maxson})

    # Show example of what it would be like to start a second session (though Stiles API port 43084 is not accesible at this writing)
    if False:
        base_url_stiles = secrets_dict.get("eds_apis", {}).get("WWTF", {}).get("url").rstrip("/")
        session_stiles = EdsClient.login_to_session(api_url = base_url_stiles ,username = secrets_dict.get("eds_apis", {}).get("WWTF", {}).get("username"), password = secrets_dict.get("eds_apis", {}).get("WWTF", {}).get("password"))
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
        point_data = EdsClient.get_points_live_mod(session,iess)
        if point_data is None:
            raise ValueError(f"No live point returned for iess {iess}")
        else:
            row.update(point_data) 
        EdsClient.print_point_info_row(row)

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
        EdsClient.print_point_info_row(row)

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
    #from pipeline import gui_flaskplotly_live
    from pipeline import gui_fastapi_plotly_live

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
        load_historic_data()
    collector_thread = Thread(target=collect_loop, daemon=True)
    collector_thread.start()

    # Now run the GUI in the main thread
    #gui_flaskplotly_live.run_gui(data_buffer)
    gui_fastapi_plotly_live.run_gui(data_buffer)

@log_function_call(level=logging.DEBUG)    
def load_historic_data(session, filter_iess, starttime, endtime, step_seconds):    
    

    starttime = TimeManager(starttime).as_unix()
    endtime = TimeManager(endtime).as_unix() 
    logger.info(f"starttime = {starttime}")
    logger.info(f"endtime = {endtime}")


    point_list = filter_iess
    api_url = str(session.base_url) 
    request_id = EdsClient.create_tabular_request(session, api_url, starttime, endtime, points=point_list, step_seconds=step_seconds)
    if not request_id:
        logger.warning(f"Could not create tabular request for points: {point_list}")
        return []  # or None, depending on how you want the CLI to behave
    EdsClient.wait_for_request_execution_session(session, api_url, request_id)
    results = EdsClient.get_tabular_trend(session, request_id, point_list)
    logger.debug(f"len(results) = {len(results)}")
    return results
    
                

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
    export_path = workspace_manager.get_exports_file_path(filename = 'export_eds_points_neo.txt')
    EdsClient.save_points_export(point_export_decoded_str, export_path = export_path)
    print(f"Export file saved to: \n{export_path}") 

@log_function_call(level=logging.DEBUG)
def demo_eds_save_graphics_export():
    # Start sessions for your WWTPs
    workspace_manager, sessions = _demo_eds_start_session_CoM_WWTPs()
    session_maxson = sessions["Maxson"]

    # Get list of graphics from the EDS session
    graphics_list = EdsClient.get_graphics_list(session_maxson, session_maxson.base_url)
    print(f"Found {len(graphics_list)} graphics to export.")

    # Loop through each graphic and save it
    for graphic in graphics_list:
        graphic_name = graphic.get("name", os.path.splitext(graphic["file"])[0])
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in graphic_name)
        output_file_path = workspace_manager.get_exports_file_path(filename=f"{safe_name}.png")

        # Fetch and save the graphic
        graphic_bytes = EdsClient.get_graphic_export(session_maxson, session_maxson.base_url, graphic["file"])
        EdsClient.save_graphic_export(graphic_bytes, output_file_path)

        print(f"Saved graphic: {graphic_name} → {output_file_path}")

    print("All graphics exported successfully.")

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
        request_id = EdsClient.create_tabular_request(session, api_url, starttime, endtime, points=point_list)
        EdsClient.wait_for_request_execution_session(session, api_url, request_id)
        results = EdsClient.get_tabular_trend(session, request_id, point_list)
        session.post(f"{api_url}'/logout", verify=False)
        #
        for idx, iess in enumerate(point_list):
            print('\n{} samples:'.format(iess))
            for s in results[idx]:
                #print('{} {} {}'.format(datetime.fromtimestamp(s['ts']), round(s['value'],2), s['quality']))
                print('{} {} {}'.format(datetime.fromtimestamp(s['ts']), s['value'], s['quality']))
        queries_manager.update_success(api_id=key) # not appropriate here in demo without successful transmission to 3rd party API

@log_function_call(level=logging.DEBUG)
def demo_eds_local_database_access():
    from pipeline.queriesmanager import QueriesManager
    from pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_col
    workspace_name = 'eds_to_rjn' # workspace_name = WorkspaceManager.identify_default_workspace_name()
    workspace_manager = WorkspaceManager(workspace_name)
    queries_manager = QueriesManager(workspace_manager)
    queries_file_path_list = workspace_manager.get_default_query_file_paths_list() # use default identified by the default-queries.toml file
    logger.debug(f"queries_file_path_list = {queries_file_path_list}")

    queries_dictlist_unfiltered = load_query_rows_from_csv_files(queries_file_path_list)
    queries_defaultdictlist_grouped_by_session_key = group_queries_by_col(queries_dictlist_unfiltered,'zd')
    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    sessions_eds = {}

    # --- Prepare Stiles session_eds

    session_stiles = None # assume the EDS API session cannot be established
    sessions_eds.update({"WWTF":session_stiles})


    key_eds = "WWTF"
    session_key = key_eds
    session_eds = session_stiles
    point_list = [row['iess'] for row in queries_defaultdictlist_grouped_by_session_key.get(key_eds,[])]
    point_list_sid = [row['sid'] for row in queries_defaultdictlist_grouped_by_session_key.get(key_eds,[])]

    logger.info(f"point_list = {point_list}")
    # Discern the time range to use
    starttime = queries_manager.get_most_recent_successful_timestamp(api_id="WWTF")
    logger.info(f"queries_manager.get_most_recent_successful_timestamp(), key = {'WWTF'}")
    endtime = helpers.get_now_time_rounded(workspace_manager)
    starttime = TimeManager(starttime).as_unix()
    endtime = TimeManager(endtime).as_unix() 
    logger.info(f"starttime = {starttime}")
    logger.info(f"endtime = {endtime}")

    if EdsClient.this_computer_is_an_enterprise_database_server(secrets_dict, key_eds):
        tables = identify_relevant_tables(session_key, starttime, endtime, secrets_dict)
        results = EdsClient.access_database_files_locally(key_eds, starttime, endtime, point=point_list_sid, tables=tables)
    else:
        logger.warning("This computer is not an enterprise database server. Local database access will not work.")
        results = [[] for _ in point_list]
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

    response = EdsClient.get_license(session_maxson, api_url = session_maxson.base_url)
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
        "poetry run python -m pipeline.api.eds demo-point-export \n"
        "poetry run python -m pipeline.api.eds demo-tabular-export \n"
        "poetry run python -m pipeline.api.eds demo-live \n"
        "poetry run python -m pipeline.api.eds demo-live-alt \n"  
        "poetry run python -m pipeline.api.eds demo-trend \n"
        "poetry run python -m pipeline.api.eds demo-plot-live \n"
        "poetry run python -m pipeline.api.eds demo-webplot-live \n"
        "poetry run python -m pipeline.api.eds demo-plot-trend \n"
        "poetry run python -m pipeline.api.eds demo-db \n"
        "poetry run python -m pipeline.api.eds ping \n"
        "poetry run python -m pipeline.api.eds license \n"
        "poetry run python -m pipeline.api.eds export-graphics \n"
        "poetry run python -m pipeline.api.eds access-workspace")
    