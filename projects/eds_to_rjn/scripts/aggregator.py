#pipeline.aggregator.py
import csv
import datetime
from collections import defaultdict
import os

from src.pipeline.api.rjn import send_data_to_rjn

def aggregate_and_send(data_file, checkpoint_file, rjn_base_url, headers_rjn):
    # Load data
    with open(data_file, newline='') as f:
        reader = csv.DictReader(f)
        grouped = defaultdict(list)
        for row in reader:
            key = (row["rjn_siteid"], row["rjn_entityid"])
            grouped[key].append(float(row["value"]))
    """
    # Aggregate and send
    for (siteid, entityid), values in grouped.items():
        avg_val = sum(values) / len(values)
        timestamp = datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)
        send_data_to_rjn(
            base_url=rjn_base_url,
            project_id=siteid,
            entity_id=entityid,
            headers=headers_rjn,
            timestamps=[timestamp.strftime('%Y-%m-%d %H:%M:%S')],
            values=[round(avg_val, 2)]
        )
    """
        
    # Prepare single timestamp (top of the hour UTC)
    timestamp = datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')

    # Check what has already been sent
    already_sent = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                siteid, entityid, timestamp = row
                already_sent.add((siteid, entityid, timestamp))

    # Load all available data from the live data CSV
    grouped = defaultdict(list)
    with open(data_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp = row["timestamp"]
            siteid = row["rjn_siteid"]
            entityid = row["rjn_entityid"]
            value = float(row["value"])
            key = (siteid, entityid)

            # Only include if not already sent
            if (siteid, entityid, timestamp) not in already_sent:
                grouped[key].append((timestamp, value))

    # Send data per entity
    for (siteid, entityid), records in grouped.items():
        # Sort timestamps if needed
        records.sort(key=lambda x: x[0])

        timestamps = [ts for ts, _ in records]
        values = [round(val, 2) for _, val in records]

        if timestamps:
            print(f"Sending {len(timestamps)} values to RJN for entity {entityid} at site {siteid}")
            send_data_to_rjn(
                base_url=rjn_base_url,
                project_id=siteid,
                entity_id=entityid,
                headers=headers_rjn,
                timestamps=timestamps,
                values=values
            )

            # Record successful sends
            with open(checkpoint_file, 'a', newline='') as f:
                writer = csv.writer(f)
                for ts in timestamps:
                    writer.writerow([siteid, entityid, ts])
        else:
            print(f"No new data to send for {siteid} / {entityid}")