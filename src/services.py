import requests
import json
from pprint import pprint
from datetime import datetime, timedelta
import sys
#import textual
from src.helpers import load_toml

#from src.address import Address
from src.eds_point import Point
post_to_rjn = True


def round_time_to_nearest_five(dt: datetime) -> datetime:
    allowed_minutes = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    # Find the largest allowed minute <= current minute
    rounded_minute = max(m for m in allowed_minutes if m <= dt.minute)
    return dt.replace(minute=rounded_minute, second=0, microsecond=0)

def populate_multiple_generic_points_from_filelist(filelist):
    for f in filelist:
        dic = load_toml(f)
        populate_generic_point_from_dict(dic)

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

def print_point_info_row(point_data, shortdesc):
    print(f'''{shortdesc}, sid:{point_data["sid"]}, idcs:{point_data["idcs"]}, dt:{datetime.fromtimestamp(point_data["ts"])}, un:{point_data["un"]}. av:{round(point_data["value"],2)}''')

def get_points_live(api_url,sid = int(),shortdesc = str(),headers = None):
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
    byte_string = request.content
    decoded_str = byte_string.decode('utf-8')
    data = json.loads(decoded_str) 
    #pprint(f"data={data}")
    points_datas = data.get("points", [])
    if not points_datas:
        print(f"{shortdesc}, sid:{sid}, no data returned, len(points)==0")
    else:
        for point_data in points_datas:
            print_point_info_row(point_data, shortdesc)

    

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