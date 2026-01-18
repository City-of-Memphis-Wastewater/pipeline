from __future__ import annotations
import requests
from .exceptions import EdsTimeoutError, EdsAuthError

def login_to_session(api_url: str, username: str, password: str, timeout: int = 10) -> requests.Session:
    session = requests.Session()
    payload = {"username": username, "password": password, "type": "script"}
    
    try:
        response = session.post(
            f"{api_url}/login",
            json=payload,
            verify=False,
            timeout=timeout
        )
        response.raise_for_status()
        session.headers["Authorization"] = f"Bearer {response.json()['sessionId']}"
        return session
    except requests.exceptions.ConnectTimeout:
        raise EdsTimeoutError("Connection to the EDS API timed out. Please check your VPN connection and try again.")
    except requests.exceptions.RequestException as e:
        if getattr(e.response, "status_code", None) in (401, 403):
            raise EdsAuthError("Login failed: invalid username or password.")
        raise EdsTimeoutError(f"Cannot reach EDS API at {api_url}") from e

def login_to_session_with_credentials(credentials: dict) -> requests.Session:
    """High-level wrapper used by core and CLI"""
    session = login_to_session(
        api_url=credentials["url"],
        username=credentials["username"],
        password=credentials["password"]
    )
    session.base_url = credentials["url"]
    session.zd = credentials.get("zd")
    return session
