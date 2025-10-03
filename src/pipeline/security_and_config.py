# pipeline/security.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import getpass
import json
import keyring
from pathlib import Path
import re
from typing import Dict, Set, List
import typer

from pipeline.environment import is_termux, is_interactive_terminal, tkinter_is_available, web_browser_is_available

# Define a standard configuration path for your package
CONFIG_PATH = Path.home() / ".pipeline-eds" / "config.json" ## configuration-example
def configure_keyring():
    """
    Configures the keyring backend to use the file-based keyring.
    This is useful for environments where the default keyring is not available,
    such as Termux on Android.
    """
    if is_termux():
        #typer.echo("Termux environment detected. Configuring file-based keyring backend.")
        import keyrings.alt.file
        keyring.set_keyring(keyrings.alt.file.PlaintextKeyring())
        #typer.echo("Keyring configured to use file-based backend.")
    else:
        pass
def init_security():
    if is_termux():
        configure_keyring() # to be run on import

def _prompt_for_value(prompt_message: str, hide_input: bool) -> str:
    """Handles prompting with a fallback from CLI to GUI."""
    # Block these off for testing the browser_get_input, which is not expeceted in this iteration but is good practice for future proofing a hypothetical console-less GUI 
    if is_interactive_terminal():
        # 1. CLI Mode (Interactive)
        typer.echo(f"\n --- Use CLI input --- ")
        if hide_input:
            new_value = getpass.getpass(f"{prompt_message}: ")
        else:
            new_value = input(f"{prompt_message}: ")
        return new_value
        
    elif tkinter_is_available():
        # 2. GUI Mode (Non-interactive fallback)
        from pipeline.guiconfig import gui_get_input
        typer.echo(f"\n --- Non-interactive process detected. Opening GUI prompt. --- ")
        value = gui_get_input(prompt_message, hide_input)
        
        if value is not None:
            return value

    elif web_browser_is_available(): # 3. Check for browser availability
        # 3. Browser Mode (Web Browser as a fallback)
        from pipeline.webconfig import WebConfigurationManager, browser_get_input
        typer.echo(f"\n --- TKinter nor console is not available to handle the configuration prompt. Opening browser-based configuration prompt --- ")
        with WebConfigurationManager():
            # We use the prompt message as the identifier key for the web service
            # because the true config_key is not available in this function's signature.
            value = browser_get_input(
                key=prompt_message, 
                prompt_message=prompt_message,
                hide_input=hide_input # <-- Passes input visibility to web config
            )

        if value is not None:
            return value

    # If all other options fail
    raise CredentialsNotFoundError(
        f"Configuration for '{prompt_message}' is missing and "
        f"neither an interactive terminal, GUI display, nor a web browser is available. "
        f"Please use a configuration utility or provide the value programmatically."
    )

def _get_config_with_prompt(config_key: str, prompt_message: str, overwrite: bool = False) -> str:
    """
    Retrieves a config value from a local file, prompting the user and saving it if missing.
    
    Args:
        config_key: The key in the config file.
        prompt_message: The message to display if prompting is needed.
        overwrite: If True, the function will always prompt for a new value,
                   even if one already exists.
    """
    config = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

    # Get the value from the config file, which will be None if not found
    value = config.get(config_key)
    
    # Check if a value exists and if the user wants to be sure about overwriting
    if value is not None and overwrite:
        typer.echo(f"\nValue for '{prompt_message}' is already set:")
        typer.echo(f"  '{value}'")
        if not typer.confirm("Do you want to overwrite it?", default=False):
            typer.echo("-> Keeping existing value.")
            return value

    # If the value is None (not found), or if a confirmation to overwrite was given,
    # prompt for a new value.
    
    if value is None or overwrite:
        typer.echo(f"\n --- One-time configuration required --- ")

        new_value = _prompt_for_value(
            prompt_message=prompt_message, 
            hide_input=False
        )

        #new_value = input(f"{prompt_message}: ")
        
        # Save the new value back to the file
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        config[config_key] = new_value
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
        typer.echo("Configuration stored.")
        return new_value
    
    # If a value existed and overwrite was False, simply return the existing value.
    return value


