import json
import os
from pathlib import Path
from pipeline.config.key_registry import get_all_keys

# --- Configuration ---
# Define the output path for the JSON Schema artifact
OUTPUT_DIR = Path("build/artifacts")
SCHEMA_FILE = OUTPUT_DIR / "config_schema.json"

def get_json_schema_type(config_key):
    """
    Determines the JSON Schema type based on Python typing or defaults.
    In a more complex system, this would map types like 'int' or 'float'.
    For now, we map everything to 'string' since all inputs are user text.
    """
    # Note: If ConfigKey included a 'python_type' field (e.g., int, str),
    # we would use that here. Assuming string for all user input fields for simplicity.
    return "string"

def generate_schema():
    """
    Reads the Python registry, transforms the data into a JSON Schema structure,
    and writes the result to a file.
    """
    print("Starting JSON Schema generation...")
    
    # 1. Initialize the root schema structure
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "EDS Configuration and Credential Schema",
        "description": "Defines the structure and validation rules for all configuration keys.",
        "type": "object",
        "properties": {},
        "required": []
    }
    
    # 2. Iterate over all ConfigKey objects
    for key_def in get_all_keys():
        key_stem = key_def.key_stem
        
        # Build properties block for the key
        schema.get("properties")[key_stem] = {
            "type": get_json_schema_type(key_def),
            "description": key_def.description,
            "prompt_message": key_def.prompt_message,
            "security_level": key_def.security_level.name, # Export enum name
            "scope": key_def.scope.name                     # Export enum name
        }
        
        # Add required keys to the 'required' array
        if key_def.is_required:
            schema.get("required").append(key_stem)
            
        # Add default value if present
        if key_def.default_value is not None:
            schema.get("properties")[key_stem]["default"] = key_def.default_value

    # 3. Ensure the output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 4. Serialize the result to JSON file
    with open(SCHEMA_FILE, 'w') as f:
        json.dump(schema, f, indent=4)
        
    print(f"Successfully generated schema at: {SCHEMA_FILE.resolve()}")
    
if __name__ == "__main__":
    # Note: You must run this script from the project root 
    # (or adjust PYTHONPATH) so 'pipeline.config.key_registry' can be imported.
    try:
        generate_schema()
    except ImportError as e:
        print("ERROR: Could not import 'pipeline.config.key_registry'.")
        print("Ensure you are running this script from the project root or your Python path is set correctly.")
        print(f"Details: {e}")
