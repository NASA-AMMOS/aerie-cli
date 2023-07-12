from aerie_cli.aerie_host import AerieHostConfiguration
from aerie_cli.persistent import PersistentConfigurationManager

import json

def find_configuration(configuration: str) -> AerieHostConfiguration:
    """Find a configuration by name or path.
    
    configuration (str): The name or path of a configuration. Paths should be to a configuration json file.

    Returns:
        AerieHostConfiguration
    """
    # search for configuration by name
    for persistent_configuration in PersistentConfigurationManager.get_configurations():
        if persistent_configuration.name != configuration:
            continue
        return persistent_configuration
    # search for configuration by path
    try:
        with open(configuration, 'r') as fid:
            try:
                found_configuration = json.load(fid)
            except ValueError as e:
                return None
    except FileNotFoundError as e:
        return None
    
    return AerieHostConfiguration.from_dict(found_configuration)