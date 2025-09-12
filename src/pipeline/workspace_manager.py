import os
import toml
import logging
from pathlib import Path
import sys
import mulch
import sys
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
    APP_NAME = "pipeline"

    TIMESTAMPS_JSON_FILE_NAME = 'timestamps_success.json'

    # Detect if running in a dev repo vs installed package
    if getattr(sys, "frozen", False):
        # Running from a pipx/executable environment
        ROOT_DIR = None
    else:
        # Running from a cloned repo
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

    
    @classmethod
    def get_workspaces_dir(cls):
        """
        Return workspaces directory depending on environment:
        - If ROOT_DIR is defined (repo clone), use that
        - Else use AppData/local platform-specific location
        """
        if cls.ROOT_DIR and (cls.ROOT_DIR / cls.WORKSPACES_DIR_NAME).exists():
            workspaces_dir = cls.ROOT_DIR / cls.WORKSPACES_DIR_NAME
        else:
            workspaces_dir = cls.get_appdata_dir() / cls.WORKSPACES_DIR_NAME
            workspaces_dir.mkdir(parents=True, exist_ok=True)
            default_file = workspaces_dir / cls.DEFAULT_WORKSPACE_TOML_FILE_NAME
            if not default_file.exists():
                # auto-populate default TOML with most recent workspace
                recent_ws = cls.most_recent_workspace_name() or "default"
                default_file.write_text(f"[default-workspace]\nworkspace = '{recent_ws}'\n")
        return workspaces_dir
    
    @classmethod
    def most_recent_workspace_name(cls):
        workspaces_dir = cls.get_workspaces_dir()
        all_dirs = [p for p in workspaces_dir.iterdir() if p.is_dir() and not p.name.startswith('.')]
        if not all_dirs:
            return None
        latest = max(all_dirs, key=lambda p: p.stat().st_mtime)
        return latest.name

    def get_workspace_dir(self):
        # workspace_name is established at instantiation. You want a new name? Initialize a new WorkspaceManager(). It manages one workpspace.
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

        workspaces_dir = cls.ROOT_DIR / cls.WORKSPACES_DIR_NAME
        workspace_name = cls.identify_default_workspace_name()
        if workspace_name is None:
            workspace_name = cls.most_recent_workspace_name() # if 
        if workspace_name is None:
            mulch.workspace(target_dir = workspaces_dir, scaffold = workspaces_dir / '.mulch' / 'mulch.toml', workspace_name = 'eds') # allow date based default if no workspace_name is provided
            workspace_name = 'eds'    
        workspace_path = workspaces_dir / workspace_name
        if not workspace_path.exists():
            #raise FileNotFoundError(f"Workspace directory not found: {default_workspace_path}")
            print("No default_workspace.toml file to identify a default workspace folder, so the most recently edited folder will be used.")
            
        return workspace_path
    
    '''
    @classmethod
    def identify_default_workspace_name(cls, workspaces_dir = None):
        if workspaces_dir is None:
            workspaces_dir = cls.get_workspaces_dir()
        default_file = workspaces_dir / cls.DEFAULT_WORKSPACE_TOML_FILE_NAME
        if not default_file.exists():
            default_file.write_text("# Default workspace\n")
        return str(default_file)
    '''
    
    @classmethod
    def identify_default_workspace_name(cls, workspaces_dir = None):
        """
        Class method that reads default-workspace.toml to identify the default-workspace.
        """
        if workspaces_dir is None:
            workspaces_dir = cls.get_workspaces_dir()
        logging.info(f"workspaces_dir = {workspaces_dir}\n")
        default_toml_path = workspaces_dir / cls.DEFAULT_WORKSPACE_TOML_FILE_NAME

        if not default_toml_path.exists():
            return None
            #raise FileNotFoundError(f"Missing {cls.DEFAULT_WORKSPACE_TOML_FILE_NAME} in {workspaces_dir}")

        with open(default_toml_path, 'r') as f:
            data = toml.load(f)
            logging.debug(f"data = {data}") 
        try:
            return data['default-workspace']['workspace'] # This dictates the proper formatting of the TOML file.
        except KeyError as e:
            recent_ws = cls.most_recent_workspace_name() or "default"
            default_toml_path.write_text(f"[default-workspace]\nworkspace = '{recent_ws}'\n")
            #raise KeyError(f"Missing key in {cls.DEFAULT_WORKSPACE_TOML_FILE_NAME}: {e}")
            return recent_ws
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
    
    @classmethod
    def get_appdata_dir(cls) -> Path:
        """Return platform-appropriate appdata folder."""
        if os.name == "nt":  # Windows
            base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif os.name == "posix" and "ANDROID_ROOT" in os.environ:  # Termux
            base = Path.home() / ".local" / "share"
        else:  # macOS/Linux
            base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return base / cls.APP_NAME

    @classmethod
    def ensure_appdata_workspaces_dir(cls) -> Path:
        """Create workspace folder and default toml if missing."""
        workspaces_dir = cls.get_appdata_dir() / cls.WORKSPACES_DIR_NAME
        workspaces_dir.mkdir(parents=True, exist_ok=True)
        cls.workspaces_dir = workspaces_dir 
        default_file = workspaces_dir / cls.DEFAULT_WORKSPACE_TOML_FILE_NAME
        if not default_file.exists():
            pass
            #default_file.write_text("# Default workspace config\n")
        mulch_scaffold = []
        mulch.seed(target_dir = workspaces_dir,scaffold_dict = mulch_scaffold, skip_if_exists=True)
        workspace_path = workspaces_dir / "eds"
        mulch.workspace(base_path = workspaces_dir.parent, scaffold_filepath = workspaces_dir / '.mulch' / 'mulch.toml', workspace_path = workspace_path) # allow date based default if no workspace_name is provided
        return workspaces_dir
    
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

    