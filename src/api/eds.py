from datetime import datetime
import json
from src.calls import make_request
from pprint import pprint
class EdsClient:
    def __init__(self,config):
        self.config = config

    def get_token_and_headers(self,plant_zd="Maxson"):
        print("\nEdsClient.get_token_and_headers()")
        try:
            plant_cfg = self.config[plant_zd]
        except KeyError:
            raise ValueError(f"Unknown plant_zd '{plant_zd}'")

        request_url = plant_cfg['url'] + 'login'
        print(f"request_url = {request_url}")
        data = {
            'username': plant_cfg['username'],
            'password': plant_cfg['password'],
            'type': 'rest client'
        }

        response = make_request(url = request_url, data=data)
        token = response.json()['sessionId']
        headers = {'Authorization': f"Bearer {token}"}

        return token, headers

    def get_license(self,site:str,headers=None):
        plant_cfg = self.config[site]
        request_url = plant_cfg['url'] + 'license'
        response = make_request(url = request_url, headers=headers, method = "GET", data = {})
        pprint(response.__dict__)
        return response

    def print_point_info_row(self,point_data, shortdesc):
        print(f'''{shortdesc}, sid:{point_data["sid"]}, iess:{point_data["iess"]}, dt:{datetime.fromtimestamp(point_data["ts"])}, un:{point_data["un"]}. av:{round(point_data["value"],2)}''')


    def get_points_live(self,site: str,sid: int,shortdesc : str="",headers = None):
        "Access live value of point from the EDS, based on site value (i.e. Maxson or WWTF (Stiles))"
        print(f"\nEdsClient.get_points_live")
        api_url = str(self.config[site]["url"])
        request_url = api_url + 'points/query'
        print(f"request_url = {request_url}")
        query = {
            'filters' : [{
            'zd' : ['Maxson','WWTF'],
            'sid': [sid],
            'tg' : [0, 1],
            }],
            'order' : ['iess']
            }

        response = make_request(url = request_url, headers=headers, data = query)
        byte_string = response.content
        decoded_str = byte_string.decode('utf-8')
        data = json.loads(decoded_str) 
        #pprint(f"data={data}")
        points_datas = data.get("points", [])
        if not points_datas:
            print(f"{shortdesc}, sid:{sid}, no data returned, len(points)==0")
        else:
            for point_data in points_datas:
                self.print_point_info_row(point_data, shortdesc)
        return points_datas[0]  # You expect exactly one point usually
    
    def get_tabular_trend(self,plant_zd = "Maxson", iess = "M100FI.UNIT0@NET0", headers=None):
        "Failed"
        try:
            plant_cfg = self.config[plant_zd]
        except KeyError:
            raise ValueError(f"Unknown plant_zd '{plant_zd}'")
        
        request_url = plant_cfg['url'] + 'login'
        data = {
            'username': plant_cfg['username'],
            'password': plant_cfg['password'],
            'type': 'rest client'
        }
        query = {
            "filters": [{"zd": [plant_zd], "tg": [0, 1]}],
            "order": [iess]
        
        }
        response = make_request(url = request_url, data = data, headers=headers, json = query)

    def show_points_tabular_trend(self,site: str,sid: int,iess:str, starttime :int,endtime:int,shortdesc : str="",headers = None):
        "Failed"
        if not starttime:
            starttime = 1744661000, # hardcoded, demo
        if not endtime:
            endtime = 1744661700 
        api_url = str(self.config[site]["url"])
        #idcs = "M100FI" # get from csv lookup

        request_url = api_url + 'trend/tabular'
        
        data = {
            'period' : {
            'from' : starttime,
            'till' : endtime
            },
            'step' : 1,
            'items' : [{
            'pointId' : {
            'sid' : sid,
            'iess' : f'{iess}.UNIT0@NET0'
            },
            'shadePriority' : 'DEFAULT'
            }]
            }
        
        response = make_request(url = request_url, headers=headers, data = data, method="POST")
        byte_string = response.content
        decoded_str = byte_string.decode('utf-8')
        data = json.loads(decoded_str)
        pprint(data)
        pprint(f"data={data}")
        id = data["id"] # query id, to reference an existing process, see page 36 of EDS REST API Python Examples.pdf.
        pprint(f"id={id}")
        query = '?id={}'.format(id)
        #data = {'id': id} # already true
        #request_url = api_url + 'trend/tabular' + query
        request_url = api_url + 'events/read' + query
        print(f"request_url = {request_url}")
        response = make_request(url = request_url, headers=headers, method = "GET") # includes the query id in the url
        byte_string = response.content
        print(f"byte_string = {byte_string}")
        decoded_str = byte_string.decode('utf-8')
        print(f"Status: {response.status_code}")
        print(decoded_str[:500])  # Print just a slice

        #print("Response content (raw bytes):")
        #print(response.content)
        #print(f"decoded_str = {decoded_str}")
        #data = json.loads(decoded_str)
        #pprint(f"data={data}")

    def get_points_export(self,site: str,sid: int=int(),iess:str=str(), starttime :int=int(),endtime:int=int(),shortdesc : str="",headers = None):
        "Success"
        api_url = str(self.config[site]["url"])
        zd = site
        iess = ''
        order = 'iess'
        query = '?zd={}&iess={}&order={}'.format(zd, iess, order)
        request_url = api_url + 'points/export' + query
        response = make_request(url = request_url, headers=headers, method="GET")
        byte_string = response.content
        decoded_str = byte_string.decode('utf-8')
        #print(f"Status: {response.status_code}")
        #print("Response content (raw bytes):")
        #print(response.content)
        #print(f"decoded_str = {decoded_str}")
        #print(decoded_str[:500])  # Print just a slice

        return decoded_str

    def save_points_export(self,decoded_str, export_file_path):
        lines = decoded_str.strip().splitlines()

        with open(export_file_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")  # Save each line in the text file


def fetch_eds_data(eds_api, site, sid, shortdesc, headers):
    point_data = eds_api.get_points_live(site=site, sid=sid, shortdesc=shortdesc, headers=headers)
    if point_data is None:
        raise ValueError(f"No live point returned for SID {sid}")
    ts = point_data["ts"]
    value = point_data["value"]
    return ts, value

def demo_eds_save_point_export():
    from src.env import SecretsYaml
    from src.projectmanager import ProjectManager
    from src.queriesmanager import QueriesManager
    project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    secrets_file_path = project_manager.get_configs_file_path(filename = 'secrets.yaml')
    config_obj = SecretsYaml.load_config(secrets_file_path = secrets_file_path)
    eds = EdsClient(config_obj['eds_apis'])
    token_eds, headers_eds_maxson = eds.get_token_and_headers(plant_zd="Maxson")
    decoded_str = eds.get_points_export(site = "Maxson",headers = headers_eds_maxson)
    export_file_path = project_manager.get_exports_file_path(filename = 'export_eds_points_all.txt')
    eds.save_points_export(decoded_str, export_file_path = export_file_path)
    print(f"Export file will be saved to: {export_file_path}")

def __main__():
    demo_eds_save_point_export()