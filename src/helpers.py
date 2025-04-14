import json
def load_json(filepath):
    # Load JSON data from the file
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data