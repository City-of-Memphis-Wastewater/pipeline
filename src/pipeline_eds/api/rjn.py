from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import requests
import logging
# from typing import Union # for 3.8 friendly type suggestions

from pipeline_eds.calls import call_ping
from pipeline_eds.env import find_urls
from pipeline_eds.decorators import log_function_call
from pipeline_eds.time_manager import TimeManager

logger = logging.getLogger(__name__)

class RjnClient:
    def __init__(self,config):
        self.config = config
    
    @staticmethod
    def login_to_session(api_url, client_id, password):
        logger.info("RjnClient.login_to_session()")
        session = requests.Session()

        data = {'client_id': client_id, 'password': password, 'type': 'script'}
        
        try:
            response = session.post(f'{api_url}/auth', json=data, verify=True)
            response.raise_for_status() # catch 4xx/5xx html status
            token = response.json().get('token')
            session.headers['Authorization'] = f'Bearer {token}'
            print("Status code:", response.status_code)
            print("Response text:", response.text)
            return session
        except requests.exceptions.SSLError as ssl_err:
            logging.warning("SSL verification failed. Will retry on next scheduled cycle.")
            logging.debug(f"SSL error details: {ssl_err}")
            return None

        except requests.exceptions.ConnectionError as conn_err:
            logging.warning("Connection error during authentication. Will retry next hour.")
            logging.debug(f"Connection error details: {conn_err}")
            return None

        except Exception as general_err:
            logging.error("Unexpected error during login.", exc_info=True)
            return None

    @staticmethod
    #def send_data_to_rjn(session, base_url:str, project_id:str, entity_id:int, timestamps: list[Union[int, float, str]], values: list[float]):
    def send_data_to_rjn(session, base_url, project_id, entity_id, timestamps, values):
        if timestamps is None:
            raise ValueError("timestamps cannot be None")
        if values is None:
            raise ValueError("values cannot be None")
        if not isinstance(timestamps, list):
            raise ValueError("timestamps must be a list. If you have a single timestamp, use: [timestamp] ")
        if not isinstance(values, list):
            raise ValueError("values must be a list. If you have a single value, use: [value] ")
        # Check for matching lengths of timestamps and values
        if len(timestamps) != len(values):
            raise ValueError(f"timestamps and values must have the same length: {len(timestamps)} vs {len(values)}")

        timestamps_str = [TimeManager(ts).as_formatted_date_time() for ts in timestamps]

        url = f"{base_url}/projects/{project_id}/entities/{entity_id}/data"
        params = {
            "interval": 300,    
            "import_mode": "OverwriteExistingData",
            "incoming_time": "DST"#, # DST seemed to fail and offset by an hour into the future. UTC with central time seemed to fail and offset the data 5 hours into the past. 
            #"local_timezone": "CST_CentralStandardTime"
        }
        body = {
        "comments": "Imported from EDS.",
        "data": dict(zip(timestamps_str, values))  # Works for single or multiple entries
        }
        

        response = None
        try:
            response = session.post(url=url, json= body, params = params)

            print("Status code:", response.status_code)
            print("Response text:", response.text)
            if response is None:
                print("Response = None, job cancelled")
            else:
                response.raise_for_status()
                print(f"Sent timestamps and values to entity {entity_id} (HTTP {response.status_code})")
                return True
        except requests.exceptions.ConnectionError as e:
            print("Skipping RjnClient.send_data_to_rjn() due to connection error")
            print(e)
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error sending data to RJN: {e}")
            if response is not None:# and response.status_code != 500:
                logging.debug(f"Response content: {response.text}")  # Print error response
                
            return False
                
    @staticmethod
    def ping():
        from pipeline_eds.env import SecretConfig
        from pipeline_eds.workspace_manager import WorkspaceManager
        workspace_name = WorkspaceManager.identify_default_workspace_name()
        workspace_manager = WorkspaceManager(workspace_name)
        secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
        
        secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
        sessions = {}

        url_set = find_urls(secrets_dict)
        for url in url_set:
            if "rjn" in url.lower():
                print(f"ping url: {url}")
                call_ping(url)

@log_function_call(level=logging.DEBUG)
def demo_rjn_ping():
    from pipeline_eds.calls import call_ping
    from pipeline_eds.env import SecretConfig
    from pipeline_eds.workspace_manager import WorkspaceManager

    from pipeline_eds.env import SecretConfig
    from pipeline_eds.workspace_manager import WorkspaceManager
    workspace_name = WorkspaceManager.identify_default_workspace_name()
    workspace_manager = WorkspaceManager(workspace_name)

    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    
    base_url = secrets_dict.get("contractor_apis", {}).get("RJN", {}).get("url").rstrip("/")
    session = RjnClient.login_to_session(api_url = base_url,
                                    client_id = secrets_dict.get("contractor_apis", {}).get("RJN", {}).get("client_id"),
                                    password = secrets_dict.get("contractor_apis", {}).get("RJN", {}).get("password"))
    if session is None:
        logger.warning("RJN session not established. Skipping RJN-related data transmission.\n")
        return
    else:
        logger.info("RJN session established successfully.")
        session.base_url = base_url
        response = call_ping(session.base_url)

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "default"

    if cmd == "ping":
        demo_rjn_ping()
    else:
        print("Usage options: \n"
        "poetry run python -m pipeline_eds.api.rjn ping")