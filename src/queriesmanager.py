import os
import toml

class QueriesManager:
    project_manager = None
    def __init__(self, project_manager:object):
        self.project_manager = project_manager
        self.queries_file_path = str()

def identify_default_queries(self):
        """
        Method that reads default-query.toml, after the project has been established.
        """
        if not self.project_manager:
             raise ValueError("self.project_manager must be provided and not None.")
        
        default_query_path = os.path.join(self.project_manager.get_queries_dir(), 'default-query.toml')

        if not os.path.exists(default_query_path):
            raise FileNotFoundError(f"Missing default-query.toml in {self.project_manager.get_queries_dir()}")

        with open(default_query_path, 'r') as f:
            query = toml.load(f)
        return default_query_path
        try:
            return config['default-project']['project']
        except KeyError as e:
            raise KeyError(f"Missing key in default-project.toml: {e}")

        
def establish_default_queries():
    from src.projectmanager import ProjectManager
    project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    queries_file_path = identify_default_queries(project_manager)
    return project_manager.get_project_dir()


def demo_queriesmanager():
    print(f"establish_default_project() = {establish_default_queries()}")

if __name__ ==  "__main__":
    # Usage
    
    print(f"Default, active project: {demo_queriesmanager()}")

    