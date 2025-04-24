import datetime
import json
from src.calls import make_request
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

        response = make_request(request_url, data)
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
        response = make_request(request_url, data, headers=headers, json = query)

    def show_points_live(api_url,sid = int(),shortdesc = str(),headers = None):
        request_url = api_url + 'points/query'
        query = {
            'filters' : [{
            'zd' : ['Maxson','WWTF'],
            'sid': [sid],
            'tg' : [0, 1],
            }],
            'order' : ['iess']
            }

        request = requests.post(request_url, headers = headers, json = query)
        #pprint(f"request={request}")
        byte_string = request.content
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
        