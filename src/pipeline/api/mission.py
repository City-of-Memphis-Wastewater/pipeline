# pipeline/api/mission.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
from datetime import datetime, timedelta
import requests
import time
from urllib.parse import quote_plus
import json
import typer
from requests.exceptions import Timeout

from pipeline.security_and_config import get_external_api_credentials
from pipeline_tests.variable_clarity import Redundancy

class MissionLoginException(Exception):
    """
    Custom exception raised when a login to the Mission 'API' fails.

    This exception is used to differentiate between a simple network timeout
    and a specific authentication or API-related login failure.
    """

    def __init__(self, message: str = "Login failed for the Mission 'API'. Check hashed credentials."):
        """
        Initializes the MissionLoginException with a custom message.

        Args:
            message: A descriptive message for the error.
        """
        self.message = message
        super().__init__(self.message)

class MissionClient:
    """
    MissionClient handles login and data retrieval from the 123scada API.
    📝 Note: Handling Hashed Passwords
    
    - The system uses a hashed version of the password for authentication.
    - If the password ever changes, you’ll need to update the stored credentials with whatever authentication values the service requires for non-interactive access.
    - Do not attempt to reverse the hash — it’s a one-way cryptographic function and cannot be decrypted to retrieve the original password.
    - Always store and transmit authentication credentials and tokens securely, and avoid exposing them in public repositories or logs.
    - If the system’s hashing method changes (e.g., due to a security update), make sure to adjust the authentication logic accordingly.
    - If you need to run this automation non-interactively, obtain a supported programmatic credential (API key, OAuth client credentials, service account, or refresh token) from the service owner and store it in a secure secrets manager. Do not rely on copying browser network values for production automation; contact the service administrator for a documented solution.
    - Ensure that the password provided is in the correct format expected by the authentication endpoint. Some systems may require pre-hashed passwords, while others hash them internally. Confirm with the administrator whether the password should be used as-is or transformed before submission.
    - If password-based login fails, consider requesting an API key, service account, or OAuth client credentials for automation. These are more stable and secure for non-interactive use.
    - Enable logging of HTTP responses during development to inspect error messages and status codes. This can help pinpoint authentication issues.
    """

    def __init__(self, token: str):
        self.true_base_url = "https://123scada.com/"
        self.services_api_url = "https://123scada.com/Mc.Services/api"
        self.report_api_url = "https://123scada.com/Mc.Reports/api"
        self.customer_id = None # Optional, set after login if needed
        self.headers = {"Authorization": f"Bearer {token}"}
        self.session = requests.Session() # session caputure, such that client.session is available
        self.session.headers.update(self.headers)

    #@instancemethod
    def set_services_api_url(self,base_url:str|None=None)-> None: # ASK FOR CLARITY ABOUT RETURN IF THERE IS NO RETURN INTENDED ON TERMINATING FUNCTION
        if base_url is None:
            self.services_api_url = "https://123scada.com/Mc.Services/api"
            return 
        
    @classmethod
    def login_via_signalr(services_api_url: str, customer_id: int, timeout: int = 10) -> "MissionClient":
        """
        Logs in by negotiating a SignalR connection and returns a MissionClient
        with the bearer token.
        """
        session = requests.Session()
        session.verify = True  # for self-signed certs

        connection_data = [
            {"name": "chathub"},
            {"name": "eventhub"},
            {"name": "heartbeathub"},
            {"name": "infohub"},
            {"name": "overviewhub"},
            {"name": "statushub"}
        ]

        params = {
            "clientProtocol": "2.1",
            "customerId": customer_id,
            "timezone": "C",
            "connectionData": json.dumps(connection_data)
        }

        response = session.get(f"{api_url}/signalr/negotiate", params=params, timeout=timeout)
        response.raise_for_status()
        json_resp = response.json()

        token = json_resp.get("accessToken") or json_resp.get("sessionId")
        if not token:
            raise ValueError("No token returned from SignalR negotiate endpoint.")

        client = MissionClient(token=token, customer_id=customer_id)
        client.session = session
        client.session.headers.update({"Authorization": f"Bearer {token}"})
        return client

    @staticmethod
    def login_to_session_with_api_credentials(api_credentials):
        """
        Like login_to_sessesion, plug with custom session attributes added to the session object.
        """
        # Expected to be used in terminal, so typer is acceptable, but should be scaled.
        session = None
        try:
            client = MissionClient.login_to_session(
                api_url=api_credentials.get("url"),# + "/api",
                username=api_credentials.get("username"),
                password=api_credentials.get("password"),
                timeout=10 # Add a 10-second timeout to the request
            )
            
            # --- Add custom session attributes to the session object ---
            ##client.session.base_url = api_credentials.get("url")
        except Timeout:
            typer.echo(
                typer.style(
                    "\nConnection to the EDS API timed out. Please check your VPN connection and try again.",
                    fg=typer.colors.RED,
                    bold=True,
                )
            )
            raise typer.Exit(code=1)
        except MissionLoginException as e:
            typer.echo(
                typer.style(
                    f"\nLogin failed for EDS API: {e}",
                    fg=typer.colors.RED,
                    bold=True,
                )
            )
            raise typer.Exit(code=1)
        
        return client
    
    @staticmethod
    def login_to_session(services_api_url: str, username: str, password: str, timeout=10) -> "MissionClient":
        """
        Login using OAuth2 password grant, returns a MissionClient with valid token.
        """
        session = requests.Session()
        session.verify = True  # Ignore self-signed certs; optional

        # Add required cookie
        session.cookies.set("userBaseLayer", "fc", domain="123scada.com")

        timestamp = int(time.time() * 1000)
        url = f"{api_url}/token?timestamp={timestamp}"

        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": "123SCADA",
            "authenticatorCode": ""
        }

        # Headers
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://123scada.com",
            "Referer": "https://123scada.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            response = session.post(url, data=data, headers=headers, timeout=timeout)
            response.raise_for_status()
            token = response.json().get("access_token")
            if not token:
                raise ValueError("No access_token returned from /token endpoint.")
                
        except Timeout:
            typer.echo(
                typer.style(
                    "\nConnection to the EDS API timed out. Please check your VPN connection and try again.",
                    fg=typer.colors.RED,
                    bold=True,
                )
            )
            raise typer.Exit(code=1)
        except MissionLoginException as e:
            typer.echo(
                typer.style(
                    f"\nLogin failed for EDS API: {e}",
                    fg=typer.colors.RED,
                    bold=True,
                )
            )
            raise typer.Exit(code=1)


        #client=MissionClient(token=token)
        #client.session = session # is this inferred ?
        #resp = client.session.get(f"{client.services_api_url}/account/GetSettings/?viewMode=1")
        #client.customer_id = resp.json()['user']['customerId']

        return MissionClient(token=token)

    @staticmethod
    def login_defunct(api_url: str, username: str, password: str, timeout: int = 10) -> "MissionClient":
        """
        Logs in to the 123scada API and returns a MissionClient instance
        with a session containing the bearer token.
        """
        session = requests.Session()
        session.verify = False  # disable SSL verification if necessary

        payload = {
            "username": username,
            "password": password,
            "type": "script"  # matches your network trace
        }

        # POST to the token endpoint (or /login)
        response = session.post(f"{api_url}/login", json=payload, timeout=timeout)
        response.raise_for_status()
        json_response = response.json()

        # Extract the bearer/session token
        bearer_token = json_response.get("sessionId")
        if not bearer_token:
            raise ValueError("Login failed: sessionId not returned.")

        # Create a MissionClient using this token
        client = MissionClient(token=bearer_token, customer_id=json_response.get("customerId", 0))
        return client

    @instancemethod
    def logout(self):
        """
        client.logout()
        """
        pass

    @classmethod
    def get_customer_id_from_fresh_login(services_api_url:str,
                                         username:str,
                                         password:str
                                         )->int:  
        """
        By providing the full api url, the username and the and password.
        The client object is temporary and disposed of internally. 
        Please maintain this function, even if it is not used. 
        It serves as the simplest tip-to-tail example of a log in to the client, with a variable retrieved.
        """  
        # Assumes that you have already logged in to a client with your api_url,username,password
        #client = MissionClient.login_to_session(services_api_url,username,password)
        client = MissionClient.login_to_session(services_api_url,username,password)
        # Example request:  
        resp = client.session.get(f"{client.services_api_url}/account/GetSettings/?viewMode=1")
        customer_id = resp.json().get('user',{}).get('customerId',{})
        # Add log out, like 
        client.logout()
        return customer_id # only give back the raw value, allowing the use to assign the atttribue as they wish
    
    #@instancemethod
    def get_customer_id_from_known_client(self:"MissionClient")->int:    
        """ 
        self is client object of type "MissionClient"
        """
        # Assumes that you have already logged in to a client with your api_url,username,password
        """
        # Infers log in has already happened, like this:
        client = MissionClient.login_to_session(services_api_url,username,password)
        
        # And then this function is called like this:
        client_id = client.get_customer_id_from_client_account_settings()
        """
        #client = MissionClient.login_to_session(services_api_url,username,password)

        # Example request:  
        resp = self.session.get(f"{self.services_api_url}/account/GetSettings/?viewMode=1")
        customer_id = resp.json().get('user',{}).get('customerId',{})
        self.customer_id = customer_id # for rigor, assign the attribute to the client - this varibale will now be known to the class instance, wthout returning the client object, and without handling any output
        return customer_id # only give back the raw value, allowing the use to assign the atttribue as they wish

    #@instancemethod
    def get_analog_table(self:"MissionClient", device_id: int = None, customer_id: int | None = None, start_ms: int = None, end_ms: int = None, start_row: int = 1, page_size: int = 50)->dict:
        url = f"{self.services_api_url}/Analog/Table"
        
        if customer_id is None and self.customer_id is not None:
            customer_id = self.customer_id
        elif self.customer_id is None:
            customer_id = MissionClient.get_customer_id_from_client_account_settings(self) # inferred assignment
            self.customer_id = MissionClient.get_customer_id_from_client_account_settings(self) # explicit assignment

        params = {
            "customerId": customer_id,
            "deviceId": device_id,
            "StartRow": start_row,
            "PageSize": page_size,
            "StartDate": start_ms,
            "EndDate": end_ms,
            "fromDate": "undefined",
            "timestamp": int(time.time() * 1000),
        }
        r = requests.get(url, headers=self.headers, params=params)
        r.raise_for_status()
        return r.json()

    def download_analog_csv(self, device_id: int=None, customer_id: int | None = None, device_name: str = None, start_date: str = None, end_date: str = None, file_name: str = None)->str:
        """Download CSV report for the device"""
        url = f"{self.report_api_url}/Download/AnalogDownload"

        if file_name is None:
            file_name = f"Analog_{device_name.replace(' ', '')}_DataPoints_{start_date}.csv"
        
        if customer_id is None:
            customer_id = self.customer_id
        params = {
            "customerId": customer_id,
            "deviceId": device_id,
            "deviceName": quote_plus(device_name),
            "startDate": start_date,
            "endDate": end_date,
            "fileName": file_name,
            "format": 1,
            "genII": False,
            "langId": "en",
            "resolution": 0,
            "type": 0,
            "timestamp": int(time.time() * 1000),
            "emailAddress": "",
        }
        r = requests.get(url, headers=self.headers, params=params)
        r.raise_for_status()
        return r.content  # CSV bytes



