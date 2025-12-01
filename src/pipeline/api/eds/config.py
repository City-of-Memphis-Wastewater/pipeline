from __future__ import annotations
def get_service_name(plant_name: str|None = None) -> str | None:
    """
    Describe the standardized string describing the service name that will be known to the configuration file.
    """
    if plant_name is None:
        plant_name = SecurityAndConfig.get_configurable_default_plant_name()
    if plant_name is None:
        return None
    service_name = f"pipeline-eds-api-{plant_name}" 
    return service_name

