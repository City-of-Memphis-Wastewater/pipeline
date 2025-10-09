import requests
import time
from urllib.parse import quote_plus

class MissionClient:
    def __init__(self, token: str, customer_id: int):
        self.base_url = "https://123scada.com/Mc.Services/api"
        self.report_base = "https://123scada.com/Mc.Reports/api"
        self.customer_id = customer_id
        self.headers = {"Authorization": f"Bearer {token}"}

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