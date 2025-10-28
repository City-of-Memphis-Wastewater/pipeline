# pipeline/security.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import json
from pathlib import Path
import re
import keyring
from typing import Dict, Set, List
import typer
import click.exceptions
import logging
import sys
from pyhabitat import on_termux, on_ish_alpine, interactive_terminal_is_available, tkinter_is_available, web_browser_is_available
import pyhabitat as ph

# Define a standard configuration path for your package
CONFIG_PATH = Path.home() / ".pipeline-eds" / "config.json" ## configuration-example
CONFIG_FILE = Path.home() / ".pipeline-eds" / "secure_config.json"
KEY_FILE = Path.home() / ".pipeline-eds" / ".key"

def init_security():
    if on_termux() or on_ish_alpine():
        try: # mid refactor, try the new function first
            configure_filebased_secure_config() # to be run on import
        except:
            configure_keyring()
    else:
        pass

def configure_keyring():
    """
    Configures the keyring backend to use the file-based keyring.
    This is useful for environments where the default keyring is not available,
    such as Termux on Android.
    Defunct, use configure_filebased_secure_config() instead.
    """
    if on_termux or on_ish_alpine():
        #typer.echo("Termux environment detected. Configuring file-based keyring backend.")
        import keyrings.alt.file
        keyring.set_keyring(keyrings.alt.file.PlaintextKeyring())
        #typer.echo("Keyring configured to use file-based backend.")
    else:
        pass


def configure_filebased_secure_config():
    """
    Configures the keyring backend to use the file-based keyring.
    This is useful for environments where the default keyring is not available,
    such as Termux on Android or iSH on iPhone.
    """
    if on_termux() or on_ish_alpine():
        #typer.echo("Termux environment detected. Configuring file-based keyring backend.")
        from cryptography.fernet import Fernet
        cryptography.fernet-1 # error on purpose
        
        # MORE CODE NEEDED

        #keyring.set_keyring(keyrings.alt.file.PlaintextKeyring())
        #typer.echo("Keyring configured to use file-based backend.")
    else:
        pass


def _prompt_for_value(prompt_message: str, hide_input: bool) -> str:
    """Handles prompting with a fallback from CLI to GUI.
    ### **Platform Quirk: Input Cancellation ({Ctrl}+C)**
    Due to the underlying POSIX terminal handling on Linux and Termux,
    using {Ctrl}+C to cancel an input prompt will require the user
    to press {Enter} (or {Return}) immediately afterward to fully 
    submit the interrupt and abort the operation. 
    This behavior, the Enter key being necessary to finalize the interruption,
     is expected for POSIX systems, when using either the 
    `typer`/`click` framework, Python's built in input() function, or any alternative.
    This extra step is necessary due to the standard input terminal behavior
    in "cooked mode.".
    On  Windows, however, just {Ctrl}+C is expected to successfully perform a keyboard interrupt..
    """
    # Block these off for testing the browser_get_input, which is not expeceted in this iteration but is good practice for future proofing a hypothetical console-less GUI 
    
    value = None # ensure safe defeault so that the except block handles properly, namely if the user cancels the typer.prompt() input with control+ c
    
    if tkinter_is_available():
        # 2. GUI Mode (Non-interactive fallback)
        from pipeline.guiconfig import gui_get_input
        typer.echo(f"\n --- Non-interactive process detected. Opening GUI prompt. --- ")
        value = gui_get_input(prompt_message, hide_input)
        
        if value is not None:
            return value
    
    elif interactive_terminal_is_available():
        try:
            # 1. CLI Mode (Interactive)
            typer.echo(f"\n --- Use CLI input --- ")
            if hide_input:
                try:
                    from rich.prompt import Prompt
                    def secure_prompt(msg: str) -> str:
                        return Prompt.ask(msg, password=True)
                except ImportError:
                    def secure_prompt(msg: str) -> str:
                        return typer.prompt(msg, hide_input=True)
                value = secure_prompt(prompt_message)
            else:
                value = typer.prompt(prompt_message, hide_input=False)

        except KeyboardInterrupt:
            typer.echo("\nInput cancelled by user.")
            return None
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
        f"Configuration for '{prompt_message}' is missing or cancelled. "
        f"The program would cancel itself if neither an interactive terminal, nor a GUI display, nor a web browser is available. "
        f"Please use a configuration utility or provide the value programmatically."
    )

