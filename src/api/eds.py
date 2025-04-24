
import requests
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
    