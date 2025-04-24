from datetime import datetime
import json
from src.calls import make_request
from pprint import pprint
class EdsClient:
    def __init__(self,config):
        self.config = config

    def get_token(self,plant_zd="Maxson"):
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

        response = make_request(url = request_url, data=data)
        token = response.json()['sessionId']
        headers = {'Authorization': f"Bearer {token}"}

        return token, headers

    def get_tabular_trend(self,plant_zd = "Maxson", iess = "M100FI.UNIT0@NET0", headers=None):
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
        #request = requests.post(request_url, headers = headers, json = query)
        response = make_request(url = request_url, data = data, headers=headers, json = query)

    def show_points_live(self,site: str,sid: int,shortdesc : str="",headers = None):
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

        #request = requests.post(request_url, headers = headers, data = query)
        response = make_request(url = request_url, headers=headers, data = query)
        #pprint(f"request={request}")
        byte_string = response.content
        decoded_str = byte_string.decode('utf-8')
        data = json.loads(decoded_str) 
        #pprint(f"data={data}")
        points_datas = data["points"]
        def print_point_info_row(sid,point_data):
                print(f'''{shortdesc}, sid:{point_data["sid"]}, idcs:{point_data["idcs"]}, dt:{datetime.fromtimestamp(point_data["ts"])}, un:{point_data["un"]}. av:{round(point_data["value"],2)}''')
        if len(points_datas)==0:
            print(f"{shortdesc}, sid:{sid}, no data returned, len(points)==0")
        elif len(points_datas)==1:
            # This is expected, that there is one point value returned for each SID, which is the match call.
            point_data = points_datas[0]
            print_point_info_row(sid,point_data)
        elif len(points_datas)>1:
            for point_data in points_datas:
                print_point_info_row(sid,point_data)
    

    def show_points_tabular_trend(self,site: str,sid: int,idcs:str, starttime :int,endtime:int,shortdesc : str="",headers = None):
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
            'iess' : f'{idcs}.UNIT0@NET0'
            },
            'shadePriority' : 'DEFAULT'
            }]
            }
        
        #request = requests.post(url = request_url, headers = headers, json = query)
        response = make_request(url = request_url, headers=headers, data = data, method="POST")
        byte_string = response.content
        decoded_str = byte_string.decode('utf-8')
        data = json.loads(decoded_str)
        pprint(data)
        pprint(f"data={data}")
        id = data["id"]
        pprint(f"id={id}")
        query = '?id={}'.format(id)
        data = {'id': id}
        request_url = api_url + 'trend/tabular' + query
        print(f"request_url = {request_url}")
        #response = make_request(url = request_url, data = data, headers=headers)
        response = make_request(url = request_url, headers=headers, method = "GET")
        #request = requests.get(request_url, headers=headers)
        byte_string = response.content
        print(f"byte_string = {byte_string}")
        decoded_str = byte_string.decode('utf-8')

        print(f"Status: {response.status_code}")
        #print("Response content (raw bytes):")
        #print(response.content)
        #print(f"decoded_str = {decoded_str}")
        print(decoded_str[:500])  # Print just a slice

        #data = json.loads(decoded_str)
        #pprint(f"data={data}")

    def get_points_export(self,site: str,sid: int=int(),idcs:str=str(), starttime :int=int(),endtime:int=int(),shortdesc : str="",headers = None):
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
