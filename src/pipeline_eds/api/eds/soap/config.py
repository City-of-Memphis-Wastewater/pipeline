# src/pipeline_eds/api/eds/soap/config.py
from __future__ import annotations
from typing import Dict
import logging

from pipeline_eds.security_and_config import SecurityAndConfig, get_base_url_config_with_prompt, not_enough_info
from pipeline_eds.variable_clarity import Redundancy

def get_eds_soap_api_credentials(plant_name: str, overwrite: bool = False, forget: bool = False) -> Dict[str, str]:
    """Retrieves API credentials for a given plant, prompting if necessary."""
  

    service_name = f"pipeline-eds-api-{plant_name}"
    overwrite = False
    eds_base_url = get_base_url_config_with_prompt(service_name = f"{plant_name}_eds_base_url", prompt_message = f"Enter {plant_name} EDS base url (e.g., http://000.00.0.000, or just 000.00.0.000)")
    eds_soap_api_port = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_soap_api_port", prompt_message = f"Enter {plant_name} EDS SOAP API port (e.g., 43080)", overwrite=overwrite)
    eds_soap_api_sub_path = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_soap_api_sub_path", prompt_message = f"Enter {plant_name} EDS SOAP API WSDL path (e.g., 'eds.wsdl')", overwrite=overwrite)
    username = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "username", prompt_message = f"Enter your EDS API username for {plant_name} (e.g. admin)", hide=False, overwrite=overwrite)
    password = SecurityAndConfig.get_credential_with_prompt(service_name = service_name, item_name = "password", prompt_message = f"Enter your EDS API password for {plant_name} (e.g. '')", overwrite=overwrite)
    idcs_to_iess_suffix = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_api_iess_suffix", prompt_message = f"Enter iess suffix for {plant_name} (e.g., .UNIT0@NET0)", overwrite=overwrite)
    zd = SecurityAndConfig.get_config_with_prompt(config_key = f"{plant_name}_eds_api_zd", prompt_message = f"Enter {plant_name} ZD (e.g., 'Maxson' or 'WWTF')", overwrite=overwrite)
    
    #if not all([username, password]):
    #    raise CredentialsNotFoundError(f"API credentials for '{plant_name}' not found. Please run the setup utility.")
    eds_soap_api_port = int(eds_soap_api_port)
    eds_soap_api_sub_path = eds_soap_api_sub_path

    # Comparable SOAP API function, for documentation:
    eds_soap_api_url = get_eds_soap_api_url(base_url = eds_base_url,
                                                    eds_soap_api_port = str(eds_soap_api_port),
                                                    eds_soap_api_sub_path = eds_soap_api_sub_path)
    if eds_soap_api_url is None:
        not_enough_info()
    
    return {
        'url': eds_soap_api_url,
        'username': username,
        'password': password,
        'zd': zd,
        'idcs_to_iess_suffix': idcs_to_iess_suffix

        # The URL and other non-secret config would come from a separate config file
        # or be prompted just-in-time as we discussed previously.
    }
    
#@Redundancy.set_on_return_hint(recipient=None,attribute_name="eds_soap_api_url")
def get_eds_soap_api_url(base_url: str | None = None,
                eds_soap_api_port: int | None = 43080, 
                eds_soap_api_sub_path: str | None = 'eds.wsdl', 
                ) -> str | None:
    """
    This is the recipe for forming the URL that 
    makes SOAP API data requests to the EDS server.
    
    WSDL (Web Service Description Language) is an XML-based language used
      to describe the functionality of a SOAP-based web service. 
      It acts as a contract between the service provider and the consumer, 
      detailing the operations available, the input/output parameters, 
      and the communication protocols.

    source: https://www.soapui.org/docs/soap-and-wsdl/working-with-wsdls/

    """
    if base_url is None:
        return None
    
    if base_url and str(eds_soap_api_port) and eds_soap_api_sub_path:
        soap_api_url = base_url + ":" + str(eds_soap_api_port) + "/" + eds_soap_api_sub_path
    else:
        logging.info("get_eds_soap_api_url() returns None due to incomplete information.")
        return None
     
    return soap_api_url
