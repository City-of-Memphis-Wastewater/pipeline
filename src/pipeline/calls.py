import requests
import certifi
import platform
import subprocess
import sys
import time
from urllib.parse import urlparse

def test_connection_to_internet():
    try:
        # call Cloudflare's CDN test site, because it is lite.
        response = requests.get("http://1.1.1.1", timeout = 5)
        print("You are connected to the internet.")
    except:
        print(f"It appears you are not connected to the internet.")
        sys.exit()

def make_request(url, data=None, params = None, method="POST", headers=None, retries=3, delay=2, timeout=10, verify_ssl=True):
    
    try:
        default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        merged_headers = {**default_headers, **(headers or {})}
        #print(f"merged_headers = {merged_headers}")

        verify = certifi.where() if verify_ssl else False

        request_func = {
            "POST": requests.post,
            "GET": requests.get,
            "PUT": requests.put,
            "DELETE": requests.delete,
            "PATCH": requests.patch,
        }.get(method.upper())

        if not request_func:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response = request_func(
            url,
            json=data,
            params=params,
            headers=merged_headers,
            timeout=timeout,
            verify=verify
        )
        if response is None:
            raise RuntimeError("Received an empty response from the server.")
        else:
            response.raise_for_status()
        return response
    except requests.exceptions.SSLError as e:
        raise ConnectionError(f"SSL Error: {e}")
    except requests.exceptions.HTTPError as e:
        if response.status_code == 500:
            print(f"HTTP 500 Error - Response content: {response.text}")
        elif response.status_code == 503 and retries > 0:
            # Retry the request if the server is unavailable
            print(f"Service unavailable (503). Retrying in {delay} seconds...")
            time.sleep(delay)
            #return make_request(url, data, retries - 1, delay * 2)  # Exponential backoff
            return make_request(
                url=url,
                data=data,
                params=params,
                method=method,
                headers=headers,
                retries=retries - 1,
                delay=delay * 2,
                timeout=timeout,
                verify_ssl=verify_ssl
            )
        elif response.status_code == 403:
            raise PermissionError("Access denied (403). The server rejected your credentials or IP.")
        else:
            raise RuntimeError(f"HTTP error: {response.status_code} {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise

def call_ping(url):
    parsed = urlparse(url)
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", parsed.hostname]
    return subprocess.call(command) == 0  # True if ping succeeds