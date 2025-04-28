from datetime import timedelta 
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

        response = make_request(request_url, data)
        token = response.json().get("token")

        ['sessionId']
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"  
        }
        return token, headers
    
    def send_point(self, payload: dict):
        request_url = self.api_url + 'data/point'  # Adjust this if needed
        response = make_request(url=request_url, headers=self.headers, data=payload)
        if response.status_code == 200:
            print(f"Successfully posted point {payload.get('rjn_name')}")
        else:
            print(f"Failed to post point {payload.get('rjn_name')}: {response.status_code}")

def send_data_to_rjn(base_url, project_id, entity_id, headers, timestamp, value):

    spoof_timestamp = timestamp - timedelta(minutes=5)
    timestamp_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S')
    spoof_timestamp_str = spoof_timestamp.strftime('%Y-%m-%dT%H:%M:%S')

    url = f"{base_url}/projects/{project_id}/entities/{entity_id}/data"
    params = {
        "interval": 300,
        "import_mode": "OverwriteExistingData",
        "incoming_time": "DST"
    }
    body = {
        "comments": "Imported from EDS.",
        "data": {
            spoof_timestamp_str : value,
            timestamp_str: value
        }
    }
    # Always add Accept header
    full_headers = {**headers, "Accept": "application/json"}
    try:
        response = make_request(url=url, headers=full_headers, params = params, method="POST", data=body)
        #response = requests.post(url, headers=headers, params=params, json=body)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to RJN: {e}")
        if response.status_code != 500:
            print(f"Response content: {response.text}")  # Print error response
    print(f"Sent {timestamp} -> {value} to {entity_id} (HTTP {response.status_code})")