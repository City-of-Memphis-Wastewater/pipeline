#env.__main__.py
#import src.helpers.load_json # good idea, to load from json file at startup, but juice isnt worth the squeeze right now
from src.address import Address 
class Env:
    token = str()
    header = str()
    username = str()
    password = str()
    
    def __init__(self):
        self.nope = "Nope"
        self.instance = None

    @classmethod
    def get_username(cls):
        return cls.username
    
    @classmethod
    def get_password(cls):
        return cls.password
    
    @classmethod
    def set_header(cls,header):
        cls.header = header

    @classmethod
    def get_header(cls):
        return cls.header
    
    def set_token(cls,token):
        cls.token = token

    def get_token(cls):
        return cls.token
    
class EnvRjn(Env):

    # migrate out to .gitignored'd config for security
    base_url = "https://rjn-clarity-api.com/v1/clarity"
    username = "OuREElQ2"
    password = "0.k2h6i19utie0.nzom0vbg020."
    header = str()

    
class EnvEds(Env):
    

    def get_token(ip_address):
        ip_address
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
    