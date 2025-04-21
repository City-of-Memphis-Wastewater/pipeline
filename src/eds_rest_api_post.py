import requests
import json
from pprint import pprint
from datetime import datetime
import sys
#import textual

from address import Address
from eds_point import Point
post_to_rjn = True

class ApiCalls:
    ip_address_maxson = "172.19.4.127"
    ip_address_stiles = "172.19.4.128"

    def __init__(self,ip_address_default = "172.19.4.127"):
        self.ip_address_default = ip_address_default

    def test_connection_to_internet():
        try:
            # call Cloudflare's CDN test site, because it is lite.
            response = requests.get("http://1.1.1.1", timeout = 5)
            print("You are connected to the internet.")
        except:
            print(f"It appears you are not connected to the internet.")
            sys.exit()

    def test_connection_to_eds():
        for api_url in Address.get_rest_api_url_list():
            try:
            #if True:
                api_url = "http://172.19.4.127:43084/api/v1/"
                login_url = api_url+"login"
                data = {'username' : 'admin', 'password' : '', 'type' : 'rest client'}
                response = requests.post(login_url, json = data)
                #print(f"Status Code: {response.status_code}")
                #print(f"Response Text: '{response.text}'")
                if response.status_code == 200:
                    try:
                        token = response.json()
                    except json.JSONDecodeError:
                        print("Failed to parse JSON:")
                        token = None
                #request_url = api_url + 'ping'
                #headers = {'Authorization' : 'Bearer {}'.format(token['sessionId'])}
                #response = requests.get(request_url, headers = headers)

                print(f"You are able to access an EDS: {api_url}") 
            #else:
            except:
                print(f"Connection to an EDS is failing: {api_url}")
                sys.exit()

    def get_license(api_url,header):
        request_url = api_url + 'license'
        request = requests.get(request_url, headers=header)
        return request

    def get_token(ip_address):
        Address.set_ip_address(ip_address)
        api_url = Address.get_rest_api_url() # if none, use known, if else, us Address.get_current_ip_address()
        request_url = api_url + 'login'
        data = {'username' : 'admin', 'password' : '', 'type' : 'rest client'}
        #data = {'username' : 'rjn', 'password' : 'RjnClarity2025', 'type' : 'rest client'}  
        response = requests.post(request_url, json = data)
        #print(f"response={response}")
        token = json.loads(response.text)
        headers = {'Authorization' : 'Bearer {}'.format(token['sessionId'])}
        return api_url,headers

def run_today():
    ApiCalls.test_connection_to_internet()
    ApiCalls.test_connection_to_eds()
    api = ApiCalls(ip_address_default = "172.19.4.127")
    api_url,headers = ApiCalls.get_token(ip_address = ApiCalls.ip_address_maxson)
    populate_today()  
    retrieve_and_show_points(option=0) # live [0] or tabular [1]
    #retrieve_and_show_points(option=1)

def populate_multiple_generic_points_from_dicts(loaded_dicts):
    for dic in loaded_dicts:
        populate_generic_point_from_dict(dic)

def populate_generic_point_from_dict(dic):
    Point().populate_eds_characteristics(
        ip_address=dic["ip_address"],
        idcs=dic["idcs"],
        sid=dic["sid"],
        zd=dic["zd"]
    ).populate_manual_characteristics(
        shortdesc=dic["shortdesc"]
    ).populate_rjn_characteristics(
        rjn_siteid=dic["rjn_siteid"],
        rjn_entityid=dic["rjn_entityid"],
        rjn_name=dic["rjn_name"]
    )