def get_temporary_input(prompt_message: str | None) -> str|None :
    """
    Seek a temporary user input value, not to be stored.
    Input options include console, pop-up window, or web browser input field, depending on what is available.
    """ 
    typer.echo(f"\n --- One-time temporary value required --- ")
    typer.echo("You may cancel the input to avoid entering a value.")

    try:
        new_value = _prompt_for_value(
            prompt_message=prompt_message,
            hide_input=False
        )
    except (KeyboardInterrupt, EOFError):
        typer.echo("\n⚠️  Configuration prompt cancelled.")
        return None
    except Exception as e:
        typer.echo(f"\n⚠️  Unexpected error during prompt: {e}")
        return None
    if new_value is None:
        typer.echo("⚠️  No input provided. Returning None.")
        return None
    elif new_value == "":
        if ph.interactive_terminal_is_available() and not typer.confirm("⚠️  An empty string was provided. Are you sure about this?", default=True):
            return None
    # Normalize user input for empty-string passwords
    elif new_value in ("''", '""'):
        new_value = ""
    return new_value

def _get_config_with_prompt(config_key: str, 
                            prompt_message: str, 
                            overwrite: bool = False, 
                            forget: bool = False,
                            ) -> str | None:
    """
    Retrieves a config value from a local file, prompting the user and saving it if missing.
    
    Args:
        config_key: The key in the config file.
        prompt_message: The message to display if prompting is needed.
        overwrite: If True, the function will always prompt for a new value,
                   even if one already exists.
        forget: If True, credentials should not be stored to system keyring, 
                and configs should not be stored to program-wide plaintext stored in AppData. 

    
    Returns:
        The configuration value (str) if successful, or None if the user cancels.
    
    """

    config = {}

     # --- Load existing config file safely ---
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            typer.echo(f"⚠️  Warning: Existing config file '{CONFIG_PATH.name}' is corrupted.")
            if not typer.confirm("Do you want to reset the corrupted file to an empty file?", default=False):
                typer.echo("-> Keeping existing corrupted file. Returning None for the requested value.")
                return None
            typer.echo("-> Resetting config file...")
            config = {}
        except Exception as e:
            typer.echo(f"⚠️  Failed to read config file: {e}")
            return None
        
    # Get the value from the config file, which will be None if not found
    value = config.get(config_key)
    
    # --- Handle existing value and overwrite logic ---
    # Check if a value exists and if the user wants to be sure about overwriting
    if value is not None and overwrite:
        typer.echo(f"\nValue for '{prompt_message}' is already set:")
        typer.echo(f"  '{value}'")
        if not typer.confirm("Do you want to overwrite it?", default=False):
            typer.echo("-> Keeping existing value.")
            return value

    # --- Prompt for new value if needed ---
    # If the value is None (not found), or if a confirmation to overwrite was given,
    # prompt for a new value
    if value is None or overwrite:
        typer.echo(f"\n --- One-time configuration required --- ")
        typer.echo("You may cancel the input to avoid entering a value.")

        try:
            new_value = _prompt_for_value(
                prompt_message=prompt_message,
                hide_input=False
            )
        except (KeyboardInterrupt, EOFError):
            typer.echo("\n⚠️  Configuration prompt cancelled.")
            return None
        except Exception as e:
            typer.echo(f"\n⚠️  Unexpected error during prompt: {e}")
            return None
        if new_value is None:
            typer.echo("⚠️  No input provided. Configuration not saved.")
            return None
        # Normalize user input for empty-string passwords
        elif new_value in ("''", '""'):
            new_value = ""
        elif new_value == "":
            if ph.interactive_terminal_is_available() and not typer.confirm("⚠️  An empty string was provided. Are you sure about this?", default=True):
                return None
        
        # --- Save updated configuration safely ---
        # Save the new value back to the file
        if forget:
            return new_value
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            config[config_key] = new_value
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)
            typer.echo("Configuration stored.")
        except Exception as e:
            typer.echo(f"⚠️  Failed to save configuration: {e}")
            return None
        return new_value
    
    # --- Return existing value if no overwrite requested ---
    return value

