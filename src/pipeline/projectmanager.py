import os
import toml
from pathlib import Path

class ProjectManager:
    def __init__(self, project_name):
        self.project_name = project_name
        #self.base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # Set base directory dynamically
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.project_dir = os.path.join(self.base_dir, 'projects', project_name)
        self.exports_dir = self.get_exports_dir()
        self.imports_dir = self.get_imports_dir()
        self.configs_dir = self.get_configs_dir()
        self.scripts_dir = self.get_scripts_dir()
        self.aggregate_dir = self.get_aggregate_dir()

    def get_exports_dir(self):
        return os.path.join(self.project_dir, 'exports')

    def get_exports_file_path(self, filename):
        # Return the full path to the export file
        return os.path.join(self.exports_dir, filename)

    def get_aggregate_dir(self):
        return os.path.join(self.exports_dir, 'aggregate')
    
    def create_exports_dir(self):
        if not os.path.exists(self.exports_dir):
            os.makedirs(self.exports_dir)

    def get_imports_dir(self):
        return os.path.join(self.project_dir, 'imports')

    def get_imports_file_path(self, filename):
        # Return the full path to the export file
        return os.path.join(self.imports_dir, filename)

    def create_imports_dir(self):
        if not os.path.exists(self.imports_dir):
            os.makedirs(self.imports_dir)

    def get_configs_dir(self):
        return os.path.join(self.project_dir, 'configs')

    def get_configs_file_path(self, filename):
        # Return the full path to the config file
        file_path = os.path.join(self.configs_dir, filename)
        #config_file_path = os.path.join(project_root, "projects", "eds_to_rjn", "configs", "secrets.yaml")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file '{filename}' not found in directory '{self.configs_dir}'.")
        return file_path
    
    def create_configs_dir(self):
        if not os.path.exists(self.configs_dir):
            os.makedirs(self.configs_dir)

    def get_scripts_dir(self):
        return os.path.join(self.project_dir, 'scripts')

    def get_scripts_file_path(self, filename):
        # Return the full path to the config file
        return os.path.join(self.scripts_dir, filename)
    
    def create_scripts_dir(self):
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir)
    
    def get_queries_dir(self):
        return os.path.join(self.get_project_dir(), 'queries')
    
    def get_queries_file_path(self,filename='points.csv'):
        # Return the full path to the config file
        return os.path.join(self.get_queries_dir(), filename)

    def get_projects_dir(self):
        return os.path.join(self.base_dir, 'projects')

    def get_project_dir(self):
        return os.path.join(self.get_projects_dir(), self.project_name)

    @classmethod
    def defunct_identify_default_project(cls):
        """
        Class method that reads default-project.toml to identify the default-project.
        """
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        projects_dir = os.path.join(base_dir, 'projects')
        default_toml_path = os.path.join(projects_dir, 'default-project.toml')

        if not os.path.exists(default_toml_path):
            raise FileNotFoundError(f"Missing default-project.toml in {projects_dir}")

        with open(default_toml_path, 'r') as f:
            config = toml.load(f)
        try:
            return config['default-project']['project']
        except KeyError as e:
            raise KeyError(f"Missing key in default-project.toml: {e}")
            
    @staticmethod
    def identify_default_project():
        # This climbs out of /src/pipeline/ to find the real root
        root_dir = Path(__file__).resolve().parents[2]  # -> <repo-root>
        projects_dir = root_dir / "projects"
        default_file = projects_dir / "default-project.toml"
        
        if not default_file.exists():
            raise FileNotFoundError(f"Missing default-project.toml in {projects_dir}")
        
        import toml
        data = toml.load(default_file)
        return data["default-project"]["project"]
        
        
def establish_default_project():
    project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    return project_manager.get_project_dir()

def demo_projectmanager_og():
    # Dynamically identify the default-project from TOML
    project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    project_manager.get_project_dir()
    project_manager.create_exports_dir()

def demo_projectmanager():
    print(f"establish_default_project() = {establish_default_project()}")

if __name__ ==  "__main__":
    # Usage
    
    print(f"Default, active project: {demo_projectmanager()}")

    