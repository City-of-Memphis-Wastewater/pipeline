from __future__ import annotations
from pipeline.time_manager import TimeManager

def load_historic_data(session, iess_list: list[str], starttime, endtime, step_seconds: int = 300):
    start = TimeManager(starttime).as_unix()
    end = TimeManager(endtime).as_unix()
    api_url = str(session.base_url)

    from . import trend_internal  # internal helpers (create request, poll, fetch)
    req_id = trend_internal.create_request(session, api_url, start, end, iess_list, step_seconds)
    if not req_id:
        return []
    trend_internal.wait_for_completion(session, api_url, req_id)
    return trend_internal.fetch_tabular(session, api_url, req_id, iess_list)