def _get_credential_with_prompt(service_name: str, 
                                item_name: str, 
                                prompt_message: str, 
                                hide: bool = False, 
                                overwrite: bool = False,
                                forget: bool = False,
                                ) -> str | None:
    """
    Retrieves a secret from the keyring, prompting the user and saving it if missing.
    
    Args:
        service_name: The keyring service name.
        item_name: The credential key.
        prompt_message: The message to display if prompting is needed.
        hide: True if the input should be hidden (getpass), False otherwise (input).
        overwrite: If True, the function will always prompt for a new credential,
                   even if one already exists.
        forget: If True, credentials should not be sotred to system keyring, 
                and configs should not be stored to program-wide plaintext stored in AppData. 

    Examples:
        OVERWRITE = False
        HIDEPASSWORD = False 

        service_name: service_name = f"pipeline-eds-db-{plant_name}"
        item_name: item_name = "username"
        prompt_message: prompt_message = f"Enter the IP address for your SOAP API (e.g., XXX.XX.X.XXX)" # no colon necessary, managed internally.
        hide_input: hide_input = HIDEPASSWORD 
        overwrite: overwrite = OVERWRITE

    Returns:
        The configuration value (str) if successful, or None if the user cancels.
    
    """

    credential = keyring.get_password(service_name, item_name)
    
    # Check if a credential exists and if the user wants to be sure about overwriting
    if credential is not None and overwrite:
        typer.echo(f"\nCredential for '{prompt_message}' already exists:")
        if hide:
            typer.echo(f"  '***'")
        else:
            typer.echo(f"  '{credential}'")
        
        if not typer.confirm("Do you want to overwrite it?", default=False):
            typer.echo("-> Keeping existing credential.")
            return credential

    # If the credential is None (not found), or if a confirmation to overwrite was given,
    # prompt for a new value.
    if credential is None or overwrite: 
        # -- Assign value of new_credential --
        try:
            print("Trying to prompt for credential ...")
            new_credential = _prompt_for_value(
                prompt_message=prompt_message, 
                hide_input=hide
            )
            print("Success: prompted for credential.")
            print(f"new_credential = {new_credential}")
        except (KeyboardInterrupt, EOFError):
            typer.echo("\n⚠️  Credential prompt cancelled.")
            return None
        except Exception as e:
            typer.echo(f"\n⚠️  Unexpected error during credential prompt: {e}")
            return None

        if new_credential is None:
            typer.echo("⚠️  No input provided. Credential not saved.")
            return None
        elif new_credential == "":
            if ph.interactive_terminal_is_available() and not typer.confirm("⚠️  An empty string was provided. Are you sure about this?", default=True):
                return None
        # Normalize user input for empty-string passwords
        if new_credential in ("''", '""'):
            new_credential = ""
        credential = new_credential
        

        if forget:
            return credential
            
        if not forget:
            # Store the new credential to keyring
            try:
                keyring.set_password(service_name, item_name, new_credential)
            except Exception as e:
                typer.echo(f"⚠️  Failed to store credential: {e}")
                return None

        typer.echo("✅  Credential stored securely.")

    # Return existing credential if no overwrite
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
    
    idcs_value = _get_config_with_prompt(config_key = service_name, prompt_message = prompt_message, overwrite=overwrite)
    
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
    
def get_eds_local_db_credentials(plant_name: str, overwrite: bool = False) -> Dict[str, str]: # generalized for stiles and maxson
    """Retrieves all credentials and config for Stiles EDS Fallback DB, prompting if necessary."""
    service_name = f"pipeline-eds-db-{plant_name}"

    # 1. Get non-secret configuration from the local file
    port = _get_config_with_prompt(config_key = "eds_db_port", prompt_message = "Enter EDS DB Port (e.g., 3306)")
    storage_path = _get_config_with_prompt(config_key = "eds_db_storage_path", prompt_message = "Enter EDS database SQL storage path on your system (e.g., 'E:/SQLData/stiles')")
    database = _get_config_with_prompt(config_key = "eds_db_database", prompt_message = "Enter EDS database name on your system (e.g., stiles)")

    # 2. Get secrets from the keyring
    username = _get_credential_with_prompt(service_name = service_name, item_name = "username", prompt_message = "Enter your EDS system username (e.g. root)", hide=False, overwrite=overwrite)
    password = _get_credential_with_prompt(service_name = service_name, item_name = "password", prompt_message = "Enter your EDS system password (e.g. Ovation1)", hide=True, overwrite=overwrite)

    return {
        'username': username,
        'password': password,
        'host': "localhost",
        'port': port,
        'database': database, # This could also be a config value if it changes
        'storage_path' : storage_path

    }


