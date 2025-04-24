import os

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

if __name__ ==  "__main__":
    # Usage
    project_name = 'your_project'  # Replace with actual project name
    project_manager = ProjectManager(project_name)
    project_manager.create_exports_dir()

    # Get export file path
    filename = 'export_file.txt'  # Replace with the desired filename
    export_file_path = project_manager.get_exports_file_path(filename)
    print(f"Export file will be saved to: {export_file_path}")