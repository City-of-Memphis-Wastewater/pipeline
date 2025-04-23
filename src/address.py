"""
Title: addresss.py
Created: 17 April 2025
Author: George Clayton Bennett

Purpose: Consolidate and modularize API address URLs, much like the Pavlovian Directories class
"""
import sys
print(sys.executable)

class Address:

    def __init__(self,host = str(), port_colon = ":", rest_api_port = int(), soap_api_port = int(), protocol = "https://", rest_api_path = str(), auth_path = str(), username = str(), password = str()):

        self.host = host
        self.port_colon = port_colon
        self.rest_api_port = str(rest_api_port)
        self.soap_api_port = str(soap_api_port)
        self.protocol = protocol 
        self.rest_api_path = rest_api_path
        self.auth_path = auth_path

        self.query = str() # initialize to no query
        
        self.set_rest_api_base_url(protocol = self.protocol,
                                                            host = self.host,
                                                            port_colon = self.port_colon,
                                                            rest_api_port = self.rest_api_port,
                                                            rest_api_path = self.rest_api_path)
        self.set_auth_url(rest_api_base_url=self.rest_api_base_url,auth_path = self.auth_path)


    def set_rest_api_base_url(self,protocol,host,port_colon,rest_api_port,rest_api_path):
        self.rest_api_base_url = str(protocol+host+port_colon+rest_api_port+rest_api_path)

    def set_auth_url(self,rest_api_base_url,auth_path):
        self.auth_url = str(rest_api_base_url+auth_path)

    def get_auth_token(self):
        if (self.auth_url is None) or (self.auth_url is str()):
            print("auth_url is not set.")
        else:
            return "future"

    def set_query(self,query):
        self.query = query

    """
    protocol = "http://" # scheme
    ip_address = str()
    host = str()
    base_url = str()
    rest_api_port = int()
    soap_api_port = int()
    rest_api_url = str()
    soap_api_url = str()
    filepath_config_toml = "./configs/*.toml"
    
    @classmethod
    def get_config_toml(cls):
        return cls.filepath_config_toml

    @classmethod
    def get_ip_address(cls):
        if cls.ip_address is str() or cls.ip_address is None:
            cls.set_ip_address(cls.ip_address_default)
        else:
            return cls.ip_address
    @classmethod
    def set_ip_address(cls,ip_address):
        cls.ip_address = ip_address
        
    @classmethod
    def get_base_url(cls):
        if cls.base_url is str():
            cls.set_base_url()
        return cls.base_url
    @classmethod
    def set_base_url(cls):  
        cls.base_url = 'http://'+str(cls.get_ip_address()) # must cast possible None as string to force calculation    
    
    @classmethod
    def get_rest_api_url(cls):
        if cls.rest_api_url is str():
            cls.set_rest_api_url()
        return cls.rest_api_url
    
    @classmethod
    def set_rest_api_url(cls,ip_address=None):
        # this allows for an IP address (like from Maxson or Stiles) to be inserted without first calling set_ip_address. 
        if ip_address is not None:
            cls.set_ip_address(ip_address=ip_address)
            cls.set_base_url()
        else:
            pass
        # Either way
        cls.rest_api_url = str(cls.get_base_url())+':43084/api/v1/'
        return cls.rest_api_url
    
    @classmethod
    def get_rest_api_url_list(cls):
        # force single list, later allow for multiple IP addresses to be registered (for both Stiles and Maxson)
        if False:
            rest_api_url_list = [cls.get_rest_api_url()]
        else:
            rest_api_url_list = ["http://172.19.4.127:43084/api/v1/",
                             "http://172.19.4.128:43084/api/v1/"]
        return rest_api_url_list
    
    
    @classmethod
    def set_soap_api_url(cls):
        cls.soap_api_url = cls.get_base_url()+":43080/eds.wsdl"
    @classmethod
    def get_soap_api_url(cls):
        if cls.soap_api_url is str():
            cls.set_soap_api_url()
        return cls.soap_api_url
    @classmethod
    def calculate(cls):
        #Config.get_default_ip_address()    
        cls.get_ip_address()
        """
    
    # """ class AddressRjn(Address):
    # " RJN offered us access to their REST API "
    # filepath_config_toml = ".\configs\config_rjn.toml"

    # @classmethod
    # def get_config_toml(cls):
    #     return cls.filepath_config_toml

    # if True:
    #     " Explicitly override irrelevant inherited methods to prevent use. "
    #     @classmethod
    #     def get_soap_api(cls):
    #         raise NotImplementedError("RJN did not offer us a SOAP API")
    #     @classmethod
    #     def set_soap_api(cls):  
    #         raise NotImplementedError("RJN did not offer us a SOAP API")

    # class AddressEds(Address):
    # # allow for multiple EDS servers
    # rest_api_port = 43084
    # soap_api_port = 43080
    # ip_address_default = "172.19.4.127" # Maxson
    # ip_address_list = ["172.19.4.127",
    #                          "172.19.4.128"]
    # filepath_config_toml = ".\configs\config_eds.toml"
    # rest_api_url_list = ["http://172.19.4.127:43084/api/v1/",
    #                          "http://172.19.4.128:43084/api/v1/"]
    # ''' """

def generate_relevant_api_addresses():
    maxson = Address(host = "172.19.4.127", port_colon = ":", rest_api_port = 43084, soap_api_port = 43080, protocol = "http://", rest_api_path = "/api/v1/", auth_path = "login/", username = "admin", password = "")
    stiles = Address(host = "172.19.4.128", port_colon = ":", rest_api_port = 43084, soap_api_port = 43080, protocol = "http://", rest_api_path = "/api/v1/", auth_path = "login/", username = "admin", password = "")
    rjn = Address(host = "rjn-clarity-api.com", port_colon = "", rest_api_port = None, soap_api_port = None, protocol = "https://", rest_api_path = "/v1/clarity/", auth_path = "auth/", username = "OuREElQ2", password = "0.k2h6i19utie0.nzom0vbg020.")
    return maxson, stiles, rjn

if __name__ == "__main__":
    maxson = Address(host = "172.19.4.127", port_colon = ":", rest_api_port = 43084, soap_api_port = 43080, protocol = "http://", rest_api_path = "/api/v1/", auth_path = "login/", username = "admin", password = "")
    stiles = Address(host = "172.19.4.128", port_colon = ":", rest_api_port = 43084, soap_api_port = 43080, protocol = "http://", rest_api_path = "/api/v1/", auth_path = "login/", username = "admin", password = "")
    rjn = Address(host = "rjn-clarity-api.com", port_colon = "", rest_api_port = None, soap_api_port = None, protocol = "https://", rest_api_path = "/v1/clarity/", auth_path = "auth/", username = "OuREElQ2", password = "0.k2h6i19utie0.nzom0vbg020.")
    maxson, stiles, rjn = generate_relevant_api_addresses()
    maxson.get_auth_token()
    stiles.get_auth_token()
    rjn.get_auth_token()    
