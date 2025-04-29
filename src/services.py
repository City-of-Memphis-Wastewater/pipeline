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
    # This expect a toml file which identified one point
    # Goal: expect a CSV file which identifies several points, one point per row
    for f in filelist:
        dic = load_toml(f)
        populate_generic_point_from_dict(dic)

def populate_multiple_generic_points_from_dicts(loaded_dicts):
    for dic in loaded_dicts:
        populate_generic_point_from_dict(dic)

def populate_generic_point_from_dict(dic):
    Point().populate_eds_characteristics(
        ip_address=dic["ip_address"],
        iess=dic["iess"],
        sid=dic["sid"],
        zd=dic["zd"]
    ).populate_manual_characteristics(
        shortdesc=dic["shortdesc"]
    ).populate_rjn_characteristics(
        rjn_siteid=dic["rjn_siteid"],
        rjn_entityid=dic["rjn_entityid"],
        rjn_name=dic["rjn_name"]
    )


if __name__ == "__main__":
    # Set up project manager
    from src.projectmanager import ProjectManager
    from src.queriesmanager import QueriesManager
    project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    queries_manager = QueriesManager(project_manager)
    query_file_paths = queries_manager.get_query_file_paths() # no args will use whatever is identified in default-query.toml
    populate_multiple_generic_points_from_filelist(filelist = query_file_paths)