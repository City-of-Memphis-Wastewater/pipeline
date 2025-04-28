# main.py (or __main__.py)
from datetime import datetime
import csv

from src.env import SecretsYaml
from src.api.eds import EdsClient
from src.api.rjn import RjnClient
from src.calls import test_connection_to_internet
from src.services import round_time_to_nearest_five
from src.projectmanager import ProjectManager
from src.queriesmanager import QueriesManager
from src.points_loader import PointsCsvLoader
from src.api.rjn import send_data_to_rjn
from src.api.eds import fetch_eds_data

def chonka():
    test_connection_to_internet()

    project_name = 'eds_to_rjn'
    project_manager = ProjectManager(project_name)
    secrets_file_path = project_manager.get_configs_file_path(filename = 'secrets.yaml')
    config_obj = SecretsYaml.load_config(secrets_file_path = secrets_file_path)
    csv_file_path = project_manager.get_queries_file_path(filename='points.csv')

    eds_api, headers_eds_maxson = get_eds_maxson_token_and_headers(config_obj)
    #eds, headers_eds_maxson, headers_eds_stiles = get_eds_tokens_and_headers(config_obj)
    headers_eds_stiles = None
    rjn_api, headers_rjn = get_rjn_tokens_and_headers(config_obj)

    process_sites_and_send(csv_file_path, eds_api, eds_site = "Maxson", eds_headers = headers_eds_maxson, rjn_base_url=rjn_api.config['url'], rjn_headers=headers_rjn)

    
def main():

    test_connection_to_internet()

    project_name = 'eds_to_rjn'
    project_manager = ProjectManager(project_name)
    secrets_file_path = project_manager.get_configs_file_path(filename = 'secrets.yaml')
    config_obj = SecretsYaml.load_config(secrets_file_path = secrets_file_path)
    
    #eds, headers_eds_maxson, headers_eds_stiles = get_eds_tokens_and_headers(config_obj)
    eds, headers_eds_maxson = get_eds_maxson_token_and_headers(config_obj)
    if False:
        queries_manager = QueriesManager(project_manager) # check file pointed to by default-query.toml
        queries_manager.load_queries_from_default_queries_file()
    else:
        #call_eds_get_points_live(eds, headers_eds_maxson, headers_eds_stiles)
        call_eds_maxson_get_points_live(eds, headers_eds_maxson)

    rjn, headers_rjn = get_rjn_tokens_and_headers(config_obj)

    
    if False:
        decoded_str = eds.get_points_export(site = "Maxson",headers = headers_eds)
        export_file_path = project_manager.get_exports_file_path(filename = 'export_eds_points_all.txt')
        eds.save_points_export(decoded_str, export_file_path = export_file_path)
        print(f"Export file will be saved to: {export_file_path}")

def get_all_tokens(config_obj):
    # toml headings
    eds = EdsClient(config_obj['eds_apis']) 
    rjn = RjnClient(config_obj['rjn_api'])
    
    token_eds, headers_eds_maxson = eds.get_token(plant_zd="Maxson")
    token_eds, headers_eds_stiles = eds.get_token(plant_zd="WWTF")
    print(f"token_eds = {token_eds}")
    #print(f"headers_eds = {headers_eds}")
    token_rjn, headers_rjn = rjn.get_token()
    print(f"token_rjn = {token_rjn}")
    return eds, rjn, headers_eds_maxson, headers_eds_stiles, headers_rjn

def get_eds_tokens_and_headers(config_obj):
    # toml headings
    eds = EdsClient(config_obj['eds_apis'])
    token_eds, headers_eds_maxson = eds.get_token(plant_zd="Maxson")
    token_eds, headers_eds_stiles = eds.get_token(plant_zd="WWTF")
    return eds, headers_eds_maxson, headers_eds_stiles

def get_eds_maxson_token_and_headers(config_obj):
    # toml headings
    eds = EdsClient(config_obj['eds_apis'])
    token_eds, headers_eds_maxson = eds.get_token(plant_zd="Maxson")
    return eds, headers_eds_maxson

def get_rjn_tokens_and_headers(config_obj):
    # toml headings
    rjn = RjnClient(config_obj['rjn_api'])
    token_rjn, headers_rjn = rjn.get_token()
    print(f"token_rjn = {token_rjn}")
    return rjn, headers_rjn

