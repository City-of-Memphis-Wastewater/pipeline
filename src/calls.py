import requests
import certifi
import sys
import json
import time

def test_connection_to_internet():
    try:
        # call Cloudflare's CDN test site, because it is lite.
        response = requests.get("http://1.1.1.1", timeout = 5)
        print("You are connected to the internet.")
    except:
        print(f"It appears you are not connected to the internet.")
        sys.exit()

class EdsCalls:
    ip_address_maxson = "172.19.4.127"
    ip_address_stiles = "172.19.4.128"

    def __init__(self,address_object):
        self.address_object = address_object



    def test_connection_to_eds(address_object):
        for api_url in address_object.get_rest_api_url_list():
            try:
            #if True:
                api_url = "http://172.19.4.127:43084/api/v1/"
                login_url = api_url+"login"
                data = {'username' : 'admin', 'password' : '', 'type' : 'rest client'}
                response = requests.post(login_url, json = data)
                #print(f"Status Code: {response.status_code}")
                #print(f"Response Text: '{response.text}'")
                if response.status_code == 200:
                    try:
                        token = response.json()
                    except json.JSONDecodeError:
                        print("Failed to parse JSON:")
                        token = None
                #request_url = api_url + 'ping'
                #headers = {'Authorization' : 'Bearer {}'.format(token['sessionId'])}
                #response = requests.get(request_url, headers = headers)

                print(f"You are able to access an EDS: {api_url}") 
            #else:
            except:
                print(f"Connection to an EDS is failing: {api_url}")
                sys.exit()

    def get_license(address_object,header):
        api_url = address_object.get_
        request_url = api_url + 'license'
        request = requests.get(request_url, headers=header)
        return request

    def get_token(address_object):
        api_url = address_object.get_auth_url() # if none, use known, if else, us Address.get_current_ip_address()
        request_url = api_url + 'login'
        data = {'username' : 'admin', 'password' : '', 'type' : 'rest client'}
        #data = {'username' : 'rjn', 'password' : 'RjnClarity2025', 'type' : 'rest client'}  
        response = requests.post(request_url, json = data)
        #print(f"response={response}")
        token = json.loads(response.text)
        headers = {'Authorization' : 'Bearer {}'.format(token['sessionId'])}
        return api_url,headers

class RjnCalls:
    def __init__(self,address_object):
        self.address_object = address_object

#def make_request(url, data, retries=3, delay=2):


def make_request(url, data=None, params = None, method="POST", headers=None, retries=3, delay=2, timeout=10, verify_ssl=True):
    
    try:
        default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        merged_headers = {**default_headers, **(headers or {})}
        print(f"merged_headers = {merged_headers}")

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
        print("\nflag\n")
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