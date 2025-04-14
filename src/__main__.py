#from libs.Api import PyEds2
import src.get_rjn_auth_token
from env import Env 
if __name__ == "__main__":
    src.get_rjn_auth_token.call_curl_script(username =  Env.get_username(),password =  Env.get_password())