def get_configurable_default_plant_name(overwrite=False) -> str :
    '''Comma separated list of plant names to be used as the default if none is provided in other commands.'''
    plant_name = _get_config_with_prompt(config_key = f"configurable_plantname_eds_api", prompt_message = f"Enter plant name(s) to be used as the default", overwrite=overwrite)
    if ',' in plant_name:
        plant_names = plant_name.split(',')
        return plant_names
    else:
        return plant_name

def get_eds_rest_api_credentials(plant_name: str, overwrite: bool = False, forget: bool = False) -> Dict[str, str]:
    """Retrieves API credentials for a given plant, prompting if necessary."""

    from pipeline.api.eds import EdsClient

    service_name = f"pipeline-eds-api-{plant_name}"
    overwrite = False
    #url = _get_config_with_prompt(config_key =f"{plant_name}_eds_api_url", prompt_message = f"Enter {plant_name} API URL (e.g., http://000.00.0.000:43084/api/v1)", overwrite=overwrite)
    #url = _get_eds_url_config_with_prompt(config_key = f"{plant_name}_eds_api_url", prompt_message = f"Enter {plant_name} EDS API URL (e.g., http://000.00.0.000:43084/api/v1, or just 000.00.0.000)", overwrite=overwrite)
    eds_base_url = _get_credential_with_prompt(service_name = service_name, item_name = f"{plant_name}_eds_base_url", prompt_message =  f"Enter {plant_name} EDS base url (e.g., http://000.00.0.000, or just 000.00.0.000)", overwrite=overwrite)
    eds_base_url = _get_base_url_config_with_prompt(service_name = f"{plant_name}_eds_base_url", prompt_message = f"Enter {plant_name} EDS base url (e.g., http://000.00.0.000, or just 000.00.0.000)")
    eds_rest_api_port = _get_config_with_prompt(config_key = f"{plant_name}_eds_rest_api_port", prompt_message = f"Enter {plant_name} EDS REST API port (e.g., 43084)", overwrite=overwrite)
    eds_rest_api_sub_path = _get_config_with_prompt(config_key = f"{plant_name}_eds_rest_api_sub_path", prompt_message = f"Enter {plant_name} EDS REST API sub path (e.g., 'api/v1')", overwrite=overwrite)
    eds_soap_api_port = _get_config_with_prompt(config_key = f"{plant_name}_eds_soap_api_port", prompt_message = f"Enter {plant_name} EDS SOAP API port (e.g., 43080)", overwrite=overwrite)
    eds_soap_api_sub_path = _get_config_with_prompt(config_key = f"{plant_name}_eds_soap_api_sub_path", prompt_message = f"Enter {plant_name} EDS SOAP API WSDL path (e.g., 'eds.wsdl')", overwrite=overwrite)
    username = _get_credential_with_prompt(service_name = service_name, item_name = "username", prompt_message = f"Enter your EDS API username for {plant_name} (e.g. admin)", hide=False, overwrite=overwrite)
    password = _get_credential_with_prompt(service_name = service_name, item_name = "password", prompt_message = f"Enter your EDS API password for {plant_name} (e.g. '')", overwrite=overwrite)
    idcs_to_iess_suffix = _get_config_with_prompt(config_key = f"{plant_name}_eds_api_iess_suffix", prompt_message = f"Enter iess suffix for {plant_name} (e.g., .UNIT0@NET0)", overwrite=overwrite)
    zd = _get_config_with_prompt(config_key = f"{plant_name}_eds_api_zd", prompt_message = f"Enter {plant_name} ZD (e.g., 'Maxson' or 'WWTF')", overwrite=overwrite)
    
    #if not all([username, password]):
    #    raise CredentialsNotFoundError(f"API credentials for '{plant_name}' not found. Please run the setup utility.")
    eds_rest_api_sub_path = str(eds_rest_api_sub_path).rstrip("/").lstrip("/").replace(r"\\","/").lower()
    eds_soap_api_port = int(eds_soap_api_port)
    eds_soap_api_sub_path = eds_soap_api_sub_path

    # EDS REST API Pattern: url = f"http://{url}:43084/api/v1" # assume EDS patterna and port http and append api/v1 if user just puts in an IP
    
    # Comparable SOAP API function, for documentation:
    eds_soap_api_url = EdsClient.get_soap_api_url(base_url = eds_base_url,
                                                    eds_soap_api_port = str(eds_soap_api_port),
                                                    eds_soap_api_sub_path = eds_soap_api_sub_path)
    if eds_soap_api_url is None:
        logging.info("Not enough information provided to build: eds_soap_api_url.")
        logging.info("Please rerun your last command or try something else.")
        sys.exit()
    
    
    eds_rest_api_url = EdsClient.get_rest_api_url(eds_base_url, 
                                        str(eds_rest_api_port),
                                        eds_rest_api_sub_path
                                        ) 
    
    if eds_rest_api_url is None:
        logging.info("Not enough information provided to build: eds_rest_api_url.")
        logging.info("Please rerun your last command or try something else.")
        sys.exit()

    return {
        'url': eds_rest_api_url,
        'username': username,
        'password': password,
        'zd': zd,
        'idcs_to_iess_suffix': idcs_to_iess_suffix

        # The URL and other non-secret config would come from a separate config file
        # or be prompted just-in-time as we discussed previously.
    }

