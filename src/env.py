#env.__main__.py
 
import os
import requests
import yaml

class SecretsYaml:
    def __init__(self, config):
        self.config = config

    @staticmethod
    def load_config(secrets_file_path="secrets.yaml"):
        with open(secrets_file_path, 'r') as f:
            return yaml.safe_load(f)
        
    def print_config(self):
        # Print the values
        for section, values in self.config.items():
            print(f"[{section}]")
            for key, val in values.items():
                print(f"{key} = {val}")



def demo1_yaml():
    config = SecretsYaml.load_config()
    secrets = SecretsYaml(config)
    
    def print_secrets():    
        secrets.print_config()
    
    def get_and_print_token_eds():
        token, headers = secrets.get_token_eds(plant_zd = "Maxson")
        print(f"Token: {token}")
        print(f"Headers: {headers}")

    def get_and_print_token_rjn():
        token, headers = secrets.get_token_rjn()
        print(f"Token: {token}")
        print(f"Headers: {headers}")
    
    print_secrets()
    get_and_print_token_eds()
    get_and_print_token_rjn()

    return secrets

if __name__ == "__main__":
    # call from the root directory using poetry run python -m src.env

    secrets=demo1_yaml()
