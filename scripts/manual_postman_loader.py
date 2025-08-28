import pandas as pd
import json

# Read your Excel file
filepath = r"C:\Users\george.bennett\dev\pipeline\workspaces\eds_to_rjn\exports\manual_effluent.csv"
df = pd.read_csv(filepath, header=None, names=["datetime", "value"])

# Convert to dict {datetime: value}
data_dict = dict(zip(df["datetime"].astype(str), df["value"]))

# Wrap it in your desired format
output = {
    "comments": "Manual upload via Postman.",
    "data": data_dict
}

# Save as JSON
with open("output.json", "w") as f:
    json.dump(output, f, indent=4)

print(json.dumps(output, indent=4))