def populate_today():
    #Point(ip_address="172.19.4.128",idcs="FI-405/415",sid="3550",zd="WWTF",rjn_siteid="eefe228a-39a2-4742-a9e3-c07314544ada",rjn_entityid="s197",rjn_name="Effluent") # failing
    #Point(ip_address="172.19.4.128",idcs="I-5005A",sid="5392",zd="WWTF",rjn_siteid="eefe228a-39a2-4742-a9e3-c07314544ada",rjn_entityid="s200",rjn_name="Influent") # failing
    #Point(ip_address="172.19.4.127",idcs="M310LI",sid=2382,zd="Maxson",rjn_siteid="64c5c5ac-04ca-4a08-bdce-5327e4b21bc5",rjn_entityid=None,rjn_name="Wet well level")
    #Point(ip_address="172.19.4.127",idcs="PAA-DOSE-EAST-PPM",sid=11002,zd="Maxson",rjn_siteid="64c5c5ac-04ca-4a08-bdce-5327e4b21bc5",rjn_entityid=None,rjn_name="PAA Dose East")

    Point().populate_eds_characteristics(
        ip_address="172.19.4.127",
        idcs="FI8001",
        sid=8528,
        zd="Maxson"
    ).populate_manual_characteristics(
        shortdesc="EFF"
    ).populate_rjn_characteristics(
        rjn_siteid="64c5c5ac-04ca-4a08-bdce-5327e4b21bc5",
        rjn_entityid="s198",
        rjn_name="Effluent"
    )

    Point().populate_eds_characteristics(
        ip_address="172.19.4.127",
        idcs="M100FI",
        sid=2308,
        zd="Maxson"
    ).populate_manual_characteristics(
        shortdesc="INFLU"
    ).populate_rjn_characteristics(
        rjn_siteid="64c5c5ac-04ca-4a08-bdce-5327e4b21bc5",
        rjn_entityid="s199",
        rjn_name="Influent")
    
    Point().populate_eds_characteristics(
        ip_address="172.19.4.127",
        idcs="M310LI",
        sid=2382,
        zd="Maxson"
    ).populate_manual_characteristics(
        shortdesc="WETWELL"
    ).populate_rjn_characteristics(
        rjn_siteid="64c5c5ac-04ca-4a08-bdce-5327e4b21bc5",
        rjn_entityid=None,
        rjn_name=None)
    
    Point().populate_eds_characteristics(
        ip_address="172.19.4.127",
        idcs="D-321E",
        sid=11003,
        zd="Maxson"
    ).populate_manual_characteristics(
        shortdesc="DOSE"
    ).populate_rjn_characteristics(
        rjn_siteid="64c5c5ac-04ca-4a08-bdce-5327e4b21bc5",
        rjn_entityid=None,
        rjn_name=None)

def retrieve_and_show_points(option = "live"):
    sid_list = [p.sid for p in Point.get_point_set()]
    print(f"sid_list = {sid_list}")
    pprint(Point.get_point_set())
    for point_object in Point.get_point_set():
        if option == "live" or option == 0: 
            show_points_live(api_url=Address.get_rest_api_url(),headers = Address.get_header(),point_object=point_object,)
        if option == "tabular" or option == 1:
            show_points_tabular_trend(api_url=Address.get_rest_api_url(),headers = Address.get_header(),point_object=point_object,)

def show_points_live(api_url,point_object,headers):
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
    decoded_str = byte_string.decode('utf-8')
    data = json.loads(decoded_str) 
    #pprint(f"data={data}")
    points_datas = data["points"]
    def print_point_info_row(point_object,point_data):
            print(f'''{point_object.shortdesc}, sid:{point_data["sid"]}, idcs:{point_data["idcs"]}, dt:{datetime.fromtimestamp(point_data["ts"])}, un:{point_data["un"]}. av:{round(point_data["value"],2)}''')
    if len(points_datas)==0:
        print(f"{point_object.shortdesc}, sid:{point_object.sid}, no data returned, len(points)==0")
    elif len(points_datas)==1:
        # This is expected, that there is one point value returned for each SID, which is the match call.
        point_data = points_datas[0]
        print_point_info_row(point_object,point_data)
    elif len(points_datas)>1:
        for point_data in points_datas:
            print_point_info_row(point_object,point_data)
    

def show_points_tabular_trend(api_url,point_object,headers):
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



if __name__ == "__main__":
    run_today()