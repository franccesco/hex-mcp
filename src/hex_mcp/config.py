"""Configuration handling for Hex MCP server."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def get_config_file_path() -> Path:
    """Get the path to the configuration file."""
    return Path.home() / ".hex-mcp" / "config.yaml"


def load_config() -> Dict[str, Any]:
    """Load configuration from the config file.

    Returns:
        Dictionary containing the configuration values
    """
    config_file = get_config_file_path()
    config = {}

    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load config from {config_file}: {e}")

    return config


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to the config file.

    Args:
        config: Dictionary containing the configuration values to save
    """
    config_file = get_config_file_path()
    config_dir = config_file.parent

    # Create config directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)

    # Write config to file
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value.

    Args:
        key: The configuration key to get
        default: Default value to return if the key is not found

    Returns:
        The configuration value or default
    """
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value: Any) -> None:
    """Set a configuration value.

    Args:
        key: The configuration key to set
        value: The value to set
    """
    config = load_config()
    config[key] = value
    save_config(config)


def get_api_key() -> Optional[str]:
    """Get the Hex API key from environment variable or config file.

    Environment variable takes precedence over config file.

    Returns:
        The API key or None if not found
    """
    return os.getenv("HEX_API_KEY") or get_config_value("api_key")


def get_api_url() -> str:
    """Get the Hex API URL from environment variable or config file.

    Environment variable takes precedence over config file.

    Returns:
        The API URL or default URL if not found
    """
    return os.getenv("HEX_API_URL") or get_config_value("api_url", "https://app.hex.tech/api/v1")
