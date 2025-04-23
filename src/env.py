#env.__main__.py
#import src.helpers.load_json # good idea, to load from json file at startup, but juice isnt worth the squeeze right now
from src.address import Address 
import os, sys
import requests
import json

from dotenv import load_dotenv
def load_env():
    load_dotenv(dotenv_path=".env")

class Env:
    token = str()
    header = str()
    username = str()
    password = str()
    
    def __init__(self):
        self.nope = "Nope"
        self.instance = None

    @classmethod
    def get_username(cls):
        return cls.username
    
    @classmethod
    def get_password(cls):
        return cls.password
    
    @classmethod
    def set_header(cls,header):
        cls.header = header

    @classmethod
    def get_header(cls):
        return cls.header
    
    def set_token(cls,token):
        cls.token = token

    def get_token(cls):
        return cls.token
    

    def get_token_eds(plant_zd="Maxson"):
        # Show a record of the EDS env keys, for posterity, and hardcode the selection with an plant_integer 
        if plant_zd == "Maxson":
            plant_integer = 0
        elif plant_zd == "Stiles":
            plant_integer = 1
        else:
            print("The plant_zd vlaue is not anticipated.")
            sys.exit()
        
        key_url = ["EDS_API_URL_127","EDS_API_URL_128"][plant_integer]
        key_username = ["EDS_API_USERNAME_127","EDS_API_USERNAME_128"][plant_integer]
        key_password = ["EDS_API_PASSWORD_127","EDS_API_PASSWORD_128"][plant_integer]

        request_url = os.getenv(key_url) + 'login'
        data = {'username' : os.getenv(key_username), 'password' : os.getenv(key_password), 'type' : 'rest client'}
        response = requests.post(request_url, json = data)
        print(f"response={response}")
        token = json.loads(response.text)
        print(f"token = {token}")
        headers = {'Authorization' : 'Bearer {}'.format(token['sessionId'])}
        return headers
    
if __name__ == "__main__":
    # call from the root directory using poetry run python -m src.env
    
    # lead all keys from .env file
    load_env()

    # list all expected keys for values stored in .env file 
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

    # call each key with os.getenv(key)
    for key in env_keys:
        print(f"{key} = {os.getenv(key)}")

    Env.get_token_eds(plant_zd = "Maxson")