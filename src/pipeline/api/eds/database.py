"""
Migrated manually from eds.py by Clayton on 1 December 2025
Moving these means that the references must be changed for the currently running code. 
However, this should become a non-issue once we call the EDS SOAP API instead of the REST API or the local db files. 

We would like to move away from this and just use the SOAP api.
"""
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import logging
import typer
import pyhabitat as ph

from pipeline.api.eds.rest.client import EdsRestClient
from pipeline.decorators import log_function_call

logger = logging.getLogger(__name__)
if ph.on_windows():
    import mysql.connector
else:
    pass


def _get_eds_local_db_credentials(service_name = "pipeline-eds-local-database",item_name = "eds_dbs") -> dict:
        return {}
    
def access_database_files_locally(
    session_key: str,
    starttime: int,
    endtime: int,
    point: list[int],
    tables: list[str] | None = None
) -> list[list[dict]]:

    from pipeline.api.eds.rest.alarm import decode_stat
    """
    Access MariaDB data directly by querying all MyISAM tables with .MYD files
    modified in the given time window, filtering by sensor ids in 'point'.

    If 'tables' is provided, only query those tables; otherwise fall back to most recent table.

    Returns a list (per sensor id) of dicts with keys 'ts', 'value', 'quality'.

    This is provided as a fallback if API access fails.
    """

    logger.info("Accessing MariaDB directly — local SQL mode enabled.")
    workspace_name = 'eds_to_rjn'
    workspace_manager = WorkspaceManager(workspace_name)

    local_database_dict = EdsRestClient._get_eds_local_db_credentials(service_name = "pipeline-eds-local-database",item_name = "eds_dbs")
    if not isinstance(local_database_dict,dict) or len(local_database_dict):
        typer.echo("Please develop _get_eds_local_db_credentials() to return a JSON-like dict structure, " \
        "after drawing database credentials from the keyring and compiling them into a dictionary. " \
        "And then, make the function defunct, " \
        "by implementing prompt or loading of each " \
        "secure credentialed string to at the point of sale, " \
        "with clear documentation but not and intermediate helper-funciton. " \
        "In this way, " \
        "we avoid spaghetti code and tie the demand for " \
        "information closely to the source for information." \
        "Implement the argument 'forget', "
        "if you do not want the value saved to the plaintext config file or " \
        "the cryptography-secure store credentials. ")
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

def this_computer_is_an_enterprise_database_server(secrets_dict: dict, session_key: str) -> bool:
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

@log_function_call(level=logging.DEBUG)
def demo_eds_local_database_access():
    from pipeline.queriesmanager import QueriesManager
    from pipeline.queriesmanager import load_query_rows_from_csv_files, group_queries_by_col
    #from pipeline.api.eds.database import this_computer_is_an_enterprise_database_server, identify_relevant_tables, access_database_files_locally
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

    if this_computer_is_an_enterprise_database_server(secrets_dict, key_eds):
        tables = identify_relevant_tables(session_key, starttime, endtime, secrets_dict)
        results = access_database_files_locally(key_eds, starttime, endtime, point=point_list_sid, tables=tables)
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
                #EdsRestClient.print_point_info_row(row)

                dt = datetime.fromtimestamp(row["ts"])
                timestamp_str = helpers.round_datetime_to_nearest_past_five_minutes(dt).isoformat(timespec='seconds')
                if row['quality'] == 'G':
                    timestamps.append(timestamp_str)
                    values.append(round(row["value"],5)) # unrounded values fail to post
            print(f"final row = {row}")
        else:
            print("No data rows for this point")

    
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


