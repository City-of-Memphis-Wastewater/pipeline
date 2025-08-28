import csv
import json

# Read your CSV file
# hardcoded filth
filepath = r"C:\Users\george.bennett\dev\pipeline\workspaces\eds_to_rjn\exports\manual_effluent.csv"

data_dict = {}
with open(filepath, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if not row:
            continue  # skip empty rows
        datetime_str, value_str = row
        data_dict[datetime_str.strip()] = float(value_str)

# Wrap it in your desired format
output = {
    "comments": "Manual upload via Postman.",
    "data": data_dict
}

# Save as JSON
with open("output.json", "w") as f:
    json.dump(output, f, indent=4)

print(json.dumps(output, indent=4))
