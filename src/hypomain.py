# main.py (or __main__.py)
from src.env import SecretsYaml
from src.api.eds import EdsClient
from src.api.rjn import RjnClient
from src.calls import test_connection_to_internet
#from src.services import show_points_live

def main():

    test_connection_to_internet()
    config_obj = SecretsYaml.load_config()
    
    eds = EdsClient(config_obj['eds_apis'])
    rjn = RjnClient(config_obj['rjn_api'])
    
    token_eds, headers_eds = eds.get_token()
    print(f"token_eds = {token_eds}")
    print(f"headers_eds = {headers_eds}")
    token_rjn, headers_rjn = rjn.get_token()
    print(f"token_rjn = {token_rjn}")
    print(f"headers_rjn = {headers_rjn}")

    #get_sid_list() # from csv or xlsx file, for Don Hudgins - check typical export scheme

    #show_points_live()


if __name__ == "__main__":
    main()