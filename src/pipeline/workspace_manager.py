import os
import toml
import logging
from pathlib import Path

'''
Goal:
Implement default-workspace.toml variable: use-most-recently-edited-workspace-directory 
'''

# Configure logging (adjust level as needed)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class WorkspaceManager:
    # It has been chosen to not make the WorkspaceManager a singleton if there is to be batch processing.

    WORKSPACES_DIR_NAME = 'workspaces'
    QUERIES_DIR_NAME = 'queries'
    IMPORTS_DIR_NAME = 'imports'
    EXPORTS_DIR_NAME = 'exports'
    SCRIPTS_DIR_NAME = 'scripts'
    CONFIGURATIONS_DIR_NAME = 'configurations'
    SECRETS_DIR_NAME ='secrets'
    LOGS_DIR_NAME = 'logs'
    CONFIGURATION_FILE_NAME = 'configuration.toml'
    SECRETS_YAML_FILE_NAME ='secrets.yaml'
    SECRETS_EXAMPLE_YAML_FILE_NAME ='secrets-example.yaml'
    DEFAULT_WORKSPACE_TOML_FILE_NAME = 'default-workspace.toml'
    TIMESTAMPS_JSON_FILE_NAME = 'timestamps_success.json'
    ROOT_DIR = Path(__file__).resolve().parents[2]  # root directory
    
    
    # This climbs out of /src/pipeline/ to find the root.
    # parents[0] → The directory that contains the (this) Python file.
    # parents[1] → The parent of that directory.
    # parents[2] → The grandparent directory (which should be the root), if root_pipeline\src\pipeline\
    # This organization anticipates PyPi packaging.

    
    def __init__(self, workspace_name):
        self.workspace_name = workspace_name
        self.workspaces_dir = self.get_workspaces_dir()
        self.workspace_dir = self.get_workspace_dir()
        self.configurations_dir = self.get_configurations_dir()
        self.exports_dir = self.get_exports_dir()
        self.imports_dir = self.get_imports_dir()
        self.queries_dir = self.get_queries_dir()
        self.secrets_dir = self.get_secrets_dir()
        self.scripts_dir = self.get_scripts_dir()
        self.logs_dir = self.get_logs_dir()
        self.aggregate_dir = self.get_aggregate_dir()

        
        self.check_and_create_dirs(list_dirs = 
                                    [self.workspace_dir, 
                                    self.exports_dir, 
                                    self.imports_dir, 
                                    self.secrets_dir, 
                                    self.scripts_dir, 
                                    self.logs_dir,
                                    self.aggregate_dir])

    def get_workspaces_dir(self):
        return self.ROOT_DIR / self.WORKSPACES_DIR_NAME

    def get_workspace_dir(self):
        return self.get_workspaces_dir() / self.workspace_name

    def get_exports_dir(self):
        return self.workspace_dir / self.EXPORTS_DIR_NAME
    
    def get_exports_file_path(self, filename):
        # Return the full path to the export file
        return self.exports_dir / filename

    def get_aggregate_dir(self):
        # This is for five-minute aggregation data to be stored between hourly bulk passes
        # This should become defunct once the tabular trend data request is functional 
        return self.exports_dir / 'aggregate'
    
    def get_configurations_dir(self):
        return self.workspace_dir / self.CONFIGURATIONS_DIR_NAME
    
    def get_configuration_file_path(self):
        # Return the full path to the config file or create it from the fallback copy if it exists
        file_path = self.get_configurations_dir() / self.CONFIGURATION_FILE_NAME
        return file_path
    
    def get_logs_dir(self):
        return self.workspace_dir / self.LOGS_DIR_NAME

    def get_imports_dir(self):
        return self.workspace_dir / self.IMPORTS_DIR_NAME

    def get_imports_file_path(self, filename):
        # Return the full path to the export file
        return self.imports_dir / filename
        
    def get_secrets_dir(self):
        return self.workspace_dir / self.SECRETS_DIR_NAME

    def get_secrets_file_path(self):
        # Return the full path to the config file
        file_path = self.secrets_dir / self.SECRETS_YAML_FILE_NAME
        if not file_path.exists():
            logging.warning(f"Secrets sonfiguration file {self.SECRETS_YAML_FILE_NAME} not found in:\n{self.secrets_dir}.\nHint: Copy and edit the {self.SECRETS_YAML_FILE_NAME}.")
            print("\n")
            choice = str(input(f"Auto-copy {self.SECRETS_EXAMPLE_YAML_FILE_NAME} [Y] or sys.exit() [n] ? "))
            if choice.lower().startswith("y"):
                file_path = self.get_secrets_file_path_or_copy()
            else:
                # edge case, expected once per machine, or less, if the user knows to set up a secrets.yaml file.
                import sys 
                sys.exit()
        return file_path
    
    def get_secrets_file_path_or_copy(self):
        # Return the full path to the config file or create it from the fallback copy if it exists
        file_path = self.secrets_dir / self.SECRETS_YAML_FILE_NAME
        fallback_file_path = self.secrets_dir / self.SECRETS_EXAMPLE_YAML_FILE_NAME
        if not file_path.exists() and fallback_file_path.exists():
            import shutil
            shutil.copy(fallback_file_path, file_path)
            print(f"{self.SECRETS_YAML_FILE_NAME} not found, copied from {self.SECRETS_YAML_FILE_NAME}")
        elif not file_path.exists() and not fallback_file_path.exists():
            raise FileNotFoundError(f"Configuration file {self.SECRETS_YAML_FILE_NAME} nor {self.SECRETS_EXAMPLE_YAML_FILE_NAME} not found in directory '{self.secrets_dir}'.")
        return file_path

    def get_scripts_dir(self):
        return self.workspace_dir / self.SCRIPTS_DIR_NAME

    def get_scripts_file_path(self, filename):
        # Return the full path to the config file
        return self.get_scripts_dir() / filename
    
    def get_queries_dir(self):
        return self.workspace_dir / self.QUERIES_DIR_NAME
    
    def get_queries_file_path(self,filename): #
        # Return the full path to the config file
        filepath = self.get_queries_dir() / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Query filepath={filepath} not found. \nPossible reason: You are in the wrong project directory.")
        return filepath    
    
    def get_timestamp_success_file_path(self):
        # Return the full path to the timestamp file
        filepath = self.get_queries_dir() / self.TIMESTAMPS_JSON_FILE_NAME
        logging.info(f"WorkspaceManager.get_timestamp_success_file_path() = {filepath}")
        return filepath

    def check_and_create_dirs(self, list_dirs):
        for dir_path in list_dirs:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_cwd(cls) -> Path:
        """Return current workspace directory, not the source code root, as a Path instance."""
        # Quick and dirty, not representative of the complex truth or opportunity.
        #cls.ROOT_DIR / 'workspaces' / cls.identify_default_workspace_name()
        
        # Pre-Exisiting function, generated some time before July 24, 2025. May as well use that instead. It is good to use your own library. Benefit from having built it.
        return cls.identify_default_workspace_name()

    @classmethod
    def get_all_workspaces_names(cls):
        """
        Return a list of all workspace names found in the workspaces directory.
        """
        workspaces_dir = cls.ROOT_DIR / cls.WORKSPACES_DIR_NAME
        if not workspaces_dir.exists():
            raise FileNotFoundError(f"Workspaces directory not found at: {workspaces_dir}")
        
        workspace_dirs = [
            p.name for p in workspaces_dir.iterdir()
            if p.is_dir() and not p.name.startswith('.')  # skip hidden/system folders
        ]
        return workspace_dirs

    @classmethod
    def identify_default_workspace_path(cls):
        """
        Class method that reads default-workspace.toml to identify the default-workspace path.
        """
        workspace_name = cls.identify_default_workspace_name()
        workspaces_dir = cls.ROOT_DIR / cls.WORKSPACES_DIR_NAME
        default_workspace_path = workspaces_dir / workspace_name
        if not default_workspace_path.exists():
            raise FileNotFoundError(f"Default workspace directory not found: {default_workspace_path}")
        return default_workspace_path
    @classmethod
    def identify_default_workspace_name(cls):
        """
        Class method that reads default-workspace.toml to identify the default-workspace.
        """
         
        workspaces_dir = cls.ROOT_DIR / cls.WORKSPACES_DIR_NAME
        logging.info(f"workspaces_dir = {workspaces_dir}\n")
        default_toml_path = workspaces_dir / cls.DEFAULT_WORKSPACE_TOML_FILE_NAME

        if not default_toml_path.exists():
            raise FileNotFoundError(f"Missing {cls.DEFAULT_WORKSPACE_TOML_FILE_NAME} in {workspaces_dir}")

        with open(default_toml_path, 'r') as f:
            data = toml.load(f)
            logging.debug(f"data = {data}") 
        try:
            return data['default-workspace']['workspace'] # This dictates the proper formatting of the TOML file.
        except KeyError as e:
            raise KeyError(f"Missing key in {cls.DEFAULT_WORKSPACE_TOML_FILE_NAME}: {e}")
        
    def get_default_query_file_paths_list(self):
        
        default_query_path = self.get_queries_dir()/ 'default-queries.toml'
        
        with open(default_query_path, 'r') as f:
            query_config = toml.load(f)
        filenames = query_config['default-query']['files']
        if not isinstance(filenames, list):
            raise ValueError("Expected a list under ['default-query']['files'] in default-queries.toml")
        paths = [self.get_queries_file_path(fname) for fname in filenames]

        for path in paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Query file not found: {path}")
        return paths

    @property
    def name(self):
        return self.workspace_name
    
def establish_default_workspace():
    workspace_name = WorkspaceManager.identify_default_workspace_name()
    logging.info(f"workspace_name = {workspace_name}")
    workspace_manager = WorkspaceManager(workspace_name)
    logging.info(f"WorkspaceManager.get_workspace_dir() = {WorkspaceManager.get_workspace_dir()}")
    return 

def demo_establish_default_workspace():
    establish_default_workspace()

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "default"

    if cmd == "demo-default":
        demo_establish_default_workspace()
    else:
        print("Usage options: \n" 
        "poetry run python -m pipeline.api.eds demo-default \n")  

    