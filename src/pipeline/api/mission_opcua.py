# pipeline/api/mission_opcua.py
from __future__ import annotations
from datetime import datetime, timedelta
import csv
from io import StringIO
import time
from typing import List, Dict

from opcua import Client, ua
from opcua.crypto import security_policies
from opcua.common.uaerrors import UaError

class MissionOPCUAClient:
    """
    MissionOPCUAClient handles connection and data retrieval from the Mission OPC UA Server.
    
    📝 Notes on Authentication and Security:
    - Requires X.509 certificate for application authentication (self-signed or CA-issued).
    - Use OpenSSL or opcua tools to generate cert/key if not provided.
      Example: openssl req -x509 -newkey rsa:2048 -keyout client_key.pem -out client_cert.pem -days 365 -nodes -subj "/CN=YourClient/O=YourOrg"
    - Server certificate must be trusted; fetch it during connection if needed.
    - Username/password for user authentication (request from Mission support; may differ from web creds).
    - Historical access assumes server support (confirm via manual or support).
    - Address space: Browse to discover; typical: Objects > [Customer] > [RTUs] > [DeviceName or ID] > [DataPoints e.g., AnalogInputs > AI1 > Value]
    - Adapt node paths based on browsing your server's structure (use the browse_example method).
    - For production, register client cert with Mission if required.
    - Download OPC UA User Manual for address space details: https://www.123mc.com/wp-content/uploads/2017/04/OPC-UA-User-Manual-3.docx
    """

    def __init__(self, username: str, password: str, cert_path: str, key_path: str, endpoint: str = "opc.tcp://opcua.123mc.com:4840/"):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.cert_path = cert_path
        self.key_path = key_path
        self.client = Client(self.endpoint)
        self.client.set_security(
            security_policies.SecurityPolicyBasic256Sha256,
            certificate_path=self.cert_path,
            private_key_path=self.key_path,
            mode=ua.MessageSecurityMode.SignAndEncrypt
        )
        self.client.application_uri = "urn:your:client:uri"  # Customize with your URI
        self.client.set_user(self.username)
        self.client.set_password(self.password)
        self.customer_id = None  # Set after browsing if needed
        self.connected = False

    def connect(self):
        try:
            self.client.connect()
            self.connected = True
            print("Connected to OPC UA Server.")
        except UaError as e:
            raise ValueError(f"Connection failed: {e}. Check certs, creds, firewall (port 4840), or contact support.")

    def disconnect(self):
        if self.connected:
            self.client.disconnect()
            self.connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def browse_example(self, start_node_id: str = "i=85"):  # i=85 is Objects folder
        """Browse and print address space structure for discovery."""
        node = self.client.get_node(ua.NodeId.from_string(start_node_id))
        print(f"Browsing from {node.get_browse_name().Name}")
        children = node.get_children()
        for child in children:
            print(f"- {child.get_browse_name().Name} (NodeId: {child.nodeid})")
            # Recurse if folder: if child.get_node_class() == ua.NodeClass.Object: self.browse_example(str(child.nodeid))

    def get_device_node(self, device_name: str, device_id: int = None):
        """Find device/RTU node; adapt based on your address space (use browse_example first)."""
        # Assume structure: Objects > Customer > RTUs > DeviceName
        objects = self.client.get_objects_node()
        # Traverse to RTUs folder (replace with actual path)
        rtus_folder = objects.get_child(["0:YourCustomer", "0:RTUs"])  # Placeholder; adapt
        device_node = None
        for child in rtus_folder.get_children():
            name = child.get_browse_name().Name
            if name == device_name or (device_id and str(device_id) in name):
                device_node = child
                break
        if not device_node:
            raise ValueError(f"Device '{device_name}' not found. Browse to confirm path.")
        return device_node

    def get_analog_nodes(self, device_node: ua.Node):
        """Find analog data nodes under device; adapt based on structure."""
        # Assume: Device > AnalogInputs > AI1 > Value, AI2 > Value, etc.
        analog_folder = device_node.get_child("0:AnalogInputs")  # Placeholder
        analog_nodes = {}
        for child in analog_folder.get_children():
            if child.get_node_class() == ua.NodeClass.Object:
                value_node = child.get_child("0:Value")  # Or "0:ScaledValue"
                analog_nodes[child.get_browse_name().Name] = value_node
        return analog_nodes

    def get_analog_table(self, device_id: int, device_name: str, start_ms: int, end_ms: int, max_values: int = 0):
        """Retrieve historical analog data (like table); assumes history support."""
        if not self.connected:
            self.connect()
        device_node = self.get_device_node(device_name, device_id)
        analog_nodes = self.get_analog_nodes(device_node)
        if not analog_nodes:
            raise ValueError("No analog nodes found.")
        
        start_time = datetime.utcfromtimestamp(start_ms / 1000)
        end_time = datetime.utcfromtimestamp(end_ms / 1000)
        results = {"analogMeasurements": []}
        
        for name, node in analog_nodes.items():
            details = ua.ReadRawModifiedDetails()
            details.IsReadModified = False
            details.StartTime = ua.uatypes.DateTime(start_time)
            details.EndTime = ua.uatypes.DateTime(end_time)
            details.NumValuesPerNode = max_values  # 0 = all
            details.ReturnBounds = False
            
            result = node.history_read(details)
            for dv in result.HistoryData.DataValues:
                results["analogMeasurements"].append({
                    "point": name,
                    "value": dv.Value.Value,
                    "timestamp": dv.SourceTimestamp.timestamp() * 1000,  # ms
                    "status": dv.StatusCode.name
                })
        
        return results

    def download_analog_csv(self, device_id: int, device_name: str, start_date: str, end_date: str, file_name: str = None):
        """Download historical analog data as CSV bytes."""
        # Parse dates (YYYYMMDD to ms)
        start_dt = datetime.strptime(start_date, "%Y%m%d")
        end_dt = datetime.strptime(end_date, "%Y%m%d") + timedelta(days=1)  # End inclusive
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        
        table_data = self.get_analog_table(device_id, device_name, start_ms, end_ms)
        measurements = table_data.get("analogMeasurements", [])
        
        if file_name is None:
            file_name = f"Analog_{device_name.replace(' ', '')}_DataPoints_{start_date}.csv"
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Point", "Value", "Timestamp (ms)", "Status"])
        for meas in measurements:
            writer.writerow([meas["point"], meas["value"], meas["timestamp"], meas["status"]])
        
        return output.getvalue().encode("utf-8")

