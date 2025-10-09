# pipeline/api/mission.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
from datetime import datetime, timedelta
import requests
import time
from urllib.parse import quote_plus
import json


    
class MissionClient:
    def __init__(self, token: str):
        self.base_url = "https://123scada.com/Mc.Services/api"
        self.report_base = "https://123scada.com/Mc.Reports/api"
        self.customer_id = None # Optional, set after login if needed
        self.headers = {"Authorization": f"Bearer {token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    #@staticmethod
    def login_via_signalr(self,api_url: str, customer_id: int, timeout: int = 10) -> "MissionClient":
        """
        Logs in by negotiating a SignalR connection and returns a MissionClient
        with the bearer token.
        """
        session = requests.Session()
        session.verify = False  # for self-signed certs

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
    def login(api_url: str, username: str, password: str, timeout=10) -> "MissionClient":
        """
        Login using OAuth2 password grant, returns a MissionClient with valid token.
        """
        session = requests.Session()
        session.verify = False  # Ignore self-signed certs; optional

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

        response = session.post(url, data=data, headers=headers, timeout=timeout)
        
        print("response = session.post(url, data=data, headers=headers, timeout=timeout)")
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise ValueError("No access_token returned from /token endpoint.")

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
        client.session = session  # preserve session for further requests
        client.session.headers.update({"Authorization": f"Bearer {bearer_token}"})
        return client

    
    def get_analog_table(self, device_id: int, start_ms: int, end_ms: int, start_row: int = 1, page_size: int = 50):
        url = f"{self.base_url}/Analog/Table"
        params = {
            "customerId": self.customer_id,
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

    def download_analog_csv(self, device_id: int, device_name: str, start_date: str, end_date: str, file_name: str = None):
        """Download CSV report for the device"""
        if file_name is None:
            file_name = f"Analog_{device_name.replace(' ', '')}_DataPoints_{start_date}.csv"
        url = f"{self.report_base}/Download/AnalogDownload"
        params = {
            "customerId": self.customer_id,
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
    


def demo_retrieve_analog_data_and_save_csv():
    from pipeline.env import SecretConfig
    from pipeline.workspace_manager import WorkspaceManager
    workspace_name = WorkspaceManager.identify_default_workspace_name()
    workspace_manager = WorkspaceManager(workspace_name)

    secrets_dict = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    api_url = secrets_dict.get("contractor_apis", {}).get("Mission", {}).get("url").rstrip("/")
    username = secrets_dict.get("contractor_apis", {}).get("Mission", {}).get("username")
    password = secrets_dict.get("contractor_apis", {}).get("Mission", {}).get("password")

    """"""
    client = MissionClient.login(api_url,username,password)

    # Example request:
    resp = client.session.get(f"{client.base_url}/account/GetSettings/?viewMode=1")
    MissionClient.customer_id = resp.json()['user']['customerId']
    print(MissionClient.customer_id)
    
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
    with open("Gayoso_Analog.csv", "wb") as f:
        f.write(csv_bytes)

if __name__ == "__main__":
    demo_retrieve_analog_data_and_save_csv()