def get_external_api_credentials(party_name: str, overwrite: bool = False) -> Dict[str, str]:
    """Retrieves API credentials for a given plant, prompting if necessary. 
    Interchangeble terms username and client_id are offered independantly and redundantly in the returned dictionary.
    This can be confusing for API clients that have both terms that mean different things (such as the MissionClient, though in that case the client=id is not sourced from stored credentials.) 
    The RJN API client was the first external API client, and it uses the term 'client_id' in place of the term 'username'."""
    service_name = f"pipeline-external-api-{party_name}"
    
    url = _get_config_with_prompt(config_key = service_name, prompt_message = f"Enter {party_name} API URL (e.g., http://api.example.com)", overwrite=overwrite)
    username = _get_credential_with_prompt( service_name = service_name, item_name = "username", prompt_message = f"Enter the username AKA client_id for the {party_name} API",hide=False, overwrite=overwrite)
    #client_id = _get_credential_with_prompt(service_name = service_name, item_name = "client_id", prompt_message = f"Enter the client_id for the {party_name} API",hide=False, overwrite=overwrite)
    password = _get_credential_with_prompt(service_name = service_name, item_name = "password", prompt_message = f"Enter the password for the {party_name} API", overwrite=overwrite)

    client_id = username
    
    #if not all([client_id, password]):
    #    raise CredentialsNotFoundError(f"API credentials for '{party_name}' not found. Please run the setup utility.")
        
    return {
        'url': url,
        'username': username,
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

def _get_base_url_config_with_prompt(service_name: str, 
                                         prompt_message: str, 
                                         overwrite: bool = False
                                         ) -> str:
    #url = _get_config_with_prompt(config_key = service_name, prompt_message = prompt_message, overwrite=overwrite)
    url = _get_credential_with_prompt(service_name=service_name, item_name="base_url",prompt_message=prompt_message, overwrite=overwrite)
    if url is None:
        return None
    if _is_likely_ip(url):
        url = f"http://{url}" # assume EDS patterns and port http if user just puts in an IP
    return url

class CredentialsNotFoundError(Exception):
    """Custom exception for missing credentials."""
    pass

# Example usage in your main pipeline
def frontload_build_all_credentials(forget : bool = False):
    """
    Sets up all possible API and database credentials for the pipeline.
    
    This function is intended for "super users" who have cloned the repository.
    It will attempt to retrieve and, if necessary, prompt for all known
    credentials and configuration values in a single execution.
    
    This is an alternative to the just-in-time setup, which prompts for
    credentials only as they are needed.
    
    Note: This will prompt for credentials for all supported plants and external
    APIs in sequence.

    'forget' should be an option that can be toggled with env var PIPELINE_FORGET, which has a default of False when set up.
    Functions that require forget:
        - frontload_build_all_credentials()
        - _get_config_with_prompt() # stored as plaintext
        - _get_credential_with_prompt() # stored to keyring
        
    Functions that store things are antithetical to 'forget':
        - _get_eds_local_db_credentials() # helper functon
    """
    
    try:
        maxson_api_creds = get_eds_rest_api_credentials(plant_name = "Maxson")
        stiles_api_creds = get_eds_rest_api_credentials(plant_name = "Stiles")
        stiles_db_creds = get_eds_local_db_credentials(plant_name = "Stiles")
        rjn_api_creds = get_external_api_credentials("RJN")
        
        # Now use the credentials normally in your application logic
        # ... your code to connect to services ...
        
    except CredentialsNotFoundError as e:
        print(f"Error: {e}")
        # Optionally, guide the user to the next step
        print("Tip: Run `your_package_name.configure()` or the corresponding CLI command.")


if __name__ == "__main__":
    frontload_build_all_credentials()
    
