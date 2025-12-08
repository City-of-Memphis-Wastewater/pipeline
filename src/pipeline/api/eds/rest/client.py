# pipeline/api/eds/rest/client.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import requests
from datetime import datetime
import re
import logging
import time

from pipeline.time_manager import TimeManager
from pipeline.decorators import log_function_call
from pipeline.api.eds.exceptions import EdsLoginException

logger = logging.getLogger(__name__)

class EdsRestClient:
    def __init__(self):
        pass

    # --- Context Management (Pattern 2) ---
    def __enter__(self):
        """Called upon entering the 'with' block."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called upon exiting the 'with' block (for cleanup)."""
        
        # Close REST Session
        if hasattr(self, "session"):
            print(f"[{self.plant_name}] Closing REST session.")
            self.session.close()
            
                
        # Return False to propagate exceptions, or True to suppress them
        return False 
    
    @staticmethod
    def login_to_session(api_url, username, password, timeout=10):
        session = requests.Session()

        data = {'username': username, 'password': password, 'type': 'script'}
        response = session.post(f"{api_url}/login",
                                json=data,
                                verify=False,
                                timeout=timeout
                                )
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        json_response = response.json()
        #print(f"response = {response}")
        session.headers['Authorization'] = f"Bearer {json_response['sessionId']}"
        return session

    @staticmethod
    def login_to_session_with_api_credentials(api_credentials):
        try:
            session = EdsRestClient.login_to_session(
                api_url=api_credentials.get("url"),
                username=api_credentials.get("username"),
                password=api_credentials.get("password"),
                timeout=10
            )
            session.base_url = api_credentials.get("url")
            session.zd = api_credentials.get("zd")
            return session

        except requests.exceptions.ConnectTimeout:
            error_msg = "Connection to the EDS API timed out. Please check your VPN connection and try again."
            #print(f"\n{error_msg}")
            raise RuntimeError(error_msg) from None

        except EdsLoginException as e:
            #error_msg = f"Login failed for EDS API: {e}"
            error_msg = f"Login failed for EDS API"
            #print(f"\n{error_msg}")
            raise RuntimeError(error_msg) from None
        except Exception as e:
            #error_msg = f"Unexpected login error: {e}"
            error_msg = f"Unexpected login error"
            #print(f"\n{error_msg}")
            raise RuntimeError(error_msg) from None

    
    @staticmethod
    def get_license(session,api_url:str):
        response = session.get(f'{api_url}/license', json={}, verify=False).json()
        return response

    @staticmethod
    def print_point_info_row(row):
        # Desired keys to print, with optional formatting
        keys_to_print = {
            "iess": lambda v: f"iess:{v}",
            "ts": lambda v: f"dt:{datetime.fromtimestamp(v)}",
            "un": lambda v: f"un:{v}",
            "value": lambda v: f"av:{round(v, 2)}",
            "shortdesc": lambda v: str(v),
        }

        parts = []
        for key, formatter in keys_to_print.items():
            try:
                parts.append(formatter(row[key]))
            except (KeyError, TypeError, ValueError):
                continue  # Skip missing or malformed values

        print(", ".join(parts))

    @staticmethod
    def get_points_live(session, iess):
        "Access live value of point from the EDS, based on zs/api_id value (i.e. Maxson, WWTF, Server)"
        api_url = str(session.base_url) 

        query = {
            'filters' : [{
            'iess': [iess],
            'tg' : [0, 1],
            }],
            'order' : ['iess']
            }
        response = session.post(f"{api_url}/points/query", json=query, verify=False).json()
        
        if not response or "points" not in response:
            return None

        points = response["points"]
        if len(points) != 1:
            raise ValueError(f"Expected 1 point for iess='{iess}', got {len(points)}")

        return points[0]

    @staticmethod
    def get_tabular_trend(session, req_id, point_list):
        # The raw from EdsRestClient.get_tabular_trend() is brought in like this: 
        #   sample = [1757763000, 48.93896783431371, 'G'] 
        results = [[] for _ in range(len(point_list))]
        while True:
            api_url = str(session.base_url) 
            response = session.get(f'{api_url}/trend/tabular?id={req_id}', verify=False).json()
            
            for chunk in response:
                if chunk['status'] == 'TIMEOUT':
                    raise RuntimeError('timeout')

                for idx, samples in enumerate(chunk['items']):
                    for sample in samples:
                        #print(f"sample = {sample}")
                        structured = {
                            "ts": sample[0],          # Timestamp
                            "value": sample[1],       # Measurement value
                            "quality": sample[2],       # Optional units or label
                        }
                        results[idx].append(structured)

                if chunk['status'] == 'LAST':
                    return results


    @staticmethod
    def get_points_export(session,filter_iess: list=None, zd: str =None) -> str: 
        """
        Retrieves point metadata from the API, filtering by a list of IESS values.

        Args:
            session (requests.Session): The active session object.
            filter_iess (list): A list of IESS strings to filter by. Currently only allows one input.
            zd (str): An optional zone directory to filter by.
        
        Returns:
            str: The raw text response from the API.
        """

        api_url = str(session.base_url) 

        # Use a dictionary to build the query parameters.
        # The `requests` library handles lists gracefully by repeating the key.
        params = {}
        
        # Add the Zone Directory (zd) if provided, otherwise use the session's zd.
        if zd:
            params['zd'] = zd
        else:
            params['zd'] = str(session.zd)

        # Add the list of IESS values if the list is not empty.
        # The 'requests' library will automatically format this as
        # ?iess=item1&iess=item2&...
        # 1. Check if filter_iess is a list and join it into a comma-separated string.
        # 2. Add the resulting string to params, which the API is likely expecting.
        #print(f"filter_iess = {filter_iess}")
        if filter_iess:
            if isinstance(filter_iess, list) and len(filter_iess) > 0:
                # Convert the list to a single string using a delimiter
                iess_string = ",".join(filter_iess) # Join with a space ","
                #iess_string = " ".join(filter_iess) # Join with a space " "
                params['iess'] = iess_string
            elif isinstance(filter_iess, str):
                # If it's already a string, use it directly
                params['iess'] = filter_iess
        # --- END OF FIX ---
        
        params['order'] = 'iess'
        #print(f"params = {params}")
        zd = str(session.zd)  
        #order = 'iess'
        #query = '?zd={}&iess={}&order={}'.format(zd, filter_iess, order)
        request_url = f"{api_url}/points/export" #+ query
        
        response = session.get(request_url, params=params, json={}, verify=False)
        #print(f"Status Code: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}, Body: {response.text[:500]}")
        decoded_str = response.text
        return decoded_str


    @staticmethod
    def get_points_metadata(session, filter_iess=None, zd=None):
        """
        Retrieves and parses point metadata into a dictionary.

        Args:
            session (requests.Session): The active session object.
            filter_iess (list): A list of IESS strings to filter by.
            zd (str): An optional zone directory to filter by.
        
        Returns:
            dict: A dictionary where keys are IESS strings and values are
                  dictionaries of the point's attributes.
                  Returns an empty dictionary on failure.
        """
        raw_export_str = EdsRestClient.get_points_export(session, filter_iess, zd)
        
        all_points_metadata = {}
        
        # Regex to find key='value' pairs. Handles single-quoted values.
        # This pattern is more robust than a simple split.
        pattern = re.compile(r"(\w+)='([^']*)'")
        for iess_value in filter_iess:
            # We must make a separate API call for each IESS.
            # Use the existing get_points_export function, but pass a single
            # IESS value in a list so the URL formatting remains consistent.
            raw_export_str = EdsRestClient.get_points_export(session, filter_iess=[iess_value], zd=zd)

            
            for line in raw_export_str.strip().splitlines():
                # We are only interested in lines that start with 'POINT'
                if line.strip().startswith('POINT '):
                    # Extract key-value pairs using the regex
                    attributes = dict(pattern.findall(line))
                    
                    # Double-check that the returned IESS matches the requested one
                    if attributes.get('IESS') == iess_value:
                        all_points_metadata[iess_value] = attributes
                        break # We found our point, so we can stop parsing this response
        
        return all_points_metadata
    # --- Example of how to use it ---
    # (Assuming you have a 'session' object and a list of iess values)
    #
    # iess_list_to_filter = ['M100FI.UNIT0@NET0', 'M119FI.UNIT0@NET0']
    # session = # ... your session object from login
    #
    # # Get the parsed dictionary
    # points_data = EdsRestClient.get_points_metadata(session, filter_iess=iess_list_to_filter)
    #
    # # Now you can easily access the unit for 'M100FI.UNIT0@NET0'
    # unit = points_data.get('M100FI.UNIT0@NET0', {}).get('UN')
    # print(f"The unit for M100FI.UNIT0@NET0 is: {unit}")
    #
    # # You can also iterate through the results
    # for iess, attributes in points_data.items():
    #     print(f"Point: {iess}, Description: {attributes.get('DESC')}, Unit: {attributes.get('UN')}")
    
    @staticmethod
    def save_points_export(decoded_str, export_path):
        lines = decoded_str.strip().splitlines()

        with open(export_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")  # Save each line in the text file
    

    @staticmethod
    def create_tabular_request(session: requests.Session, api_url: str, starttime: int, endtime: int, points: list, step_seconds: int = 300):
        """
        Submit a tabular trend request. Returns request id on success, or None if failed.
        """

        data = {
            "period": {
                "from": starttime,
                "till": endtime,
            },
            "step": step_seconds,
            "items": [
                {
                    "pointId": {"iess": p},
                    "shadePriority": "DEFAULT",
                    "function": "AVG",
                }
                for p in points
            ],
        }

        try:
            res = session.post(f"{api_url}/trend/tabular", json=data, verify=False)
        except Exception as e:
            logger.error(f"Request failed to {api_url}/trend/tabular: {e}")
            return None

        if res.status_code != 200:
            logger.error(f"Bad status {res.status_code} from server: {res.text}")
            return None

        try:
            payload = res.json()
        except Exception:
            logger.error(f"Non-JSON response: {res.text}")
            return None

        req_id = payload.get("id")
        if not req_id:
            logger.error(f"No request id in response: {payload}")
            return None

        return req_id

    @staticmethod
    def wait_for_request_execution_session(session, api_url, req_id):
        st = time.time()
        while True:
            time.sleep(1)
            res = session.get(f'{api_url}/requests?id={req_id}', verify=False).json()
            status = res[str(req_id)]
            if status['status'] == 'FAILURE':
                raise RuntimeError('request [{}] failed: {}'.format(req_id, status['message']))
            elif status['status'] == 'SUCCESS':
                break
            elif status['status'] == 'EXECUTING':
                print('request [{}] progress: {:.2f}\n'.format(req_id, time.time() - st))

        print('request [{}] executed in: {:.3f} s\n'.format(req_id, time.time() - st))


    @log_function_call(level=logging.DEBUG)    
    @staticmethod
    def load_historic_data(session, filter_iess, starttime, endtime, step_seconds):    
        """
        Retrieves historic time series data for a list of points (IESS)
        within a specified time range and step interval using the EDS API.

        This function converts the start and end times to Unix timestamps,
        creates a tabular trend request, waits for its execution, and
        then retrieves the results.

        Args:
            session (EdsSession): The authenticated EDS API session object.
            filter_iess (list[str]): A list of point IDs (IESS) for which
                                    to retrieve data.
            starttime (str or int): The start time for the data request.
                                    Can be a datetime string or a Unix timestamp.
            endtime (str or int): The end time for the data request.
                                Can be a datetime string or a Unix timestamp.
            step_seconds (int): The aggregation interval (step size) in seconds.

        Returns:
            list[dict] or list: A list of dictionaries containing the historic
                                data results (tabular trend), or an empty list
                                if the request creation failed.
        """

        starttime = TimeManager(starttime).as_unix()
        endtime = TimeManager(endtime).as_unix() 
        logger.info(f"starttime = {starttime}")
        logger.info(f"endtime = {endtime}")


        point_list = filter_iess
        api_url = str(session.base_url) 
        request_id = EdsRestClient.create_tabular_request(session, api_url, starttime, endtime, points=point_list, step_seconds=step_seconds)
        if not request_id:
            logger.warning(f"Could not create tabular request for points: {point_list}")
            return []  # or None, depending on how you want the CLI to behave
        EdsRestClient.wait_for_request_execution_session(session, api_url, request_id)
        results = EdsRestClient.get_tabular_trend(session, request_id, point_list)
        logger.debug(f"len(results) = {len(results)}")
        return results
