from __future__ import annotations

from pipeline.security_and_config import SecurityAndConfig
from pipeline.security_and_config import get_base_url_config_with_prompt


def get_configurable_default_plant_name(overwrite=False) -> str :
    '''Comma separated list of plant names to be used as the default if none is provided in other commands.'''
    plant_name = SecurityAndConfig.get_config_with_prompt(config_key = f"configurable_plantname_eds_api", prompt_message = f"Enter plant name(s) to be used as the default", overwrite=overwrite)
    if plant_name is not None and ',' in plant_name:
        plant_names = plant_name.split(',')
        return plant_names
    else:
        return plant_name

def get_service_name(plant_name: str|None = None) -> str | None:
    """
    Describe the standardized string describing the service name that will be known to the configuration file.
    """
    if plant_name is None:
        plant_name = get_configurable_default_plant_name()
    if plant_name is None:
        return None
    service_name = f"pipeline-eds-api-{plant_name}" 
    return service_name

def get_eds_base_url(plant_name: str|None = None, overwrite: bool = False) -> str | None:
    """
    Retrieves the EDS base URL for the given plant name from configuration.
    """
    if plant_name is None:
        plant_name = get_configurable_default_plant_name()
    if plant_name is None:
        return None
    eds_base_url = get_base_url_config_with_prompt(service_name = f"{plant_name}_eds_base_url", prompt_message = f"Enter {plant_name} EDS base url (e.g., http://000.00.0.000, or just 000.00.0.000)")
    return eds_base_url

def get_idcs_to_iess_suffix(plant_name: str|None = None, overwrite: bool = False) -> str | None:
    """
    Retrieves the iess suffix for the given plant name from configuration.
    Prompts the user if not found and overwrite is True.
    """
    if plant_name is None:
        plant_name = get_configurable_default_plant_name()
    if plant_name is None:
        return None
    idcs_to_iess_suffix = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_api_iess_suffix", prompt_message = f"Enter iess suffix for {plant_name} (e.g., .UNIT0@NET0)", overwrite=overwrite)
    return idcs_to_iess_suffix

def get_zd(plant_name: str|None = None, overwrite: bool = False) -> str | None:
    """
    Retrieves the iess suffix for the given plant name from configuration.
    Prompts the user if not found and overwrite is True.
    """
    if plant_name is None:
        plant_name = get_configurable_default_plant_name()
    if plant_name is None:
        return None
    zd = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_api_zd", prompt_message = f"Enter {plant_name} ZD (e.g., 'Maxson' or 'WWTF')", overwrite=overwrite)
    return zd