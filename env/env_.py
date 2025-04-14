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
        return cls.rjn_base_url
    