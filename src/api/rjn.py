from src.calls import make_request
class RjnClient:
    def __init__(self,config):
        self.config = config

    def get_token(self):
        
        request_url = self.config['url'] + 'auth'
        data = {
            'client_id': self.config['client_id'],
            'password': self.config['password']
        }

        response = make_request(request_url, data)
        token = response.json().get("token")

        ['sessionId']
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"  
        }
        return token, headers