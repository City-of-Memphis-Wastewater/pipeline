#env.__main__.py
 
import yaml
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9

'''
migrate this to ConfigurationManager
'''

class SecretConfig:
    def __init__(self, config):
        self.config = config

    @staticmethod
    def load_config(secrets_file_path): 
        with open(secrets_file_path, 'r') as f:
            return yaml.safe_load(f)
        
    def print_config(self):
        # Print the values
        for section, values in self.config.items():
            print(f"[{section}]")
            for key, val in values.items():
                print(f"{key} = {val}")


def find_urls(config, url_set=None):
    '''determine all values with the key "url" in a config file.'''
    if url_set is None:
        url_set = set()

    if isinstance(config, dict):
        for key, value in config.items():
            if key == "url":
                url_set.add(value)
            else:
                find_urls(value, url_set)
    elif isinstance(config, list):
        for item in config:
            find_urls(item, url_set)

    return url_set

def demo_secrets():
    """
    The defaut SecretConfig.load_config() call 
    should load fromthe default-workspace 
    as defined by the configuration file in the workspaces directorys,
    caed defaut_workspace.toml - Clayton Bennett 26 April 2025.
    However this call can also be made if another project is made the active project.
    """
    from pipeline.workspace_manager import WorkspaceManager 

    workspace_name = WorkspaceManager.identify_default_workspace_name()
    workspace_manager = WorkspaceManager(workspace_name)
    config = SecretConfig.load_config(secrets_file_path = workspace_manager.get_secrets_file_path())
    secrets = SecretConfig(config)
    return secrets

if __name__ == "__main__":
    # call from the root directory using: poetry run python -m pipeline.env
    secrets=demo_secrets()
    secrets.print_config()