def _get_credential_with_prompt(service_name: str, item_name: str, prompt_message: str, hide_password: bool = True, overwrite: bool = False) -> str:
    """
    Retrieves a secret from the keyring, prompting the user and saving it if missing.
    
    Args:
        service_name: The keyring service name.
        item_name: The credential key.
        prompt_message: The message to display if prompting is needed.
        hide_password: True if the input should be hidden (getpass), False otherwise (input).
        overwrite: If True, the function will always prompt for a new credential,
                   even if one already exists.
    """

    credential = keyring.get_password(service_name, item_name)
    
    # Check if a credential exists and if the user wants to be sure about overwriting
    if credential is not None and overwrite:
        typer.echo(f"\nCredential for '{prompt_message}' already exists:")
        if hide_password:
            typer.echo(f"  '***'")
        else:
            typer.echo(f"  '{credential}'")
        
        if not typer.confirm("Do you want to overwrite it?", default=False):
            typer.echo("-> Keeping existing credential.")
            return credential

    # If the credential is None (not found), or if a confirmation to overwrite was given,
    # prompt for a new value.
    if credential is None or overwrite:
        #if hide_password:
        #    new_credential = getpass.getpass(f"{prompt_message}: ")
        #else:
        #    new_credential = input(f"{prompt_message}: ")

        new_credential = _prompt_for_value(
            prompt_message=prompt_message, 
            hide_input=hide_password
        )
            
        # Store the new credential
        if new_credential == "''" or new_credential == '""':
            new_credential = str("") # ensure empty string if user types '' or "" 
        keyring.set_password(service_name, item_name, new_credential) ## configuration-example
        typer.echo("Credential stored securely.")
        return new_credential
    
    # If a credential existed and overwrite was False, simply return the existing value.
    return credential
    
def get_configurable_idcs_list(plant_name: str, overwrite: bool = False) -> List[str]:
    """
    Retrieves a list of default IDCS points for a specific plant from configuration. 
    If not configured, it prompts the user to enter them and saves them.
    
    The function handles IDCS values separated by one or more spaces or commas.
    """
    service_name = f"{plant_name}-default-idcs"
    
    prompt_message = (
        f"Enter default IDCS values for the {plant_name} plant"
        f"(e.g., M100FI FI8001 M310LI)"
    )
    
    idcs_value = _get_config_with_prompt(service_name, prompt_message, overwrite=overwrite)
    
    if not idcs_value:
        return []
    
    # Use re.split to split by multiple delimiters: 
    # r'[,\s]+' means one or more commas (,) OR one or more whitespace characters (\s).
    raw_idcs_list = re.split(r'[,\s]+', idcs_value)
    
    # Filter out any empty strings resulting from the split (e.g., if input was "IDCS1,,IDCS2")
    # and strip leading/trailing whitespace from each element.
    idcs_list = [
        item.strip() 
        for item in raw_idcs_list 
        if item.strip()
    ]
    
    return idcs_list
    
def get_eds_db_credentials(plant_name: str, overwrite: bool = False) -> Dict[str, str]: # generalized for stiles and maxson
    """Retrieves all credentials and config for Stiles EDS Fallback DB, prompting if necessary."""
    service_name = f"pipeline-eds-db-{plant_name}"

    # 1. Get non-secret configuration from the local file
    port = _get_config_with_prompt("eds_db_port", "Enter EDS DB Port (e.g., 3306)")
    storage_path = _get_config_with_prompt("eds_db_storage_path", "Enter EDS database SQL storage path on your system (e.g., 'E:/SQLData/stiles')")
    database = _get_config_with_prompt("eds_db_database", "Enter EDS database name on your system (e.g., stiles)")

    # 2. Get secrets from the keyring
    username = _get_credential_with_prompt(service_name, "username", "Enter your EDS system username (e.g. root)", hide_password=False, overwrite=overwrite)
    password = _get_credential_with_prompt(service_name, "password", "Enter your EDS system password (e.g. Ovation1)", hide_password=True, overwrite=overwrite)

    return {
        'username': username,
        'password': password,
        'host': "localhost",
        'port': port,
        'database': database, # This could also be a config value if it changes
        'storage_path' : storage_path

    }


def get_configurable_plant_name(overwrite=False) -> str:
    '''Comma separated list of plant names to be used as the default if none is provided in other commands.'''
    plant_name = _get_config_with_prompt(f"configurable_plantname_eds_api", f"Enter plant name(s) to be used as the default", overwrite=overwrite)
    if ',' in plant_name:
        plant_names = plant_name.split(',')
        return plant_names
    else:
        return plant_name

