import requests
import logging
from requests.exceptions import SSLError, ConnectionError
import logging

from src.pipeline.calls import make_request, call_ping
from src.pipeline.env import find_urls
from src.pipeline.decorators import log_function_call
from src.pipeline import helpers

logger = logging.getLogger(__name__)

class RjnClient:
    def __init__(self,config):
        self.config = config
    
    def send_point(self, payload: dict):
        request_url = self.api_url + 'data/point'  # Adjust this if needed
        response = make_request(url=request_url, headers=self.headers, data=payload, method="POST")
        if response.status_code == 200:
            print(f"Successfully posted point {payload.get('rjn_name')}")
        else:
            print(f"Failed to post point {payload.get('rjn_name')}: {response.status_code}")

    @staticmethod
    def login_to_session(api_url, client_id, password):
        logger.info("RjnClient.login_to_session()")
        session = requests.Session()

        data = {'client_id': client_id, 'password': password, 'type': 'script'}
        
        try:
            response = session.post(api_url + 'auth', json=data, verify=True)
            response.raise_for_status() # catch 4xx/5xx html status
            token = response.json().get('token')
            session.headers['Authorization'] = f'Bearer {token}'
            print("Status code:", response.status_code)
            print("Response text:", response.text)
            return session
        except SSLError as ssl_err:
            logging.warning("SSL verification failed. Will retry on next scheduled cycle.")
            logging.debug(f"SSL error details: {ssl_err}")
            return None

        except ConnectionError as conn_err:
            logging.warning("Connection error during authentication. Will retry next hour.")
            logging.debug(f"Connection error details: {conn_err}")
            return None

        except Exception as general_err:
            logging.error("Unexpected error during login.", exc_info=True)
            return None
        
    @staticmethod
    def send_data_to_rjn2(session, base_url:str, project_id:str, entity_id:int, timestamps, values):
        if timestamps is None:
            raise ValueError("timestamps cannot be None")
        if values is None:
            raise ValueError("values cannot be None")
        if not isinstance(timestamps, list):
            timestamps = [timestamps]
        if not isinstance(values, list):
            values = [values]
        # Check for matching lengths of timestamps and values
        if len(timestamps) != len(values):
            raise ValueError(f"timestamps and values must have the same length: {len(timestamps)} vs {len(values)}")


        url = f"{base_url}/projects/{project_id}/entities/{entity_id}/data"
        params = {
            "interval": 300,
            "import_mode": "OverwriteExistingData",
            "incoming_time": "DST"
        }
        body = {
        "comments": "Imported from EDS.",
        "data": dict(zip(timestamps, values))  # Works for single or multiple entries
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
        except ConnectionError as e:
            print("Skipping RjnClient.send_data_to_rjn() due to connection error")
            print(e)
        except requests.exceptions.RequestException as e:
            print(f"Error sending data to RJN: {e}")
            if response is not None:# and response.status_code != 500:
                print(f"Response content: {response.text}")  # Print error response
                
    @staticmethod
    def ping():
        from src.pipeline.env import SecretsYaml
        from src.pipeline.projectmanager import ProjectManager
        project_name = ProjectManager.identify_default_project()
        project_manager = ProjectManager(project_name)
        secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
        
        secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
        sessions = {}

        url_set = find_urls(secrets_dict)
        for url in url_set:
            if "rjn" in url.lower():
                print(f"ping url: {url}")
                call_ping(url)

@log_function_call(level=logging.DEBUG)
def demo_eds_ping():
    from src.pipeline.calls import call_ping
    from src.pipeline.env import SecretsYaml
    from src.pipeline.projectmanager import ProjectManager



    from src.pipeline.env import SecretsYaml
    from src.pipeline.projectmanager import ProjectManager
    project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)

    secrets_dict = SecretsYaml.load_config(secrets_file_path = project_manager.get_configs_secrets_file_path())
    
    api_secrets_r = helpers.get_nested_config(secrets_dict, ["contractor_apis","RJN"])
    session = RjnClient.login_to_session(api_url = api_secrets_r["url"],
                                                username = api_secrets_r["client_id"],
                                                password = api_secrets_r["password"])
    session.custom_dict = api_secrets_r
    
    
    api_url = session.custom_dict["url"]
    response = call_ping(api_url)

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "default"

    if cmd == "ping":
        RjnClient.ping()
    else:
        print("Usage options: \n"
        "poetry run python -m pipeline.api.rjn ping")