def demo_retrieve_analog_data_and_save_csv():
    from pipeline.env import SecretConfig
    from pipeline.workspace_manager import WorkspaceManager
    workspace_name = WorkspaceManager.identify_default_workspace_name()
    workspace_manager = WorkspaceManager(workspace_name)

    secrets_dict = SecretConfig.load_config(secrets_file_path=workspace_manager.get_secrets_file_path())
    username = secrets_dict.get("contractor_apis", {}).get("Mission", {}).get("opc_username")  # Use OPC-specific creds
    password = secrets_dict.get("contractor_apis", {}).get("Mission", {}).get("opc_password")
    cert_path = secrets_dict.get("contractor_apis", {}).get("Mission", {}).get("client_cert_path")
    key_path = secrets_dict.get("contractor_apis", {}).get("Mission", {}).get("client_key_path")

    with MissionOPCUAClient(username, password, cert_path, key_path) as client:
        # Optional: Browse to discover structure
        # client.browse_example()

        # Get last 24 hours of analog table data
        end = datetime.utcnow()
        start = end - timedelta(days=1)
        to_ms = lambda dt: int(dt.timestamp() * 1000)
        table_data = client.get_analog_table(device_id=22158, device_name="Gayoso Pump Station", start_ms=to_ms(start), end_ms=to_ms(end))
        print(f"table_data = {table_data}")
        print(f"Fetched {len(table_data.get('analogMeasurements', []))} measurements.")

        # Download CSV for 6–11 Oct 2025
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
