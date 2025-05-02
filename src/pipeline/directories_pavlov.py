"""
Title: directories.py
Author: Clayton Bennett
Created: 29 January 2025
Project: Pavlov3D

Purpose: 
Keep directory assignment organized, particularly for using project folders.
Migrate away from directory amangement in environmental.py

Example:
from pipeline.directories import Directories

"""
import os
import inspect
from src import toml_utils
from pathlib import Path
from src import environmental

class Directories:
    root = None
    project = None
    configs = None
    exports = None
    imports = None
    groupings = None
    env = None

    #setters
    @classmethod
    def set_root_dir(cls,path):
        cls.root = path
    @classmethod
    def set_project_dir(cls,path):
        # if a legitimate full path is not provided, assume that the project directory is within the root\projects\ directory
        if os.path.isdir(path):
            cls.project = path
        else:
            relative_path =  cls.get_root_dir()+"\\projects\\"+path
            if os.path.isdir(relative_path):
                cls.project = relative_path
        print(f"Project directory set: {cls.project}")

    # getters
    @classmethod
    def get_root_dir(cls):
        #return cls.root
        return cls.root
    @classmethod
    def get_program_dir(cls):
        return cls.get_root_dir()
    @classmethod
    def get_project_dir(cls):
        return cls.project
    @classmethod
    def get_config_dir(cls):
        return cls.get_project_dir()+"\\configs\\"
    @classmethod
    def get_export_dir(cls):
        return cls.get_project_dir()+"\\exports\\"
    @classmethod
    def get_import_dir(cls):
        return cls.get_project_dir()+"\\imports\\"
    @classmethod
    def get_groupings_dir(cls):
        return cls.get_config_dir()+"\\groupings\\"
    @classmethod
    def get_intermediate_group_structure_export_dir(cls):
        return cls.get_groupings_dir()+"\\intermediate_group_structure_export\\"
    @classmethod
    def initilize_program_dir(cls): # called in CLI. Should also be called at other entry points.
        cls.set_root_dir(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
        print(f"cls.initial_program_dir = {cls.get_root_dir()}")
        #cls.initialize_startup_project()
    @classmethod
    def initialize_startup_project(cls):
        filename_default_project_entry = "./src/projects/default-project.toml"
        loaded_entry = toml_utils.load_toml(filename_default_project_entry)
        cls.set_project_dir(cls.get_root_dir()+"\\projects\\"+loaded_entry["project_directory"])
    @staticmethod
    def check_file(filepath):
        if not(os.path.isfile(filepath)):
            print(f"The file does not exist: {filepath}")
            raise SystemExit
        else:
            return True
        