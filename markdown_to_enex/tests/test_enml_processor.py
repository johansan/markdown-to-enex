import unittest
import tempfile
import os
import hashlib
import base64
from pathlib import Path
import re

from markdown_to_enex.enml_processor import ENMLProcessor, process_html_to_enml


class TestENMLProcessor(unittest.TestCase):
    """Tests for the ENML processor module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a default configuration
        self.config = {
            "resources_directory": "_resources",
            "source_directory": "",
            "enml_options": {}
        }
        
        # Create a temporary directory for test resources
        self.temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(self.temp_dir.name)
        
        # Create resources directory
        self.resources_dir = temp_path / "_resources"
        self.resources_dir.mkdir()
        
        # Create a sample image file
        self.test_image = self.resources_dir / "test_image.png"
        with open(self.test_image, 'wb') as f:
            f.write(b'Test Image Data')
            
        # Calculate hash for test image
        with open(self.test_image, 'rb') as f:
            self.test_image_hash = hashlib.md5(f.read()).hexdigest()
            
        # Update config with temp path
        self.config["source_directory"] = str(temp_path)
        
        # Initialize processor
        self.processor = ENMLProcessor(self.config)
        
    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
        
    def test_clean_html(self):
        """Test cleaning HTML content."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>body { font-size: 12px; }</style>
        </head>
        <body>
            <div id="content" class="main" onclick="alert('test')">
                <h1>Test Heading</h1>
                <script>alert('test');</script>
                <img src="test_image.png">
            </div>
        </body>
        </html>
        """
        
        cleaned = self.processor._clean_html(html)
        
        # Check that prohibited elements are removed
        self.assertNotIn("<html>", cleaned)
        self.assertNotIn("<body>", cleaned)
        self.assertNotIn("<head>", cleaned)
        self.assertNotIn("<meta", cleaned)
        self.assertNotIn("<style>", cleaned)
        self.assertNotIn("<script>", cleaned)
        
        # Check that prohibited attributes are removed
        self.assertNotIn('id="content"', cleaned)
        self.assertNotIn('class="main"', cleaned)
        self.assertNotIn('onclick=', cleaned)
        
        # Check that content is preserved
        self.assertIn("<h1>Test Heading</h1>", cleaned)
        
        # Check that unclosed tags are fixed
        self.assertIn("<img src=", cleaned)
        self.assertIn("/>", cleaned)  # Should now have proper closing
        
    def test_find_resource_path(self):
        """Test finding resource paths."""
        # Test with filename
        path = self.processor._find_resource_path("test_image.png")
        self.assertIsNotNone(path)
        self.assertEqual(path.name, "test_image.png")
        
        # Test with nonexistent resource
        path = self.processor._find_resource_path("nonexistent.png")
        self.assertIsNone(path)
        
    def test_get_mime_type(self):
        """Test MIME type determination."""
        # Test various file extensions
        self.assertEqual(self.processor._get_mime_type(Path("test.jpg")), "image/jpeg")
        self.assertEqual(self.processor._get_mime_type(Path("test.png")), "image/png")
        self.assertEqual(self.processor._get_mime_type(Path("test.pdf")), "application/pdf")
        self.assertEqual(self.processor._get_mime_type(Path("test.txt")), "text/plain")
        
        # Test unknown extension
        self.assertEqual(self.processor._get_mime_type(Path("test.xyz")), "application/octet-stream")
        
    def test_process_image_references(self):
        """Test processing image references."""
        # Prepare resource map manually
        self.processor.resource_map = {
            "test_image.png": {
                "mime": "image/png",
                "hash": self.test_image_hash,
                "filename": "test_image.png"
            }
        }
        
        html = '<p>Test image: <img src="test_image.png" width="100" height="100" alt="Test Image"></p>'
        
        processed = self.processor._process_image_references(html)
        
        # Check that img tag is replaced with en-media
        self.assertNotIn("<img", processed)
        self.assertIn("<en-media", processed)
        self.assertIn(f'type="image/png"', processed)
        self.assertIn(f'hash="{self.test_image_hash}"', processed)
        self.assertIn('width="100"', processed)
        self.assertIn('height="100"', processed)
        self.assertIn('alt="Test Image"', processed)
        
    def test_process_html_to_enml(self):
        """Test the full HTML to ENML conversion process."""
        html = """
        <h1>Test Note</h1>
        <p>This is a test note with an image:</p>
        <img src="test_image.png" alt="Test Image">
        <p>And a list:</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        """
        
        resource_refs = {"test_image.png"}
        
        enml, resources = self.processor.process_html_to_enml(html, resource_refs)
        
        # Check that ENML has proper XML declaration and DOCTYPE
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', enml)
        self.assertIn('<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">', enml)
        
        # Check that content is wrapped in en-note
        self.assertIn('<en-note>', enml)
        self.assertIn('</en-note>', enml)
        
        # Check that image is converted to en-media
        self.assertIn('<en-media', enml)
        self.assertIn(f'hash="{self.test_image_hash}"', enml)
        
        # Check that resources list contains our image
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["hash"], self.test_image_hash)
        self.assertEqual(resources[0]["mime"], "image/png")
        self.assertEqual(resources[0]["filename"], "test_image.png")
        
    def test_process_html_to_enml_function(self):
        """Test the main processing function."""
        html = '<p>Test with image: <img src="test_image.png"></p>'
        resource_refs = {"test_image.png"}
        
        enml, resources = process_html_to_enml(html, resource_refs, self.config)
        
        self.assertIn('<en-note>', enml)
        self.assertEqual(len(resources), 1)


if __name__ == "__main__":
    unittest.main()