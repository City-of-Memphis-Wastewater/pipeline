#pipeline.aggregator.py
import csv
from collections import defaultdict
import os
from pprint import pprint

from src.pipeline.api.rjn import RjnClient #send_data_to_rjn2
from src.pipeline.time_manager import TimeManager


def aggregate_and_send(session_rjn, data_file, checkpoint_file):

    # Check what has already been sent
    already_sent = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                projectid, entityid, timestamp = row
                already_sent.add((projectid, entityid, timestamp))

    print(f"len(already_sent) = {len(already_sent)}")

    # Load all available data from the live data CSV
    grouped = defaultdict(list)
    with open(data_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["value"] == "":
                 #print("Skipping empty row")
                 continue
            elif "timestamp" not in row:
                print(row.keys())
                print("timestamp not in row")
                continue
            timestamp = row["timestamp"]
            projectid = row["rjn_projectid"]
            entityid = row["rjn_entityid"]
            value = float(row["value"])
            key = (projectid, entityid)
            # Only include if not already sent
            if (projectid, entityid, timestamp) not in already_sent:
                grouped[key].append((timestamp, value))

    print(f"len(grouped) = {len(grouped)}")

    # Send data per entity
    for (projectid, entityid), records in grouped.items():
        print(f"projectid = {projectid}")
        # Sort timestamps if needed
        records.sort(key=lambda x: x[0])

        timestamps = [ts for ts, _ in records]
        values = [val for _, val in records]

        if timestamps:
            print(f"Attempting to send {len(timestamps)} values to RJN for entity {entityid} at site {projectid}")
            '''
            send_data_to_rjn(
                base_url=rjn_base_url,
                project_id=projectid,
                entity_id=entityid,
                headers=headers_rjn,
                timestamps=timestamps,
                values=values
            )
            '''
            RjnClient.send_data_to_rjn(
            session_rjn,
            base_url = session_rjn.custom_dict["url"],
            project_id=row["rjn_projectid"],
            entity_id=row["rjn_entityid"],
            timestamps=timestamps,
            values=[row["value"]]
        )

            # Record successful sends
            if os.path.exists(checkpoint_file):
                with open(checkpoint_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    for ts in timestamps:
                        writer.writerow([projectid, entityid, TimeManager(ts).as_formatted_date_time()])
        else:
            print(f"No new data to send for {projectid} / {entityid}")