def get_eds_api_credentials(plant_name: str, overwrite: bool = False) -> Dict[str, str]:
    """Retrieves API credentials for a given plant, prompting if necessary."""
    service_name = f"pipeline-eds-api-{plant_name}"
    
    #url = _get_config_with_prompt(f"{plant_name}_eds_api_url", f"Enter {plant_name} API URL (e.g., http://000.00.0.000:43084/api/v1)", overwrite=overwrite)
    url = _get_eds_url_config_with_prompt(f"{plant_name}_eds_api_url", f"Enter {plant_name} API URL (e.g., http://000.00.0.000:43084/api/v1, or just 000.00.0.000)", overwrite=overwrite)
    username = _get_credential_with_prompt(service_name, "username", f"Enter your API username for {plant_name} (e.g. admin)", hide_password=False, overwrite=overwrite)
    password = _get_credential_with_prompt(service_name, "password", f"Enter your API password for {plant_name} (e.g. '')", overwrite=overwrite)
    idcs_to_iess_suffix = _get_config_with_prompt(f"{plant_name}_eds_api_iess_suffix", f"Enter iess suffix for {plant_name} (e.g., .UNIT0@NET0)", overwrite=overwrite)
    zd = _get_config_with_prompt(f"{plant_name}_eds_api_zd", f"Enter {plant_name} ZD (e.g., 'Maxson' or 'WWTF')", overwrite=overwrite)
    
    #if not all([username, password]):
    #    raise CredentialsNotFoundError(f"API credentials for '{plant_name}' not found. Please run the setup utility.")
        
    return {
        'url': url,
        'username': username,
        'password': password,
        'zd': zd,
        'idcs_to_iess_suffix': idcs_to_iess_suffix

        # The URL and other non-secret config would come from a separate config file
        # or be prompted just-in-time as we discussed previously.
    }

def get_external_api_credentials(party_name: str, overwrite: bool = False) -> Dict[str, str]:
    """Retrieves API credentials for a given plant, prompting if necessary."""
    service_name = f"pipeline-external-api-{party_name}"
    
    url = _get_config_with_prompt(service_name, f"Enter {party_name} API URL (e.g., http://api.example.com)", overwrite=overwrite)
    client_id = _get_credential_with_prompt(service_name, "client_id", f"Enter the client_id for the {party_name} API",hide_password=False, overwrite=overwrite)
    password = _get_credential_with_prompt(service_name, "password", f"Enter the password for the {party_name} API", overwrite=overwrite)

    
    #if not all([client_id, password]):
    #    raise CredentialsNotFoundError(f"API credentials for '{party_name}' not found. Please run the setup utility.")
        
    return {
        'url': url,
        'client_id': client_id,
        'password': password
    }


def get_all_configured_urls(only_eds: bool) -> Set[str]:
    """
    Reads the config file and returns a set of all URLs found.
    If only_eds is True, it returns only the EDS-related URLs.
    """
    config = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

    urls = set()
    for key, value in config.items():
        if isinstance(value, str):
            # A simple check to see if the string looks like a URL
            if value.startswith(("http://", "https://")):
                if only_eds and "eds" in key.lower():
                    urls.add(value)
                elif not only_eds:
                    urls.add(value)
    return urls


def _is_likely_ip(url: str) -> bool:
    """Simple heuristic to check if a string looks like an IP address."""
    parts = url.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not (0 <= int(part) <= 255):
            return False
    return True

def _get_eds_url_config_with_prompt(config_key: str, prompt_message: str, overwrite: bool = False) -> str:
    url = _get_config_with_prompt(config_key, prompt_message, overwrite=overwrite)
    if _is_likely_ip(url):
        url = f"http://{url}:43084/api/v1" # assume EDS patterna and port http and append api/v1 if user just put in an IP
    return url

class CredentialsNotFoundError(Exception):
    """Custom exception for missing credentials."""
    pass

# Example usage in your main pipeline
def frontload_build_all_credentials():
    """
    Sets up all possible API and database credentials for the pipeline.
    
    This function is intended for "super users" who have cloned the repository.
    It will attempt to retrieve and, if necessary, prompt for all known
    credentials and configuration values in a single execution.
    
    This is an alternative to the just-in-time setup, which prompts for
    credentials only as they are needed.
    
    Note: This will prompt for credentials for all supported plants and external
    APIs in sequence.
    """
    
    try:
        maxson_api_creds = get_eds_api_credentials(plant_name = "Maxson")
        stiles_api_creds = get_eds_api_credentials(plant_name = "Stiles")
        stiles_db_creds = get_eds_db_credentials(plant_name = "Stiles")
        rjn_api_creds = get_external_api_credentials("RJN")
        
        # Now use the credentials normally in your application logic
        # ... your code to connect to services ...
        
    except CredentialsNotFoundError as e:
        print(f"Error: {e}")
        # Optionally, guide the user to the next step
        print("Tip: Run `your_package_name.configure()` or the corresponding CLI command.")


if __name__ == "__main__":
    frontload_build_all_credentials()
    