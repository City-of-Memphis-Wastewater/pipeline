# src/pipeline/config/key_registry.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9import time
import dataclasses
from enum import Enum, auto
from typing import Optional

# --- Enums for Configuration Governance ---

class SecurityLevel(Enum):
    """
    Defines where the value for a configuration key should be stored.
    This governs the persistence mechanism in SecurityAndConfig.
    """
    # Stored in the local file system config.json (e.g., URLs, timeouts).
    PLAINTEXT = auto()
    # Stored securely in OS Keyring (e.g., passwords, API tokens).
    CREDENTIAL = auto()

class ConfigScope(Enum):
    """
    Defines the scope of a configuration key's value.
    This governs how the key is constructed for storage and retrieval.
    """
    # Key applies to the entire application/user (e.g., generic username).
    GLOBAL = auto()
    # Key is prefixed by a dynamic identifier (e.g., 'Maxson_eds_base_url').
    PER_PLANT = auto()


# --- The Registry Definition ---

@dataclasses.dataclass(frozen=True)
class ConfigKey:
    """
    A foundational definition object for a single configuration or credential key.
    This object is the single source of truth for the key's metadata.
    """
    key_stem: str
    security_level: SecurityLevel
    scope: ConfigScope
    description: str
    prompt_message: str
    is_required: bool = True
    default_value: Optional[str] = None
    
# --- The Central Registry ---

class EdsConfigKeys:
    """
    The central, immutable registry defining all known configuration and 
    credential keys used by the pipeline-eds library.
    
    All client code (CLI, SPA backend, etc.) MUST reference these objects.
    """
    
    # --- EDS Client Configuration ---
    
    EDS_BASE_URL = ConfigKey(
        key_stem="eds_base_url",
        security_level=SecurityLevel.PLAINTEXT,
        scope=ConfigScope.PER_PLANT,
        description="The base URL for the EDS SOAP API.",
        prompt_message="Please enter the EDS base URL (e.g., http://0.0.0.0/eds):"
    )

    EDS_TIMEOUT_SECONDS = ConfigKey(
        key_stem="timeout_seconds",
        security_level=SecurityLevel.PLAINTEXT,
        scope=ConfigScope.GLOBAL,
        description="Default timeout for SOAP requests in seconds.",
        prompt_message="Enter the default API timeout in seconds:",
        default_value="30",
        is_required=False
    )

    # --- Credentials ---

    EDS_USERNAME = ConfigKey(
        key_stem="username",
        security_level=SecurityLevel.CREDENTIAL,
        scope=ConfigScope.GLOBAL, # Assuming the same user logs into all plants
        description="The API username for authenticating with EDS.",
        prompt_message="Enter your EDS API username:"
    )

    EDS_PASSWORD = ConfigKey(
        key_stem="password",
        security_level=SecurityLevel.CREDENTIAL,
        scope=ConfigScope.GLOBAL,
        description="The API password for the given username.",
        prompt_message="Enter your EDS API password:"
    )

    # --- Auxiliary / State Keys ---

    LAST_USED_PLANT = ConfigKey(
        key_stem="last_used_plant",
        security_level=SecurityLevel.PLAINTEXT,
        scope=ConfigScope.GLOBAL,
        description="The last plant name successfully used.",
        prompt_message="", # No prompt needed, this is internal state
        is_required=False
    )

# A utility function to retrieve all keys for easy iteration (e.g., for JSON Schema generation)
def get_all_keys():
    """Returns a list of all ConfigKey objects defined in the registry."""
    keys = []
    for attr_name in dir(EdsConfigKeys):
        attr = getattr(EdsConfigKeys, attr_name)
        if isinstance(attr, ConfigKey):
            keys.append(attr)
    return keys

# Example usage to retrieve the prompt message for a key:
# prompt = EdsConfigKeys.EDS_BASE_URL.prompt_message
# security = EdsConfigKeys.EDS_USERNAME.security_level