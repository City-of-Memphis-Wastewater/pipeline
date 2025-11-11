# pipeline/api/mission.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
from datetime import datetime, timedelta
import requests
import time
from urllib.parse import quote_plus
import json
import typer
from requests.exceptions import Timeout
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table

from pipeline.security_and_config import SecurityAndConfig
#from pipeline.variable_clarity_grok import Redundancy
from pipeline.variable_clarity import Redundancy, instancemethod
from pipeline.time_manager import TimeManager

# Get the Rich console instance
console = Console()

"""
```
### What is SignalR?

SignalR (specifically ASP.NET SignalR, though the concept is general) is a framework that simplifies adding **real-time web functionality** to applications.

1. **Real-Time:** It allows server code to push content to connected clients (like a web browser or your Python application) instantly as it happens, rather than the client having to constantly poll the server for new data.
    
2. **Persistent Connection:** It automatically manages persistent connections between the server and client, using WebSockets where available, and gracefully falling back to older techniques (like long polling) if necessary.
    
3. **Bi-directional:** It enables two-way communication, meaning the client can call methods on the server, and the server can call methods on the client.
    

### When is the Right Time to Use SignalR?

You use SignalR whenever you need **low-latency, asynchronous updates** from the server without the client repeatedly asking for them.

|**Scenario**|**When to Use SignalR**|**When to Use Standard REST (like /Analog/Table)**|
|---|---|---|
|**Data Nature**|Real-time, streaming, or rapidly changing data.|Historical, batch, or configuration data.|
|**Examples**|Live dashboards, instant alerts, chat applications, gaming, monitoring real-time SCADA events.|Retrieving a CSV report, fetching a page of historical measurements, updating account settings.|
|**Client Behavior**|The client passively listens for server pushes.|The client actively requests (pulls) data when needed.|

**In the context of your `MissionClient`:**

- **`login_via_signalr`** is intended to establish the connection necessary to listen to **live updates** (e.g., a pump turned on, a pressure sensor spike, a heart-beat signal) which arrive via a WebSocket channel.
    
- **`login_to_session`** is intended to get the Bearer Token needed to access the **historical REST endpoints** (like `/Analog/Table` and `/Download/AnalogDownload`) that fetch stored data.
```
"""
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

