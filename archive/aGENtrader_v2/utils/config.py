"""
aGENtrader v2 Configuration Utility

This module provides utilities for loading and managing configuration settings.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union, List

logger = logging.getLogger('aGENtrader.utils.config')

class Config:
    """Class for managing application configuration."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration with provided data or empty dict.
        
        Args:
            config_data: Initial configuration data
        """
        self.config = config_data if config_data is not None else {}
        self.logger = logger
    
    @classmethod
    def from_file(cls, file_path: str) -> 'Config':
        """
        Load configuration from a file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Config instance with loaded data
        """
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            logger.info(f"Loaded configuration from {file_path}")
            return cls(config_data)
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {str(e)}")
            return cls({})
    
    def get_value(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value by its path.
        
        Args:
            path: Dot-separated path to the value (e.g., 'api.coinapi.key')
            default: Default value to return if path not found
            
        Returns:
            Configuration value or default
        """
        parts = path.split('.')
        current = self.config
        
        try:
            for part in parts:
                current = current[part]
            return current
        except (KeyError, TypeError):
            return default
    
    def set_value(self, path: str, value: Any) -> None:
        """
        Set a configuration value by its path.
        
        Args:
            path: Dot-separated path to the value (e.g., 'api.coinapi.key')
            value: Value to set
        """
        parts = path.split('.')
        current = self.config
        
        # Navigate to the second-to-last part
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value at the last part
        current[parts[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Section as a dictionary
        """
        return self.get_value(section, {})
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.
        
        Returns:
            Complete configuration dictionary
        """
        return self.config

def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get the application configuration.
    
    Args:
        config_path: Path to configuration file (optional)
        
    Returns:
        Config instance
    """
    # Use default config path if not provided
    if config_path is None:
        config_path = os.environ.get('AGENTRADER_CONFIG', 'config/default.json')
    
    # Ensure we have a valid path
    if not config_path:
        config_path = 'config/default.json'
    
    # Load from file
    config = Config.from_file(config_path)
    
    # Override with environment variables (if any)
    # For example, AGENTRADER_API_COINAPI_KEY would override api.coinapi.key
    for env_var, value in os.environ.items():
        if env_var.startswith('AGENTRADER_'):
            # Convert from environment variable format to config path
            # Example: AGENTRADER_API_COINAPI_KEY -> api.coinapi.key
            path = env_var[11:].lower().replace('_', '.')
            config.set_value(path, value)
    
    return config