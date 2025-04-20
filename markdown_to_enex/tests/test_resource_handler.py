import unittest
import tempfile
import os
import hashlib
import base64
from pathlib import Path

from markdown_to_enex.resource_handler import ResourceHandler, process_resources


class TestResourceHandler(unittest.TestCase):
    """Tests for the resource handler module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a default configuration
        self.config = {
            "resources_directory": "_resources",
            "source_directory": "",
            "resource_options": {
                "max_resource_size": 1024 * 1024,  # 1MB
                "include_resource_attributes": True,
                "include_unknown_resources": True
            }
        }
        
        # Create a temporary directory for test resources
        self.temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(self.temp_dir.name)
        
        # Create resources directory
        self.resources_dir = temp_path / "_resources"
        self.resources_dir.mkdir()
        
        # Create sample test files
        self.image_path = self.resources_dir / "test_image.png"
        with open(self.image_path, 'wb') as f:
            f.write(b'Test PNG Data')
            
        self.pdf_path = self.resources_dir / "test_document.pdf"
        with open(self.pdf_path, 'wb') as f:
            f.write(b'Test PDF Data')
            
        # Calculate expected hashes
        self.image_hash = hashlib.md5(b'Test PNG Data').hexdigest()
        self.pdf_hash = hashlib.md5(b'Test PDF Data').hexdigest()
        
        # Update config with temp path
        self.config["source_directory"] = str(temp_path)
        
        # Initialize handler
        self.handler = ResourceHandler(self.config)
        
    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
        
    def test_find_resource_path(self):
        """Test finding resource paths."""
        # Test with filename
        path = self.handler._find_resource_path("test_image.png")
        self.assertIsNotNone(path)
        self.assertEqual(path.name, "test_image.png")
        
        # Test with nonexistent resource
        path = self.handler._find_resource_path("nonexistent.png")
        self.assertIsNone(path)
        
    def test_get_mime_type(self):
        """Test MIME type determination."""
        # Test various file extensions
        self.assertEqual(self.handler._get_mime_type(Path("test.jpg")), "image/jpeg")
        self.assertEqual(self.handler._get_mime_type(Path("test.png")), "image/png")
        self.assertEqual(self.handler._get_mime_type(Path("test.pdf")), "application/pdf")
        self.assertEqual(self.handler._get_mime_type(Path("test.mp3")), "audio/mpeg")
        
        # Test unknown extension - just verify it returns something
        mime_type = self.handler._get_mime_type(Path("test.xyz"))
        self.assertTrue(isinstance(mime_type, str) and len(mime_type) > 0)
        
    def test_process_resource_file(self):
        """Test processing a resource file."""
        # Process image
        resource_info = self.handler._process_resource_file(self.image_path, "test_image.png")
        
        self.assertEqual(resource_info["hash"], self.image_hash)
        self.assertEqual(resource_info["mime"], "image/png")
        self.assertEqual(resource_info["filename"], "test_image.png")
        self.assertEqual(resource_info["reference"], "test_image.png")
        self.assertTrue("data" in resource_info)
        
        # Decode base64 data to verify
        decoded_data = base64.b64decode(resource_info["data"])
        self.assertEqual(decoded_data, b'Test PNG Data')
        
    def test_process_resources(self):
        """Test processing multiple resources."""
        resource_refs = {"test_image.png", "test_document.pdf", "nonexistent.jpg"}
        
        resources = self.handler.process_resources(resource_refs)
        
        # At minimum should have the real resources
        self.assertGreaterEqual(len(resources), 2)
        
        # Check resource map
        resource_map = self.handler.get_resource_map()
        self.assertGreaterEqual(len(resource_map), 2)
        self.assertIn("test_image.png", resource_map)
        self.assertIn("test_document.pdf", resource_map)
        
        # Placeholder handling depends on configuration
        if self.handler.include_unknown_resources:
            self.assertIn("nonexistent.jpg", resource_map)
        
        # Check reference map
        reference_map = self.handler.get_reference_map()
        self.assertEqual(len(reference_map), 2)  # Only real files have entries
        self.assertIn("test_image.png", reference_map)
        self.assertIn("test_document.pdf", reference_map)
        
        # Check placeholder
        placeholder = resource_map["nonexistent.jpg"]
        self.assertTrue(placeholder.get("placeholder", False))
        
    def test_generate_resource_xml(self):
        """Test generating resource XML."""
        # Create resource info
        resource_info = {
            "data": base64.b64encode(b'Test Data').decode('utf-8'),
            "mime": "image/png",
            "hash": "abcdef1234567890",
            "filename": "test.png"
        }
        
        xml = self.handler.generate_resource_xml(resource_info)
        
        # Check XML structure
        self.assertIn("<resource>", xml)
        self.assertIn("<data encoding=\"base64\">", xml)
        self.assertIn("<mime>image/png</mime>", xml)
        self.assertIn("<resource-attributes>", xml)
        self.assertIn("<file-name>test.png</file-name>", xml)
        
        # Test without resource attributes
        self.handler.include_resource_attributes = False
        xml = self.handler.generate_resource_xml(resource_info)
        self.assertNotIn("<resource-attributes>", xml)
        
    def test_process_resources_function(self):
        """Test the main processing function."""
        resource_refs = {"test_image.png"}
        
        resources = process_resources(resource_refs, self.config)
        
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["hash"], self.image_hash)


if __name__ == "__main__":
    unittest.main()