def call_eds_get_points_live(eds,headers_eds_maxson, headers_eds_stiles):
    print(f"\neds.get_points_live():")
    eds.get_points_live(site = "Maxson", sid = 2308,shortdesc = "INFLUENT",headers = headers_eds_maxson) # M100FI.UNIT0@NET0
    eds.get_points_live(site = "Maxson", sid = 8528,shortdesc = "EFFLUENT",headers = headers_eds_maxson) # FI8001.UNIT0@NET0
    eds.get_points_live(site = "WWTF", sid = 5392,shortdesc = "INFLUENT",headers = headers_eds_stiles) # I-5005A.UNIT1@NET1
    eds.get_points_live(site = "WWTF", sid = 3550,shortdesc = "EFFLUENT",headers = headers_eds_stiles) # FI-405/415.UNIT1@NET1

def call_eds_maxson_get_points_live(eds,headers_eds_maxson):
    print(f"\neds.get_points_live():")
    eds.get_points_live(site = "Maxson", sid = 2308,shortdesc = "INFLUENT",headers = headers_eds_maxson) # M100FI.UNIT0@NET0
    eds.get_points_live(site = "Maxson", sid = 8528,shortdesc = "EFFLUENT",headers = headers_eds_maxson) # FI8001.UNIT0@NET0

def call_eds_stiles_get_points_live(eds, headers_eds_stiles):
    print(f"\neds.get_points_live():")
    eds.get_points_live(site = "WWTF", sid = 5392,shortdesc = "INFLUENT",headers = headers_eds_stiles) # I-5005A.UNIT1@NET1
    eds.get_points_live(site = "WWTF", sid = 3550,shortdesc = "EFFLUENT",headers = headers_eds_stiles) # FI-405/415.UNIT1@NET1

# runner
def process_points_and_send_to_rjn(csv_file_path, eds: EdsClient, rjn: RjnClient, headers_eds_maxson, headers_eds_stiles):
    loader = PointsCsvLoader(csv_file_path)
    points_list = loader.load_points()

    for point in points_list:
        site = point['zd']
        sid = int(point['sid'])
        shortdesc = point['shortdesc']

        if site == "Maxson":
            headers = headers_eds_maxson
        elif site == "WWTF":
            headers = headers_eds_stiles
        else:
            print(f"Unknown site {site}")
            continue

        point_data = eds.get_points_live(site=site, sid=sid, shortdesc=shortdesc, headers=headers)
        if point_data:
            payload = {
                "rjn_siteid": point['rjn_siteid'],
                "rjn_entityid": point['rjn_entityid'],
                "rjn_name": point['rjn_name'],
                "timestamp": round_time_to_nearest_five(datetime.fromtimestamp(point_data["ts"])).isoformat(),
                "value": point_data["value"],
                "units": point_data["un"],
                "source_sid": sid,
                "source_iess": point_data["idcs"]
            }
            rjn.send_point(payload)
            print(f"Posted point {payload['rjn_name']} to RJN.")
        else:
            print(f"No point data found for SID {sid}")

def process_sites_and_send(csv_path, eds_api, eds_site, eds_headers, rjn_base_url, rjn_headers):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                eds_sid = int(row["sid"])
                shortdesc = row.get("shortdesc", "")
                rjn_siteid = row["rjn_siteid"]
                rjn_entityid = row["rjn_entityid"]
            except KeyError as e:
                print(f"Missing expected column in CSV: {e}")
                continue

            try:
                ts, value = fetch_eds_data(
                    eds_api=eds_api,
                    site=eds_site,
                    sid=eds_sid,
                    shortdesc=shortdesc,
                    headers=eds_headers
                )

                if value is None:
                    print(f"Skipping null value for SID {eds_sid}")
                    continue

                dt = datetime.fromtimestamp(ts)
                rounded_dt = round_time_to_nearest_five(dt)
                timestamp = rounded_dt

                send_data_to_rjn(
                    base_url=rjn_base_url,
                    project_id=rjn_siteid,
                    entity_id=rjn_entityid,
                    headers=rjn_headers,
                    timestamp=timestamp,
                    value=round(value, 2)
                )
            except Exception as e:
                print(f"Error processing SID {eds_sid}: {e}")

def post_captured_values_from_eds_to_rjn():
    pass
def load_data_from_file():
    pass
if __name__ == "__main__":
    #main()
    chonka()