class MissionTransformation:


    @staticmethod
    def display_table_with_rich(data_list: List[Dict[str, Any]]):
        """
        Creates and prints a formatted table from a list of dictionaries using Rich.
        """
        if not data_list:
            console.print("[bold yellow]Warning:[/bold yellow] No data to display.")
            return

        # 1. Initialize the Rich Table
        table = Table(title="Analog Data Measurements", show_header=True, header_style="bold magenta")
        
        # Get the keys (column headers) from the first row
        field_names = list(data_list[0].keys())

        # 2. Define Columns and Formatting
        for name in field_names:
            # Set alignment: Date/Time left-aligned, everything else right-aligned
            align = "left" if name == "Date/Time" else "right"
            
            # Add a column. You can specify style, minimum width, and alignment.
            table.add_column(name, style="cyan", justify=align)

        # 3. Add Rows
        for row_dict in data_list:
            row_values = []
            for name in field_names:
                value = row_dict.get(name)
                
                # Format numbers for better readability (no need for a float_format setting)
                if isinstance(value, (int, float)):
                    # Format to 2 decimal places and convert back to string for Rich
                    # Add a comma separator for large numbers, e.g., 11,432.00
                    formatted_value = f"{value:,.2f}"
                elif value is None:
                    formatted_value = "[dim]N/A[/dim]"
                else:
                    formatted_value = str(value)

                row_values.append(formatted_value)
                
            # Add the list of formatted string values as a row
            table.add_row(*row_values)

        # 4. Print the final table
        console.print(table)


    # --- Example Usage (assuming analog_table is available) ---
    # display_table_with_rich(analog_table)


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
    services_root_url = "https://123scada.com/Mc.Services"
    services_api_url = "https://123scada.com/Mc.Services/api"
    report_api_url = "https://123scada.com/Mc.Reports/api"

    def __init__(self, token: str):
        
        self._assignment_hints = {}  # for use with Redundancy class
        self.customer_id = None # Optional, set after login if needed
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, "session"):
            self.session.close()
        
    @classmethod
    def get_account_settings_url(cls):
        return f"{cls.services_api_url}/account/GetSettings/?viewMode=1"
    
    @classmethod
    def get_signalr_negotiate_url(cls):
        return f"{cls.services_root_url}/signalr/negotiate"
        
        
    @classmethod
    def login_via_signalr(cls, customer_id: int, timeout: int = 10) -> "MissionClient":
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

        response = session.get(cls.get_signalr_negotiate_url(), params=params, timeout=timeout)
        
        response.raise_for_status()
        json_resp = response.json()
        print(f"json_resp = {json_resp}")
        #token = json_resp.get("accessToken") or json_resp.get("sessionId")
        token = json_resp.get("ConnectionToken")
        if not token:
            raise ValueError("No token returned from SignalR negotiate endpoint.")

        client = MissionClient(token=token)
        client.session = session

        # WARNING: This sets the Authorization header with the SignalR token, 
        # which will cause 401 on REST calls. This is corrected in the demo function below.
        client.session.headers.update({"Authorization": f"Bearer {token}"})
        return client
    
    @staticmethod
    def login_to_session(username: str, password: str, timeout=10) -> "MissionClient":
        """
        Login using OAuth2 password grant, returns a MissionClient with valid token.
        """
        session = requests.Session()
        session.verify = True  # Ignore self-signed certs; optional

        # Add required cookie
        session.cookies.set("userBaseLayer", "fc", domain="123scada.com")

        timestamp = int(time.time() * 1000)
        url = f"{MissionClient.services_root_url}/token?timestamp={timestamp}"
        #url = f"https://123scada.com/Mc.Services/token?timestamp={timestamp}"
        
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


        client=MissionClient(token=token)
        if not hasattr(client,"session"):
            client.session = session # make it  a non-temporary session. # this breaks everything if already handled in intitializion
        client.session.headers.update({"Authorization": f"Bearer {token}"})

        return client

    @instancemethod
    def logout(self):
        """
        client.logout()
        """
        self.__exit__()

    @classmethod 
    @Redundancy.set_on_return_hint(recipient=None,attribute_name="customer_id")
    def get_customer_id_from_fresh_login(cls,
                                         username:str,
                                         password:str
                                         )->int:  
        """
        By providing the full api url, the username and the and password.
        The client object is temporary and disposed of internally. 
        Please maintain this function, even if it is not used. 
        It serves as the simplest tip-to-tail example of a log in to the client, with a variable retrieved.
        """  
        with cls.login_to_session(username,password) as client:  
            customer_id = client.get_customer_id_from_known_client()
        return customer_id # only give back the raw value, allowing the use to assign the atttribue as they wish, with functionoal programming
    
    @instancemethod
    @Redundancy.set_on_return_hint(recipient="self",attribute_name = "customer_id")
    def get_customer_id_from_known_client(self:"MissionClient")->int:    
        """ 
        Assumes that you have already logged in with your api_url,username,password
        
        # Infers log in has already happened, like this:
        client = MissionClient.login_to_session(username,password)
        
        # And then this function is called like this:
        client_id = client.get_customer_id_from_known_client()
        """
        # Example request:  
        #resp = self.session.get(f"{MissionClient.services_api_url}/account/GetSettings/?viewMode=1")
        resp = self.session.get(MissionClient.get_account_settings_url())
        #print(f"resp = {resp}")
        customer_id = resp.json().get('user',{}).get('customerId',{})
        if not isinstance(customer_id, int):
            raise ValueError(f"Expected integer customerId, got: {customer_id}")

        # Instead of here, the 'dpuble tap' is now handled by the decorator.
        #self.customer_id = customer_id # for rigor, assign the attribute to the client - this varibale will now be known to the class instance, wthout returning the client object, and without handling any output
        
        return customer_id # only give back the raw value, allowing the use to assign the atttribue as they wish

    
    @staticmethod
    def get_analog_download_url():
        url = f"{MissionClient.report_api_url}/Download/AnalogDownload"
        return url
    
    @instancemethod
    def get_analog_csv_bytes(self, device_id: int=None, 
                            customer_id: int | None = None, 
                            device_name: str = None, 
                            start_date: str = None, 
                            end_date: str = None, 
                            resolution: int = 1)->bytes:
        """
        Generate report for the device.
        
        Calling this function does not actually download a file, like it would in browser. Only the response.content is returned and then is handled.

        Retrieves the raw CSV file bytes for the device report from the server.
        
        This function is preferred over get_analog_table() due to supporting 
        custom 'resolution' values and handling large data sets without pagination.
        
        Note: This method ONLY fetches the raw content (bytes); it does not 
        save the file to the local disk. The caller must handle the file I/O.
        
        Args:
            device_id (int, optional): The ID of the device to fetch data for. Defaults to None.
            customer_id (int | None, optional): The customer ID associated with the device. 
                Defaults to None, in which case the client's cached customer_id is used.
            device_name (str, optional): The name of the device (used for URL encoding and default file name). 
                Defaults to None.
            start_date (str, optional): The start date of the data range (format: YYYYMMDD). Defaults to None.
            end_date (str, optional): The end date of the data range (format: YYYYMMDD). 
                If 'start_date' and 'end_date' are the same, the API provides a 
                24-hour range for that day (00:00 to 23:58). Defaults to None.
            resolution (int, optional): The sampling interval for the data. This is the primary reason 
                to use this endpoint over /Analog/Table. 
                Possible values include: {0, "All Points"}, {1, "5 min Samples"}, {22, "15 min Samples"}, {3, "30 min Samples"}. 
                Defaults to 1 (5-minute samples).

        Defunct Args:
            file_name (str, optional): A suggested filename passed to the server to populate the 
                Content-Disposition header. It does NOT control the local save path. Defaults to a generated name.
        
        Returns:
            bytes: The raw CSV content. The calling function must write this to disk.
        """
        
        url = MissionClient.get_analog_download_url()

        # Placeholder filename - useless
        file_name = f"Analog_{device_name.replace(' ', '')}_DataPoints_{start_date}_MissionClient.csv"
        # not used in this context of the Client, even when provided
        
        if customer_id is None:
            customer_id = self.customer_id
        params = {
            "customerId": customer_id,
            "deviceId": device_id,
            "deviceName": quote_plus(device_name),
            "startDate": start_date,
            "endDate": end_date,
            "fileName": file_name, # Server uses this for Content-Disposition header, but is expected to make no difference in this programmatic context (tested with curl, python, compred to Developer Tools Netwrok observations)
            "format": 1,
            "genII": False,
            "langId": "en",
            "resolution": resolution, # {0, "All Points"}, {1, "5 min Samples"}, {22, "15 min Samples"}, {3, "30 min Samples"},  
            "type": 0,
            "timestamp": int(time.time() * 1000),
            "emailAddress": "",
        }
        ###r = requests.get(url, headers=self.headers, params=params)
        r = self.session.get(url, params=params)
        r.raise_for_status()
        return r.content  # CSV bytes

    @staticmethod
    def login_and_retrieve_analog_csv_bytes(device_name:str=None, device_id:int = None, start_date: int=None, end_date: int=None)->bytes:
        """
        The download function only accepts days as an input.
        If Start Date and End Date value are identical, 
        a 24-hour timeframe worth of data will be downloaded, 
        for 00:00 to 23:58, every two minutes, 
        for the date listed.

        This function is not necessary to be a part of our API flow unless we want CSV backups, but it is smoother to use client.get_analog_table() rather than client.get_analog_csv_bytes().
        """
        typer.echo("Running: pipeline.api.mission.login_and_retrieve_analog_csv_bytes()...")
        typer.echo("Running: Calling 123scada.com using the Mission Client ...")

        party_name = "Mission"
        service_name = f"pipeline-external-api-{party_name}"
        overwrite=False
        
        username = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "username", prompt_message = f"Enter the username for the {party_name} API",hide=False, overwrite=overwrite)
        password = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "password", prompt_message = f"Enter the password for the {party_name} API", overwrite=overwrite)

        if start_date is None:
            # Get the last 24 hours of analog table data
            end = TimeManager(TimeManager.now_rounded_to_hour()).as_datetime() # some time today
            start = end - timedelta(days=1) # some time yesterday
            start_date = TimeManager(start).as_yyyymmdd() # some time yesterday rounded down to 00:00
            #end_date = start_date # when the date is the same, 24 hours worth of data is provided
        if end_date is None:
            end_date = start_date # when the date is the same, 24 hours worth of data is provided

        if start_date > end_date:
            typer.echo("Warning: start_date > end_date")

        with MissionClient.login_to_session(username, password) as client: # works
            client.customer_id = client.get_customer_id_from_known_client()
            print(f"client.customer_id = {client.customer_id}")
        

            # Or download CSV for 6–11 Oct 2025
            csv_bytes = client.get_analog_csv_bytes(
                device_id=device_id,
                device_name=device_name,
                start_date=start_date, # start at 00:00 for date provided in format YYYYMMDD
                end_date=start_date # end at 23:58 for date provided in format YYYYMMDD
            )

            typer.echo("\nCSV bytes retrieved.")

        return csv_bytes, start_date

    @staticmethod
    def save_csv_from_csv_bytes(path:str|Path=None, csv_bytes:bytes=None):
        typer.echo("\nRunning: Generating sample file... ")
        with open(path, "wb") as f:
            f.write(csv_bytes)

        typer.echo(f"\nFile generated: {str(path)}")
    
    @staticmethod
    def csv_bytes_to_table_(csv_bytes:bytes=None):
        """
        Args:
            csv_bytes: Raw CSV data as bytes (e.g., from HTTP response.content)

        Returns:
            A list of dictionaries, one per row, with column headers as keys.
        """
        import io
        import csv
        text_stream = io.StringIO(csv_bytes.decode('utf-8-sig'))  # handle UTF-8 with BOM
        reader = csv.DictReader(text_stream)

        table = [row for row in reader]
        return table
    
    @staticmethod
    def csv_bytes_to_table(csv_bytes:bytes=None):
        """
        Parses raw CSV bytes (which include a 4-line metadata header) 
        into a clean list of dictionaries.

        Args:
            csv_bytes: Raw CSV data as bytes (e.g., from HTTP response.content)

        Returns:
            A list of dictionaries, one per row, with column headers as keys.
        """
        import io
        import csv
        
        if not csv_bytes:
            return []

        # Decode the bytes and create an in-memory text stream
        text_stream = io.StringIO(csv_bytes.decode('utf-8-sig')) # handle UTF-8 with BOM

        # The CSV file has 4 lines of metadata before the actual headers.
        # We must skip them so DictReader finds the correct header row.
        try:
            for _ in range(4):
                next(text_stream)
        except StopIteration:
            # This handles the case where the file is empty or has fewer than 4 lines
            console.print("[bold red]Error:[/bold red] CSV file appears to be empty or has an invalid format.")
            return []
        # ---------------------

        # Now, text_stream's next line is the correct header row
        reader = csv.DictReader(text_stream)

        table = [row for row in reader]
        return table


