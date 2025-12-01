# src/pipeline/api/eds/rest/config.py
from __future__ import annotations
from typing import Dict

from pipeline.security_and_config import SecurityAndConfig, get_base_url_config_with_prompt, not_enough_info


def get_rest_api_url(base_url: str | None = None,
                        eds_rest_api_port: int | None = 43080, 
                        eds_rest_api_sub_path: str = 'api/v1', 
                        ) -> str | None:
    """
    This is the recipe for forming the URL with that 
    makes REST API data requests to the EDS server.
    """
    if base_url is None:
        return None
    if base_url and str(eds_rest_api_port) and eds_rest_api_sub_path:
        eds_rest_api_url = base_url + ":" + str(eds_rest_api_port) + "/" + eds_rest_api_sub_path

    return eds_rest_api_url

def get_eds_rest_api_credentials(plant_name: str, overwrite: bool = False, forget: bool = False) -> Dict[str, str]:
    """Retrieves API credentials for a given plant, prompting if necessary."""

    #from pipeline.api.eds.rest.client import EdsRestClient

    service_name = f"pipeline-eds-api-{plant_name}"
    overwrite = False
    eds_base_url = get_base_url_config_with_prompt(service_name = f"{plant_name}_eds_base_url", prompt_message = f"Enter {plant_name} EDS base url (e.g., http://000.00.0.000, or just 000.00.0.000)")
    eds_rest_api_port = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_rest_api_port", prompt_message = f"Enter {plant_name} EDS REST API port (e.g., 43084)", overwrite=overwrite)
    eds_rest_api_sub_path = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_rest_api_sub_path", prompt_message = f"Enter {plant_name} EDS REST API sub path (e.g., 'api/v1')", overwrite=overwrite)
    username = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "username", prompt_message = f"Enter your EDS API username for {plant_name} (e.g. admin)", hide=False, overwrite=overwrite)
    password = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "password", prompt_message = f"Enter your EDS API password for {plant_name} (e.g. '')", overwrite=overwrite)
    idcs_to_iess_suffix = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_api_iess_suffix", prompt_message = f"Enter iess suffix for {plant_name} (e.g., .UNIT0@NET0)", overwrite=overwrite)
    zd = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_api_zd", prompt_message = f"Enter {plant_name} ZD (e.g., 'Maxson' or 'WWTF')", overwrite=overwrite)
    
    #if not all([username, password]):
    #    raise CredentialsNotFoundError(f"API credentials for '{plant_name}' not found. Please run the setup utility.")
    eds_rest_api_sub_path = str(eds_rest_api_sub_path).rstrip("/").lstrip("/").replace(r"\\","/").lower()

    # EDS REST API Pattern: url = f"http://{url}:43084/api/v1" # assume EDS patterna and port http and append api/v1 if user just puts in an IP
    
    from pipeline.api.eds.rest.config import get_rest_api_url
    eds_rest_api_url = get_rest_api_url(eds_base_url, 
                                        str(eds_rest_api_port),
                                        eds_rest_api_sub_path
                                        ) 
    
    if eds_rest_api_url is None:
        not_enough_info()

    return {
        'url': eds_rest_api_url,
        'username': username,
        'password': password,
        'zd': zd,
        'idcs_to_iess_suffix': idcs_to_iess_suffix

        # The URL and other non-secret config would come from a separate config file
        # or be prompted just-in-time as we discussed previously.
    }