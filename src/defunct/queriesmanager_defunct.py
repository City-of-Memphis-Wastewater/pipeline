import os
import toml

class QueriesManager:
    project_manager = None
    def __init__(self, project_manager:object):
        self.project_manager = project_manager
        

    def identify_default_query_filepath(self):
        """
        Method that reads default-queries.toml, after the project has been established.
        """
        if not self.project_manager:
            raise ValueError("self.project_manager must be provided and not None.")
        
        default_query_path = os.path.join(self.project_manager.get_queries_dir(), 'default-queries.toml')

        if not os.path.exists(default_query_path):
            raise FileNotFoundError(f"Missing default-queries.toml in {self.project_manager.get_queries_dir()}")

        with open(default_query_path, 'r') as f:
            query = toml.load(f)
        try:
            query_file = query['default-query']['file']
        except KeyError as e:
            raise KeyError(f"Missing key in default-queries.toml: {e}")
        
        query_file_path = self.project_manager.get_queries_file_path(query_file)
        return query_file_path
        
    def get_query_file_path(self, filename=None):
        """
        Determine the full path to the query CSV file.
        If `filename` is provided, it is used directly.
        If not, the file listed in default-queries.toml is used.
        """
        """ 
        Argparse usage in CLI, with example filename :
        poetry run python -m src.queriesmanager --csv-file points-copy.csv
        """
        if filename is None:
            # No file specified (by argparse using CLI), check the default-queries.toml file for CSV slection
            query_file_path = self.identify_default_query_filepath()
            filename_display = os.path.basename(query_file_path)
        else:
            ## No file specified, use default (points.csv)
            ## filename = 'points.csv'    
            # Check if the file exists in the queries directory
            query_file_path = self.project_manager.get_queries_file_path(filename)
            filename_display = filename

        
        if not os.path.exists(query_file_path):
            raise FileNotFoundError(f"Query file '{filename_display}' not found in {self.project_manager.get_queries_dir()}")
        
        return query_file_path

def demo_queriesmanager():
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
        query_file_path = queries_manager.get_query_file_path(args.csv_file)
        print(f"Using query file: {query_file_path}")
        # Further processing with the query file...
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ ==  "__main__":
    demo_queriesmanager()




