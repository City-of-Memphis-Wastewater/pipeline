# main.py (or __main__.py)
from src.env import SecretsYaml
from src.api.eds import EdsClient
from src.api.rjn import RjnClient

def main():
    config_obj = SecretsYaml.load_config()
    
    eds = EdsClient(config_obj['eds_apis'])
    rjn = RjnClient(config_obj['rjn_api'])

    token_eds, headers_eds = eds.get_token()
    print(f"token_eds = {token_eds}")
    print(f"headers_eds = {headers_eds}")
    token_rjn = rjn.get_token()

if __name__ == "__main__":
    main()