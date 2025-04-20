import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigError(Exception):
    """Exception raised for errors in the configuration."""
    pass


class Config:
    """Configuration manager for the Markdown to ENEX converter.
    
    Loads configuration from a JSON file with default values and user overrides.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration system.
        
        Args:
            config_path: Path to a custom configuration file. If None, the default
                configuration will be used, and user_config.json if it exists.
        """
        self.config: Dict[str, Any] = {}
        self._load_default_config()
        
        # Try to load user config file if it exists
        user_config_path = Path(__file__).parent.parent / "config" / "user_config.json"
        if user_config_path.exists():
            try:
                self._load_custom_config(str(user_config_path))
            except ConfigError:
                # Silently continue if user config has errors
                pass
        
        # Load explicitly provided config file (overrides user config)
        if config_path:
            self._load_custom_config(config_path)
            
        self._validate_config()
    
    def _load_default_config(self) -> None:
        """Load the default configuration file."""
        default_config_path = Path(__file__).parent.parent / "config" / "default_config.json"
        
        try:
            with open(default_config_path, "r") as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ConfigError(f"Error loading default configuration: {e}")
    
    def _load_custom_config(self, config_path: str) -> None:
        """Load a custom configuration file and merge with defaults.
        
        Args:
            config_path: Path to the custom configuration file.
        """
        try:
            with open(config_path, "r") as f:
                custom_config = json.load(f)
                
            # Merge processing_options separately to prevent complete overwrite
            if "processing_options" in custom_config and "processing_options" in self.config:
                self.config["processing_options"].update(custom_config.pop("processing_options", {}))
                
            # Update the rest of the config
            self.config.update(custom_config)
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ConfigError(f"Error loading custom configuration: {e}")
    
    def _validate_config(self) -> None:
        """Validate the configuration values."""
        # Validate source_directory if provided
        if self.config.get("source_directory"):
            source_dir = Path(self.config["source_directory"])
            if not source_dir.exists() or not source_dir.is_dir():
                raise ConfigError(f"Source directory does not exist: {source_dir}")
                
        # Validate output_directory if provided
        if self.config.get("output_directory"):
            output_dir = Path(self.config["output_directory"])
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise ConfigError(f"Cannot create output directory: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: The configuration key.
            default: Default value if the key doesn't exist.
            
        Returns:
            The configuration value.
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: The configuration key.
            value: The value to set.
        """
        self.config[key] = value
        
    def to_dict(self) -> Dict[str, Any]:
        """Return the configuration as a dictionary.
        
        Returns:
            The complete configuration dictionary.
        """
        return self.config.copy()
    
    def save(self, filepath: str) -> None:
        """Save the current configuration to a file.
        
        Args:
            filepath: Path where to save the configuration.
        """
        try:
            with open(filepath, "w") as f:
                json.dump(self.config, f, indent=2)
        except OSError as e:
            raise ConfigError(f"Error saving configuration: {e}")