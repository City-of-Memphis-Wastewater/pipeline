# main.py (or __main__.py)
from src.env import SecretsYaml
from src.api.eds import EdsClient
from src.api.rjn import RjnClient
from src.calls import test_connection_to_internet
from src.projectmanager import ProjectManager

def main():

    test_connection_to_internet()

    project_name = 'eds_to_rjn'
    project_manager = ProjectManager(project_name)
    secrets_file_path = project_manager.get_configs_file_path(filename = 'secrets.yaml')
    config_obj = SecretsYaml.load_config(secrets_file_path = secrets_file_path)
    #secrets = SecretsYaml(config_obj)
    #secrets.print_config()
    

    eds = EdsClient(config_obj['eds_apis'])
    rjn = RjnClient(config_obj['rjn_api'])
    
    token_eds, headers_eds = eds.get_token()
    print(f"token_eds = {token_eds}")
    #print(f"headers_eds = {headers_eds}")
    token_rjn, headers_rjn = rjn.get_token()
    print(f"token_rjn = {token_rjn}")
    #print(f"headers_rjn = {headers_rjn}")

    #get_sid_list() # from csv or xlsx file, for Don Hudgins - check typical export scheme

    #show_points_live()
    eds.show_points_live(site = "Maxson", sid = 2308,shortdesc = "INFLUENT",headers = headers_eds)
    #eds.show_points_live(site = "Maxson", iess = "M100FI.UNIT0@NET0",headers = headers_eds)
    eds.show_points_tabular_trend(site = "Maxson", sid = 2308,idcs = "M100FI",starttime = 1745516074, endtime = 1745433274,headers = headers_eds)

    decoded_str = eds.get_points_export(site = "Maxson",headers = headers_eds)
    export_file_path = project_manager.get_exports_file_path(filename = 'export_eds_points.txt')
    eds.save_points_export(decoded_str, export_file_path = export_file_path)
    print(f"Export file will be saved to: {export_file_path}")

if __name__ == "__main__":
    main()
