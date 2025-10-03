'''
Title: sanitizer.py
Author: Clayton Bennett
Created: 2025 05-May 17th

Purpose:
I like it when data gathered is data returned. Sanitization should not happen during import. If not entirely probitive, the entirety of the raw should be available for unforeseen use cases.
So. We need explicit and discernible sanitization scenarios, called a scripted approach, following the preparation, collection, and aggregation, insert buzz words here, etc.
'''
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
from datetime import datetime
from pipeline.helpers import round_datetime_to_nearest_past_five_minutes

def sanitize_data_for_printing(data):
    #data_sanitized_for_printing = data
    #pass
    #return data_sanitized_for_printing
    return data

def sanitize_data_for_aggregated_storage(data):
    sanitized = []
    for row in data:
        rounded_dt = round_datetime_to_nearest_past_five_minutes(datetime.fromtimestamp(row["ts"])) # arguably not appropriate at this point. round at transmission
        #row["timestamp_sani"] = rounded_dt
        #row["value_rounded"] = round(row["value"], 2)

        sanitized.append({
            "timestamp": rounded_dt.isoformat(),
            "ts": rounded_dt.timestamp(),
            "iess": row.get("iess"),
            "sid": row.get("sid"),
            "un": row.get("un"),
            "shortdesc": row.get("shortdesc"),
            "rjn_projectid": row.get("rjn_projectid"),
            "rjn_entityid": row.get("rjn_entityid"),
            "value": round(row.get("value"), 2)
        })
                
    data_sanitized_for_aggregated_storage = sanitized
                    
    return data_sanitized_for_aggregated_storage