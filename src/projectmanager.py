import os
import toml

class ProjectManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # Set base directory dynamically
        self.project_dir = os.path.join(self.base_dir, 'projects', project_name)
        self.exports_dir = self.get_exports_dir()
        self.imports_dir = self.get_imports_dir()
        self.configs_dir = self.get_configs_dir()
        self.scripts_dir = self.get_scripts_dir()

    def get_exports_dir(self):
        return os.path.join(self.project_dir, 'exports')

    def get_exports_file_path(self, filename):
        # Return the full path to the export file
        return os.path.join(self.exports_dir, filename)

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
        return os.path.join(self.configs_dir, filename)
    
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

    def get_projects_dir(self):
        return os.path.join(self.base_dir, 'projects')

    def get_project_dir(self):
        return os.path.join(self.get_projects_dir(), self.project_name)

    @classmethod
    def identify_default_project(cls):
        """
        Class method that reads default_project.toml to identify the default project.
        """
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        projects_dir = os.path.join(base_dir, 'projects')
        default_toml_path = os.path.join(projects_dir, 'default_project.toml')

        if not os.path.exists(default_toml_path):
            raise FileNotFoundError(f"Missing default_project.toml in {projects_dir}")

        with open(default_toml_path, 'r') as f:
            config = toml.load(f)

        try:
            return config['default project']['project']
        except KeyError as e:
            raise KeyError(f"Missing key in default_project.toml: {e}")

if __name__ ==  "__main__":
    # Usage
    # Dynamically identify the default project from TOML
    project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    project_manager.create_exports_dir()
    print(f"Active project: {project_manager.get_project_dir()}")

