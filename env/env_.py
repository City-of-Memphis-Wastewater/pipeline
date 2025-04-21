#env.__main__.py
#import src.helpers.load_json # good idea, to load from json file at startup, but juice isnt worth the squeeze right now

class Env:
    rjn_base_url = "https://rjn-clarity-api.com/v1/clarity"
    rjn_username = "OuREElQ2"
    rjn_password = "0.k2h6i19utie0.nzom0vbg020."

    def __init__(self):
        self.nope = "Nope"
        self.instance = None

    @classmethod
    def get_username(cls):
        return cls.rjn_username
    
    @classmethod
    def get_password(cls):
        return cls.rjn_password
    
    @classmethod
    def get_base_url(cls):
        # careful - connection with Address from address (which should be project agnostic)
        return cls.rjn_base_url
    
    def set_header():
        pass
    def get_header():
        pass

    def set_token():
        pass
    def get_token():
        pass

    def get_token(ip_address):
        ip_address
        api_url = f'http://{point_object.ip_address}:43084/api/v1/'
        api_url = f'http://{ip_address}:43084/api/v1/'
        api_url = Address.get_rest_api_url(ip_address = None) # if none, use known, if else, us Address.get_current_ip_address()
        f'http://{ip_address}:43084/api/v1/'
        request_url = api_url + 'login'
        data = {'username' : 'admin', 'password' : '', 'type' : 'rest client'}
        #data = {'username' : 'rjn', 'password' : 'RjnClarity2025', 'type' : 'rest client'}  
        response = requests.post(request_url, json = data)
        #print(f"response={response}")
        token = json.loads(response.text)
        headers = {'Authorization' : 'Bearer {}'.format(token['sessionId'])}
        return api_url,headers
    