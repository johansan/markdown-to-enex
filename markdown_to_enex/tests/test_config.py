import unittest
import tempfile
import json
import os
from pathlib import Path

from markdown_to_enex.config import Config, ConfigError


class TestConfig(unittest.TestCase):
    """Test cases for the configuration system."""
    
    def setUp(self):
        """Create temporary files for testing."""
        # Create a temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a valid custom config file
        self.valid_config_path = os.path.join(self.temp_dir.name, "valid_config.json")
        valid_config = {
            "source_directory": self.temp_dir.name,
            "output_directory": self.temp_dir.name,
            "processing_options": {
                "custom_option": True
            }
        }
        with open(self.valid_config_path, "w") as f:
            json.dump(valid_config, f)
            
        # Create an invalid config file
        self.invalid_config_path = os.path.join(self.temp_dir.name, "invalid_config.json")
        with open(self.invalid_config_path, "w") as f:
            f.write("Not a valid JSON")
    
    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def test_default_config_load(self):
        """Test loading the default configuration."""
        config = Config()
        self.assertIn("processing_options", config.to_dict())
        
    def test_custom_config_load(self):
        """Test loading a custom configuration."""
        config = Config(self.valid_config_path)
        self.assertEqual(config.get("source_directory"), self.temp_dir.name)
        self.assertEqual(config.get("output_directory"), self.temp_dir.name)
        self.assertTrue(config.get("processing_options").get("custom_option"))
        
        # Check that default options are preserved
        self.assertTrue(config.get("processing_options").get("remove_code_block_markers"))
        
    def test_invalid_config_file(self):
        """Test loading an invalid configuration file."""
        with self.assertRaises(ConfigError):
            Config(self.invalid_config_path)
            
    def test_nonexistent_config_file(self):
        """Test loading a nonexistent configuration file."""
        with self.assertRaises(ConfigError):
            Config("nonexistent_file.json")
            
    def test_get_set_methods(self):
        """Test get and set methods."""
        config = Config()
        config.set("new_key", "new_value")
        self.assertEqual(config.get("new_key"), "new_value")
        self.assertEqual(config.get("nonexistent_key", "default"), "default")
        
    def test_save_config(self):
        """Test saving configuration to a file."""
        config = Config()
        config.set("test_key", "test_value")
        
        save_path = os.path.join(self.temp_dir.name, "saved_config.json")
        config.save(save_path)
        
        # Load the saved config and verify
        with open(save_path, "r") as f:
            saved_data = json.load(f)
            
        self.assertEqual(saved_data.get("test_key"), "test_value")


if __name__ == "__main__":
    unittest.main()