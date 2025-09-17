# pipeline/security.py
import keyring
import getpass
import json
from pathlib import Path
from typing import Dict
import typer

# Define a standard configuration path for your package
CONFIG_PATH = Path.home() / ".pipeline-eds" / "config.json"

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
        new_value = input(f"{prompt_message}: ")
        
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
        if hide_password:
            new_credential = getpass.getpass(f"{prompt_message}: ")
        else:
            new_credential = input(f"{prompt_message}: ")
            
        # Store the new credential
        keyring.set_password(service_name, item_name, new_credential)
        typer.echo("Credential stored securely.")
        return new_credential
    
    # If a credential existed and overwrite was False, simply return the existing value.
    return credential

# Note: The other helper function, _get_config_with_prompt, should also
# be updated with an overwrite parameter for consistency.


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
    
def get_eds_api_credentials(plant_name: str, overwrite: bool = False) -> Dict[str, str]:
    """Retrieves API credentials for a given plant, prompting if necessary."""
    service_name = f"pipeline-eds-api-{plant_name}"
    
    url = _get_config_with_prompt(f"{plant_name}_eds_api_url", f"Enter {plant_name} API URL (e.g., http://000.00.0.000:43084/api/v1)", overwrite=overwrite)
    zd = _get_config_with_prompt(f"{plant_name}_eds_api_zd", f"Enter {plant_name} ZD (e.g., 'Maxson' or 'WWTF')", overwrite=overwrite)
    username = _get_credential_with_prompt(service_name, "username", f"Enter your API username for {plant_name} (e.g. admin)", hide_password=False, overwrite=overwrite)
    password = _get_credential_with_prompt(service_name, "password", f"Enter your API password for {plant_name} (e.g. '')", overwrite=overwrite)

    #if not all([username, password]):
    #    raise CredentialsNotFoundError(f"API credentials for '{plant_name}' not found. Please run the setup utility.")
        
    return {
        'url': url,
        'zd': zd,
        'username': username,
        'password': password
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
    