def demo_retrieve_analog_data_table():
    """
    The endpoint for get_analog_table does not table arguments that allow fo much control.
    It is better to use 
    """
    typer.echo("Running: pipeline.api.mission.demo_retrieve_analog_data_table()...")
    typer.echo("Running: Calling 123scada.com using the Mission Client ...")
    party_name = "Mission"
    device_id = 22158
    device_name="Gayoso Pump Station"
    service_name = f"pipeline-external-api-{party_name}"
    overwrite=False

    username = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "username", prompt_message = f"Enter the username for the {party_name} API",hide=False, overwrite=overwrite)
    password = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "password", prompt_message = f"Enter the password for the {party_name} API", overwrite=overwrite)

    with MissionClient.login_to_session(username, password) as client: # works
        client.customer_id = client.get_customer_id_from_known_client()
        # Get the last 24 hours of analog table data
        end = TimeManager(TimeManager.now_rounded_to_hour()).as_datetime()
        start = end - timedelta(days=1)
        start_str = TimeManager(start).as_yyyymmdd()

        
        to_ms = lambda dt: int(dt.timestamp() * 1000)
        table_data = client.get_analog_table(device_id=device_id, 
                                             customer_id=client.customer_id,
                                             start_ms=to_ms(start), 
                                             end_ms=to_ms(end))
        

        print(f"table_data = {table_data}")
    return table_data


if __name__ == "__main__":
    device_name="Gayoso Pump Station"
    device_id = 22158
    end = TimeManager(TimeManager.now_rounded_to_hour()).as_datetime() # some time today
    start = end - timedelta(days=1) # some time yesterday
    start_date = TimeManager(start).as_yyyymmdd() # some time yesterday rounded down to 00:00
    csv_bytes, start_str = MissionClient.login_and_retrieve_analog_csv_bytes(device_name = device_name, 
                                                                                device_id = device_id,
                                                                                start_date=start_date,
                                                                                end_date=start_date)
    path = Path("exports") / (f"Gayoso_Analog_{start_str}.csv")
    MissionClient.save_csv_from_csv_bytes(path = path, csv_bytes=csv_bytes)

    analog_table = MissionClient.csv_bytes_to_table(csv_bytes)
    MissionTransformation.display_table_with_rich(analog_table)

