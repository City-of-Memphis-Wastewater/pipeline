import requests
import sys
import json

class EdsCalls:
    ip_address_maxson = "172.19.4.127"
    ip_address_stiles = "172.19.4.128"

    def __init__(self,address_object):
        self.address_object = address_object

    def test_connection_to_internet():
        try:
            # call Cloudflare's CDN test site, because it is lite.
            response = requests.get("http://1.1.1.1", timeout = 5)
            print("You are connected to the internet.")
        except:
            print(f"It appears you are not connected to the internet.")
            sys.exit()

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