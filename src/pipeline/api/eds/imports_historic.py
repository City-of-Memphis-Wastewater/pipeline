

    
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
from datetime import datetime
import logging
import requests
from requests.exceptions import Timeout
import time
from pprint import pprint
from pathlib import Path
import os
import re
import inspect
import subprocess
import platform
from functools import lru_cache
import typer # for CLI
from pyhabitat import on_windows

from pipeline.env import SecretConfig
from pipeline.workspace_manager import WorkspaceManager
from pipeline import helpers
from pipeline.decorators import log_function_call
from pipeline.time_manager import TimeManager
from pipeline.security_and_config import SecurityAndConfig, get_base_url_config_with_prompt
from pipeline.variable_clarity import Redundancy
from pipeline.api.eds.exceptions import EdsLoginException, EdsTimeoutError, EdsAuthError
 
#_get_credential_with_prompt, 
# 
#_get_config_with_prompt, 
#get_configurable_idcs_list, 
#get_temporary_input
