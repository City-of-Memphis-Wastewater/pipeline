import requests
import json
from pprint import pprint
from datetime import datetime

post_to_rjn = True
class Point:
    point_dict = dict()
    @classmethod
    def add_to_point_dict(cls,self):
        cls.point_dict.update({self.sid:self})
    def __init__(self):
        self.ip_address = str()
        self.idcs = str()
        self.sid = int()
        self.zd = int()
        self.rjn_siteid = str()
        self.rjn_entityid = str()
        self.rjn_name= str()
    def __init__(self,ip_address,idcs,sid,zd,rjn_siteid,rjn_entityid,rjn_name):
        self.ip_address = ip_address
        self.idcs = idcs
        self.sid = sid
        self.zd = zd
        self.rjn_siteid = rjn_siteid
        self.rjn_entityid = rjn_entityid
        self.rjn_name= rjn_name
        self.add_to_point_dict(self)
    def set_value(self,value = float()):
        self.value = value
        #self.timestamp = 


#Point(ip_address="172.19.4.128",idcs="FI-405/415",sid="3550",zd="WWTF",rjn_siteid="eefe228a-39a2-4742-a9e3-c07314544ada",rjn_entityid="s197",rjn_name="Effluent") # failing
#Point(ip_address="172.19.4.128",idcs="I-5005A",sid="5392",zd="WWTF",rjn_siteid="eefe228a-39a2-4742-a9e3-c07314544ada",rjn_entityid="s200",rjn_name="Influent") # failing
Point(ip_address="172.19.4.127",idcs="FI8001",sid=8528,zd="Maxson",rjn_siteid="64c5c5ac-04ca-4a08-bdce-5327e4b21bc5",rjn_entityid="s198",rjn_name="Effluent")
Point(ip_address="172.19.4.127",idcs="M100FI",sid=2308,zd="Maxson",rjn_siteid="64c5c5ac-04ca-4a08-bdce-5327e4b21bc5",rjn_entityid="s199",rjn_name="Influent")
#Point(ip_address="172.19.4.127",idcs="M310LI",sid=2382,zd="Maxson",rjn_siteid="64c5c5ac-04ca-4a08-bdce-5327e4b21bc5",rjn_entityid=None,rjn_name="Wet well level")
#Point(ip_address="172.19.4.127",idcs="PAA-DOSE-EAST-PPM",sid=11002,zd="Maxson",rjn_siteid="64c5c5ac-04ca-4a08-bdce-5327e4b21bc5",rjn_entityid=None,rjn_name="PAA Dose East")

sid_list = [int(x) for x in list(Point.point_dict.keys())]
print(f"sid_list = {sid_list}")

for point_object in Point.point_dict.values():
    #api_url = 'http://localhost:43084/api/v1/'
    #api_url = 'http://172.19.4.127:43084/api/v1/'
    api_url = f'http://{point_object.ip_address}:43084/api/v1/'
    request_url = api_url + 'login'
    data = {'username' : 'admin', 'password' : '', 'type' : 'rest client'}
    #data = {'username' : 'rjn', 'password' : 'RjnClarity2025', 'type' : 'rest client'}  
    response = requests.post(request_url, json = data)
    #print(f"response={response}")
    token = json.loads(response.text)
    headers = {'Authorization' : 'Bearer {}'.format(token['sessionId'])}
    if True:
        request_url = api_url + 'points/query'
        query = {
            'filters' : [{
            'zd' : ['Maxson','WWTF'],
            'sid': [point_object.sid],
            'tg' : [0, 1],
            }],
            'order' : ['iess']
            }

        request = requests.post(request_url, headers = headers, json = query)
        #pprint(f"request={request}")
        byte_string = request.content
        #pprint(f"byte_string={byte_string}")
        decoded_str = byte_string.decode('utf-8')
        data = json.loads(decoded_str) 
        #pprint(f"data={data}")
        points = data["points"]

        i=0
        print(f'''value:{points[i]["value"]},idcs:{points[i]["idcs"]},sid:{points[i]["sid"]},quality:{points[i]["quality"]},desc:{points[i]["desc"]},ts:{points[i]["ts"]},dt:{datetime.fromtimestamp(points[i]["ts"])}''')
        #point_object.rjn_

        #if post_to_rjn is True:
    else:
        request_url = api_url + 'trend/tabular'
        query = {
            'period' : {
            'from' : 1744661000,
            'till' : 1744661700
            },
            'step' : 60,
            'items' : [{
            'pointId' : {
            'sid' : point_object.sid,
            'iess' : f'{point_object.idcs}@NET0'
            },
            'shadePriority' : 'DEFAULT'
            }]
            }
        request = requests.post(request_url, headers = headers, json = query)
        byte_string = request.content
        decoded_str = byte_string.decode('utf-8')
        data = json.loads(decoded_str)
        pprint(f"data={data}")
        id = data["id"]
        pprint(f"id={id}")
        query = '?id={}'.format(id)
        request_url = api_url + 'events/read' + query
        request = requests.get(request_url, headers=headers)
        byte_string = request.content
        decoded_str = byte_string.decode('utf-8')
        data = json.loads(decoded_str)
        pprint(f"data={data}")