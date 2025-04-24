#env.__main__.py
 
import os, sys
import requests
import json
import yaml

from dotenv import load_dotenv
def load_env():
    load_dotenv(dotenv_path=".env")

PLANT_CONFIG = {
    "Maxson": {
        "url_key": "EDS_API_URL_127",
        "user_key": "EDS_API_USERNAME_127",
        "pass_key": "EDS_API_PASSWORD_127",
    },
    "Stiles": {
        "url_key": "EDS_API_URL_128",
        "user_key": "EDS_API_USERNAME_128",
        "pass_key": "EDS_API_PASSWORD_128",
    },
}

class SecretsEnv:
    @staticmethod
    def get_token_eds_env(plant_zd="Maxson"):
        # Show a record of the EDS env keys, for posterity, and hardcode the selection with an plant_integer 

        cfg = PLANT_CONFIG.get(plant_zd)
        if not cfg:
            print(f"Unexpected plant_zd value: {plant_zd}")
            sys.exit(1)

        request_url = os.getenv(cfg["url_key"]) + "login"
        data = {
            "username": os.getenv(cfg["user_key"]),
            "password": os.getenv(cfg["pass_key"]),
            "type": "rest client"
        }

        response = requests.post(request_url, json=data)
        if response.status_code != 200:
            print(f"Failed to get token: {response.status_code} {response.text}")
            sys.exit(1)
        token = json.loads(response.text)
        print(f"token = {token}")
        headers = {'Authorization' : 'Bearer {}'.format(token['sessionId'])}
        return token['sessionId'], headers

class SecretsYaml:
    def __init__(self, config):
        self.config = config

    @staticmethod
    def load_config(path="secrets.yaml"):
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_token_eds_yaml(self,plant_zd="Maxson"):
        try:
            plant_cfg = self.config['eds_apis'][plant_zd]
        except KeyError:
            raise ValueError(f"Unknown plant_zd '{plant_zd}'")

        request_url = plant_cfg['url'] + 'login'
        data = {
            'username': plant_cfg['username'],
            'password': plant_cfg['password'],
            'type': 'rest client'
        }

        response = requests.post(request_url, json=data)
        response.raise_for_status()

        token = response.json()
        headers = {'Authorization': f"Bearer {token['sessionId']}"}

        return token['sessionId'], headers
    
class Example:
    def test0_env():
        # call from the root directory using poetry run python -m src.env
        
        # Load all keys from .env file
        load_env()

        # List all expected keys for values stored in .env file 
        env_keys = [
            "EDS_API_URL_127",
            "EDS_API_USERNAME_127",
            "EDS_API_PASSWORD_127",
            "EDS_API_URL_128",
            "EDS_API_USERNAME_128",
            "EDS_API_PASSWORD_128",
            "RJN_API_URL",
            "RJN_API_USERNAME",
            "RJN_API_PASSWORD"
            ]

        # Call each expected key with os.getenv(key)
        for key in env_keys:
            print(f"{key} = {os.getenv(key)}")

        plant_zd = "Maxson"
        token, headers = SecretsEnv.get_token_eds_env(plant_zd)
        print(f"token = {token}")
        print(f"headers = {headers}")

    def test1_yaml():
        load_env()
        env = SecretsEnv()
        token, headers = env.get_token_eds_env("Maxson")
        print(f"Token: {token}")
        print(f"Headers: {headers}")
        
        config = SecretsYaml.load_config()
        secrets = SecretsYaml(config)
        token, headers = secrets.get_token_eds_yaml(plant_zd = "Maxson")
        print(f"Token: {token}")
        print(f"Headers: {headers}")
        

if __name__ == "__main__":
    #Example.test0_env()
    Example.test1_yaml()
