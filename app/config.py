import yaml
from pathlib import Path

def load_config():
    """Loads the configuration from config.yaml."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError("config.yaml not found in the project root.")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    return config

# Load the configuration once when the module is imported
config = load_config()

def get_setting(key, default=None):
    """
    Retrieves a setting from the loaded configuration using dot notation.
    e.g., get_setting("video.quality")
    """
    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value
