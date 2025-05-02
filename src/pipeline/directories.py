#env.directories.py
'''
Title: directories.py
Author: Clayton Bennett
Created: 11 April 2025
'''
from pathlib import Path

class Directories:
    # Dynamically locate the project root based on the current file location
    
    project = None
    src = None
    env = None
    token_auth_file = None
    user_credentials_file = None
    def __init__(self):
        self.nope = True
    
    @classmethod
    def initialize(cls):
        dir(cls)
        cls.set_project_dir()
        cls.set_env_dir()
        cls.set_src_dir()
        cls.set_tokenauth_file()
        cls.set_env_file()
    @classmethod
    def set_project_dir(cls,path_str=None):
        if path_str is None:
            cls.directories_file = Path(__file__).resolve()
            cls.project = cls.directories_file.parents[1]  # Move up two levels from the current file
        if path_str is not None and Path(path_str).is_dir() :
            cls.project = path_str
            
    @classmethod
    def set_env_dir(cls,path_str=None):
        if path_str is None:
            cls.env = cls.get_project_dir()+"\\env"
        if path_str is not None and Path(path_str).is_dir() :
            cls.env = path_str
    @classmethod
    def set_src_dir(cls,path_str=None):
        if path_str is None:
            cls.src = cls.get_project_dir()+"\\src"
        if path_str is not None and Path(path_str).is_dir() :
            cls.src = path_str
    @classmethod
    def set_gui_dir(cls,path_str=None):
        if path_str is None:
            cls.gui = cls.get_project_dir()+"\\gui"
        if path_str is not None and Path(path_str).is_dir() :
            cls.gui = path_str
    @classmethod
    def set_shell_dir(cls,path_str=None):
        if path_str is None:
            cls.shell = cls.get_project_dir()+"\\shell"
        if path_str is not None and Path(path_str).is_dir() :
            cls.shell = path_str
    @classmethod
    def set_tui_dir(cls,path_str=None):
        if path_str is None:
            cls.tui = cls.get_project_dir()+"\\tui"
        if path_str is not None and Path(path_str).is_dir() :
            cls.tui = path_str
    @classmethod
    def set_api_dir(cls,path_str=None):
        if path_str is None:
            cls.api = cls.get_project_dir()+"\\api"
        if path_str is not None and Path(path_str).is_dir() :
            cls.api = path_str
    #@classmethod
    #def set_token_auth_file(cls):
    #@classmethod
    #def set_user_credentials_file(cls):
    
    @classmethod
    def get_project_dir(cls):
    @classmethod
    def get_env_dir(cls):
    @classmethod
    def get_src_dir(cls):
    #@classmethod
    #def get_token_auth_file(cls):
    #@classmethod
    #def get_user_credentials_file(cls):
