from datetime import datetime, timedelta

from src.exploratory.mission_client import MissionClient
token = "YOUR_BEARER_TOKEN"
token = "3WhLq_PBIa1VBVG5VdGZOlKIjSHOxOyXW49c6f1Ct_C8DiCx98Q8FQ9hoqr_nEYsENKiyDuLKNCthYQ700h5ZDmKubNu83fEGcWPHIbKN0AYgugejslE3RmYRpvokkN1CQ1hwNSnSBFVq9FFBgIvdyuIOdQSNOSwsbmPdZONC8jKvnAJBSB2o01Dj3pagQ3ov0ZDDS3RuR8lizldjBpMM1jqWv8JIhvirF-Ro71gpUbz7xTUJyIuriarOzuRNIi8MOEmuiHn2iSpyPuHW2cuzbFEUvD2FwmE9VjccWwPTfGQ86a9LamitCUup5g4M7WdIahk-ZR_iuKK_2qyRcr7_Jxc6Yw9Dk0vBMKXCRc9LpgN1pYBcP3av-W5chnUXGBDv52Upc4xrVxPbHNjSV1542qNNQogdeY10Tcw-02EHdgD9vtMf9K3x7rXyc8Za7w2DPj8zafF2D72mbNcKaZ7ESw65dtGoBooIPtZ2lZgib_70d7K2rjmiy-ChObXEgJgfpUSDq7HDCJJlop2sqSDtsrNQGYbYaaL9Gd1NAGSu0qnW0JYJq7J-dRsIFEpwHVoP1bwxvONxGa6_P7iFpVFuYW-62xoC-nUwlKqYQW994Yz47ZNaRx2MXvw4MSNOkv-9VG4W5arqtSjFpeI86wydBZID_O6jbPKX3NxcOMzGa6VqTKURcy4NAoL4GzwryhHEUtIttSn2mCS4wjnXuQ0dVHedzSnzdRPfXxUIUid161dP-wy8gn1uZlBGtleK2igjFSdCJVsuvULGVGr5mKdOw"
client = MissionClient(token, customer_id=10892)
print(f"client.headers = {client.headers}")

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