def demo_retrieve_analog_data_and_save_csv(services_api_url:str=None)->dict:
    #from pipeline.env import SecretConfig
    #from pipeline.workspace_manager import WorkspaceManager
    typer.echo("Running: pipeline.api.mission.demo_retrieve_analog_data_and_save_csv()...")
    typer.echo("Running: Calling 123scada.com using the Mission Client ...")
    #mission_api_creds = get_external_api_credentials("TestMission")
    party_name = "Mission"
    mission_api_creds = get_external_api_credentials(party_name = party_name)
    #mission_api_creds["username"] = mission_api_creds["client_id"] # rectify the way this is stored for RJN
    
    #workspace_name = WorkspaceManager.identify_default_workspace_name()
    #workspace_manager = WorkspaceManager(workspace_name)
    
    service_name = f"pipeline-external-api-{party_name}"
    api_url_full = _get_config_with_prompt(config_key = service_name, prompt_message = f"Enter {party_name} API URL (e.g., http://api.example.com)", overwrite=overwrite)
    username = _get_credential_with_prompt( service_name = service_name, item_name = "username", prompt_message = f"Enter the username AKA client_id for the {party_name} API",hide=False, overwrite=overwrite)
    #client_id = _get_credential_with_prompt(service_name = service_name, item_name = "client_id", prompt_message = f"Enter the client_id for the {party_name} API",hide=False, overwrite=overwrite)
    password = _get_credential_with_prompt(service_name = service_name, item_name = "password", prompt_message = f"Enter the password for the {party_name} API", overwrite=overwrite)
    
    
    client = MissionClient.login_to_session_with_api_credentials(mission_api_creds)

    #secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    #api_url = secrets_dict.get("contractor_apis", {}).get("Mission", {}).get("url").rstrip("/")
    #username = secrets_dict.get("contractor_apis", {}).get("Mission", {}).get("username")
    #password = secrets_dict.get("contractor_apis", {}).get("Mission", {}).get("password")
    client = MissionClient.login_to_session(services_api_url,username,password)

    '''
    Logic check
    provided as a function input for clarity # opportunity for static class variable
    
    '''
    from pipeline_tests.variable_clarity import Redundancy
    Redundancy.compare(client.services_api_url == services_api_url) # already known 
    
    # Example request:  
    resp = client.session.get(f"{services_api_url}/account/GetSettings/?viewMode=1")
    client.customer_id = resp.json().get('user',{}).get('customerId',{})

    # Get the last 24 hours of analog table data
    end = datetime.now()
    start = end - timedelta(days=1)
    to_ms = lambda dt: int(dt.timestamp() * 1000)

    table_data = client.get_analog_table(device_id=22158, start_ms=to_ms(start), end_ms=to_ms(end))
    print(f"table_data = {table_data}")


    print(f"Fetched {len(table_data.get('analogMeasurements', []))} rows from analog table.")
    #print(f"Fetched {len(table_data.get('rows', []))} rows from analog table.")

    # Or download CSV for 6–11 Oct 2025
    csv_bytes = client.download_analog_csv(
        device_id=22158,
        device_name="Gayoso Pump Station",
        start_date="20251006",
        end_date="20251011"
    )
    typer.echo("\nRunning: Generating sample file... ")
    with open("Gayoso_Analog.csv", "wb") as f:
        f.write(csv_bytes)
    typer.echo("\nJob Complete.")
    typer.echo("\nAdvice: Do no git add Gayoso_Analog.csv.")
    return dict
if __name__ == "__main__":
    demo_retrieve_analog_data_and_save_csv()
