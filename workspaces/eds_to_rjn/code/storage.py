import csv
from datetime import datetime
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9

'''
Mostly defunct now that eds tabular trend is working. But still interesting.
Use: 
    ```
    storage.store_live_values(data, workspace_manager.get_aggregate_dir() / "live_data.csv") 
    ```
'''
def store_live_values(data, path):
    with open(path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        if f.tell() == 0:  # file is empty
            writer.writeheader()
        writer.writerows(data)
    print(f"Live values stored, {datetime.now()} to {path}")