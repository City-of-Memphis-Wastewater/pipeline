import os
import toml

class QueriesManager:
    def __init__(self, project_manager: object):
        if not project_manager:
            raise ValueError("project_manager must be provided and not None.")
        self.project_manager = project_manager

    def get_query_file_paths(self, filename=None):
        """
        Returns a list of query CSV file paths:
        - If `filename` is provided, use only that one. Expected source: argparse cli
        - Else, try to read default-query.toml for a list.
        - Else, fallback to ['points.csv']
        """
        if filename:
            paths = [self.project_manager.get_queries_file_path(filename)]
        else:
            try:
                default_query_path = os.path.join(
                    self.project_manager.get_queries_dir(), 'default-query.toml'
                )
                with open(default_query_path, 'r') as f:
                    query_config = toml.load(f)
                filenames = query_config['default-query']['files']
                if not isinstance(filenames, list):
                    raise ValueError("Expected a list under 'files' in default-query.toml")
                paths = [self.project_manager.get_queries_file_path(fname) for fname in filenames]
            except Exception as e:
                print(f"Warning: {e}. Falling back to ['points.csv']")
                paths = [self.project_manager.get_queries_file_path('points.csv')]

        for path in paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Query file not found: {path}")
        return paths
    
def cli_queriesmanager():
    import argparse
    from src.projectmanager import ProjectManager
    from src.queriesmanager import QueriesManager
    parser = argparse.ArgumentParser(description="Select CSV file for querying.")
    parser.add_argument(
        '--csv-file',
        type=str,
        default=None,
        help="Specify the CSV file to use for querying (default is points.csv)"
    )
    args = parser.parse_args()

    # Set up project manager
    project_name = ProjectManager.identify_default_project()
    project_manager = ProjectManager(project_name)
    queries_manager = QueriesManager(project_manager)

    try:
        # Get the query file path (either default or user-provided)
        query_file_path = queries_manager.get_query_file_paths(args.csv_file)
        print(f"Using query file: {query_file_path}")
        # Further processing with the query file...
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ ==  "__main__":
    cli_queriesmanager()



