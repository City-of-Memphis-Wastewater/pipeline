from __future__ import annotations
import re
import requests

def get_point_live(session: requests.Session, iess: str) -> dict | None:
    api_url = str(session.base_url)
    query = {"filters": [{"iess": [iess], "tg": [0, 1]}]}
    resp = session.post(f"{api_url}/points/query", json=query, verify=False)
    data = resp.json()
    return data.get("points", [None])[0]

def get_points_export(session: requests.Session, filter_iess: list | None = None, zd: str | None = None) -> str:
    params = {"zd": zd or session.zd, "order": "iess"}
    if filter_iess:
        params["iess"] = ",".join(filter_iess) if isinstance(filter_iess, list) else filter_iess
    resp = session.get(f"{session.base_url}/points/export", params=params, verify=False)
    return resp.text

def get_points_metadata(session: requests.Session, iess_list: list[str]) -> dict[str, dict]:
    raw = get_points_export(session, filter_iess=iess_list)
    pattern = re.compile(r"(\w+)='([^']*)'")
    metadata = {}
    for line in raw.splitlines():
        if line.startswith("POINT "):
            attrs = dict(pattern.findall(line))
            if attrs.get("IESS") in iess_list:
                metadata[attrs["IESS"]] = attrs
    return metadata
