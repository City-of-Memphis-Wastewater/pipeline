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
from prettytable import PrettyTable
from rich.console import Console
from rich.table import Table

from pipeline.security_and_config import SecurityAndConfig
#from pipeline_tests.variable_clarity_grok import Redundancy
from pipeline_tests.variable_clarity import Redundancy, instancemethod
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
    def transform_analog_data(table_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transforms the nested Mission API analog data structure into a flat
        list of dictionaries, mapping scaledValues to their corresponding channel names.

        Args:
            table_data: The raw dictionary returned by the analog data table API call.

        Returns:
            A list of dictionaries, where each dictionary is a time-stamped row.
        """
        
        # 1. Extract Channel Names and Units from 'setting'
        # We need to build an ordered list of column headers (names and units).
        # This assumes the order in 'scaledValues' matches the order in 'setting'.
        channel_headers = []
        
        # The API includes channel numbers, but they might not be sequential or start at 1.
        # We rely on the *order* of the 'setting' list matching the order of 'scaledValues'.
        for setting in table_data.get('setting', []):
            # Format the header as 'Name (Unit)' for clarity, or just 'Name'
            header = f"{setting['name']} ({setting['unit']})" if setting.get('unit') else setting['name']
            channel_headers.append(header)
        
        # 2. Iterate and Flatten the Data
        flat_data_list = []
        
        # The actual data is in the 'analogMeasurements' list
        for measurement in table_data.get('analogMeasurements', []):
            row = {}
            
            # Add the timestamp column
            # Formatting for readability and modularity (e.g., stripping milliseconds)
            dt_str = measurement.get('localDateTime')
            if dt_str:
                try:
                    # Parse and reformat the datetime string
                    dt_obj = datetime.fromisoformat(dt_str)
                    row['Date/Time'] = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    row['Date/Time'] = dt_str # Keep original if parsing fails

            # Extract the list of values (e.g., [{'value': 10923.0}, {'value': 14.18}, ...])
            scaled_values = measurement.get('scaledValues', [])
            
            # Map values to their channel headers
            for i, value_dict in enumerate(scaled_values):
                if i < len(channel_headers):
                    header = channel_headers[i]
                    # Store the raw float value, which is better than converting to string here
                    row[header] = value_dict.get('value')
                # else: Skip if there are more scaledValues than channels defined in settings
            
            # Optionally include 'calculatedWeirGpm' if it's meaningful, but it's 'NaN' here.
            # if measurement.get('calculatedWeirGpm') != 'NaN':
            #     row['calculatedWeirGpm'] = measurement['calculatedWeirGpm']

            flat_data_list.append(row)

        return flat_data_list
    
    
    @staticmethod
    def display_table_with_prettytable(data_list: list):
        """
        Creates and prints a formatted table from a list of dictionaries.
        """
        if not data_list:
            print("No data to display.")
            return

        # 1. Initialize the table and set field names
        # Use the keys from the first dictionary as column headers
        field_names = list(data_list[0].keys())
        table = PrettyTable()
        table.field_names = field_names

        # 2. Add rows (using the list of dictionaries)
        for row_dict in data_list:
            # Get the values in the order defined by field_names
            row_values = [row_dict.get(name) for name in field_names]
            table.add_row(row_values)
            
        # 3. Apply formatting for better readability
        table.align = "r"          # Right-align all data
        table.align["Date/Time"] = "l" # Left-align the Date/Time column
        table.float_format = ".2"  # Format floats to 2 decimal places

        print(table)
        # Example usage (assuming analog_table is available)
        # display_table_with_prettytable(analog_table)


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


    @staticmethod
    def demo_transform_analog_table(table_data):
    # --- Demonstration of Use ---

        analog_table = MissionTransformation.transform_analog_data(table_data)

        print("\n--- Transformed Modular Data (First 3 Rows) ---")
        print(f"Total Rows Transformed: {len(analog_table)}")
        for row in analog_table[:3]:
            print(row)

        # Example of modular use: Calculate the average Wet Well Level
        if analog_table:
            wet_well_key = "Wet Well Level (Feet)" # Use the generated key
            valid_levels = [r[wet_well_key] for r in analog_table if isinstance(r[wet_well_key], (int, float))]
            
            if valid_levels:
                average_level = sum(valid_levels) / len(valid_levels)
                print(f"\nAverage {wet_well_key}: {average_level:.2f} Feet")

        return analog_table

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

        typer.echo(f"\n[bold green]CURL/External Bearer Token:[/bold green] {token}") # <-- Print the actual token


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

    @instancemethod
    def get_analog_table(self:"MissionClient", 
                         device_id: int = None, 
                         customer_id: int | None = None, 
                         start_ms: int = None, 
                         end_ms: int = None, 
                         start_row: int = 1, 
                         page_size: int = 1440, #720,
                         )->dict:
        
        print(f" MissionClient.get_analog_table() ...")
        url = f"{MissionClient.services_api_url}/Analog/Table"
        

        if customer_id is None and self.customer_id is None:
            self.customer_id = self.get_customer_id_from_known_client(self) # explicit assignment
            customer_id = self.customer_id
        
        print(f"start_ms = {start_ms}")
        print(f"end_ms = {end_ms}")

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
        # Use self.session.get() instead of requests.get() to use the authenticated session
        r = self.session.get(url, params=params)
        r.raise_for_status()
        print(f" MissionClient.get_analog_table() complete.")
        return r.json()
    
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
                            resolution: int = 1,
                            file_name: str = None)->bytes:
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
            file_name (str, optional): A suggested filename passed to the server to populate the 
                Content-Disposition header. It does NOT control the local save path. Defaults to a generated name.
        
        Returns:
            bytes: The raw CSV content. The calling function must write this to disk.
        """
        
        url = MissionClient.get_analog_download_url()

        if file_name is None:
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


def demo_retrieve_analog_data_and_save_csv()->bytes:
    """
    The download function only accepts days as an input.
    If Start Date and End Date value are identical, 
    a 24-hour timeframe worth of data will be downloaded, 
    for 00:00 to 23:58, every two minutes, 
    for the date listed.

    This function is not necessary to be a part of our API flow unless we want CSV backups, but it is smoother to use client.get_analog_table() rather than client.get_analog_csv_bytes().
    """
    typer.echo("Running: pipeline.api.mission.demo_retrieve_analog_data_and_save_csv()...")
    typer.echo("Running: Calling 123scada.com using the Mission Client ...")

    party_name = "Mission"
    service_name = f"pipeline-external-api-{party_name}"
    overwrite=False

    device_name="Gayoso Pump Station"
    device_id = 22158
    
    username = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "username", prompt_message = f"Enter the username for the {party_name} API",hide=False, overwrite=overwrite)
    password = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "password", prompt_message = f"Enter the password for the {party_name} API", overwrite=overwrite)

    with MissionClient.login_to_session(username, password) as client: # works
        client.customer_id = client.get_customer_id_from_known_client()
        print(f"client.customer_id = {client.customer_id}")
        
        
        # Get the last 24 hours of analog table data
        #end = datetime.now()
        end = TimeManager(TimeManager.now_rounded_to_hour()).as_datetime()
        start = end - timedelta(days=1)
        start_filename_str = TimeManager(start).as_yyyymmdd()

        # Or download CSV for 6–11 Oct 2025
        csv_bytes = client.get_analog_csv_bytes(
            device_id=device_id,
            device_name=device_name,
            #start_date="20251006", # start at 00:00 for date provided in format YYYYMMDD
            #end_date="20251011" # end at 23:58 for date provided in format YYYYMMDD
            start_date=start_filename_str, # start at 00:00 for date provided in format YYYYMMDD
            end_date=start_filename_str # end at 23:58 for date provided in format YYYYMMDD
        )
        typer.echo("\nRunning: Generating sample file... ")
        path = Path("exports") / (f"Gayoso_Analog_{start_filename_str}.csv")
        with open(path, "wb") as f:
            f.write(csv_bytes)

        typer.echo(f"\nFile generated: {str(path)}")

        typer.echo("\nJob Complete.")

    return csv_bytes

