import requests
from src.calls import make_request
class RjnClient:
    def __init__(self,config):
        self.config = config

    def get_token(self):
        
        request_url = self.config['url'] + 'auth'
        data = {
            'client_id': self.config['client_id'],
            'password': self.config['password']
        }

        #response = requests.post(request_url, json=data)
        #response.raise_for_status()

        #response = make_request(request_url, data)
        #token = response.json()

        response = make_request(request_url, data)
        token = response.json().get("token")

        print(f"token = {token}")
        ['sessionId']
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"  
        }
        return token, headers