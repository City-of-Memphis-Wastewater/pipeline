# collector.py
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from src.pipeline.helpers import round_datetime_to_nearest_past_five_minutes
from src.pipeline.api.eds import EdsClient


def collect_live_values(session, queries_dictlist_filtered_by_session_key):   
    data = []
    for row in queries_dictlist_filtered_by_session_key:
        #print(f"\trow = {row}")
        # Skip empty rows (if all values in the row are empty or None)
        if not any(row.values()):
            print("Skipping empty row.")
            continue
        
        # light validation - if you want to change column keys, that could be cool
        #required_cols = ["iess", "rjn_projectid", "rjn_entityid"]
        required_cols = ["iess"]
        if any(c not in row for c in required_cols):
            raise ValueError(f"Row missing required column keys: {row}")
        
        try:
            # extract and validate iess value from CSV row before it is used to retrieve data
            iess = str(row["iess"]) if row["iess"] not in (None, '', '\t') else None
        except KeyError as e:
            print(f"Missing expected column in CSV: {e}")
            continue
        except ValueError as e:
            print(f"Invalid data in row: {e}")
            continue
        
        try:
            point_data = EdsClient.get_points_live_mod(session, iess)
            if point_data is None:
                print(f"No data returned for iess={iess}")
                continue
            conflicts = set(row.keys()) & set(point_data.keys())
            if conflicts:
                logger.debug(f"Warning: column key collision on {conflicts}, for iess = {iess}. This is expected.")
            '''
            Not the worst idea:
            Use nested structures
            Instead of flattening all column keys into the same dict, keep fetched data as a sub-dictionary.
            In which case, the aggregate should be JSON (or TOML, whatever), not CSV.
            However, we have something that works. It is fine for now.
            '''
            # Retrieved point data is flatly added to the existing row from the query.   
            row.update(point_data) 
            data.append(row)
        except Exception as e:
            print(f"Error on row: {e}")
    return data

if __name__ == "__main__":
    print("[x] from src.pipeline import collector")
    print("[x] from src.pipeline import collector.collector_live_vales(session,query_list)")
    print("[ ] from src.pipeline import collector.collector_live_vales(session,query_dict)")