def demo_retrieve_analog_data_table():
    """
    The endpoint for get_analog_table does not table arguments that allow fo much control.
    It is better to use 
    """
    typer.echo("Running: pipeline.api.mission.demo_retrieve_analog_data_table()...")
    typer.echo("Running: Calling 123scada.com using the Mission Client ...")
    party_name = "Mission"
    device_id = 22158
    service_name = f"pipeline-external-api-{party_name}"
    overwrite=False

    username = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "username", prompt_message = f"Enter the username for the {party_name} API",hide=False, overwrite=overwrite)
    password = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "password", prompt_message = f"Enter the password for the {party_name} API", overwrite=overwrite)

    with MissionClient.login_to_session(username, password) as client: # works
        client.customer_id = client.get_customer_id_from_known_client()
        # Get the last 24 hours of analog table data
        #end = datetime.now()
        end = TimeManager(TimeManager.now_rounded_to_hour()).as_datetime()
        print(end)
        start = end - timedelta(days=1)
        to_ms = lambda dt: int(dt.timestamp() * 1000)
        table_data = client.get_analog_table(device_id=device_id, 
                                             customer_id=client.customer_id,
                                             start_ms=to_ms(start), 
                                             end_ms=to_ms(end))
        #print(f"table_data = {table_data}")
        print(f"Fetched {len(table_data.get('analogMeasurements', []))} rows from analog table.") # separate process
    return table_data


if __name__ == "__main__":
    if True:
        demo_retrieve_analog_data_and_save_csv()
    else:
        table_data = demo_retrieve_analog_data_table()
        analog_table = MissionTransformation.transform_analog_data(table_data)
        #MissionTransformation.display_table_with_prettytable(analog_table)
        MissionTransformation.display_table_with_rich(analog_table)


