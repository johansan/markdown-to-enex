import unittest
import os
import tempfile
import datetime
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from markdown_to_enex.enex_generator import (
    ENEXGenerator, 
    generate_enex_file, 
    extract_note_metadata,
    create_note_object
)


class TestENEXGenerator(unittest.TestCase):
    """Tests for the ENEX generator module."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a default configuration
        self.config = {
            "enex_options": {
                "add_creation_date": True,
                "add_update_date": True,
                "add_source_url": True,
                "extract_metadata": True,
                "default_author": "Test Author",
                "enex_version": "1.0",
                "application_name": "markdown-to-enex-test"
            }
        }
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create a test note
        self.note = {
            "title": "Test Note",
            "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">\n<en-note><p>Test content</p></en-note>",
            "created": datetime.datetime(2023, 1, 1, 12, 0, 0),
            "updated": datetime.datetime(2023, 1, 2, 12, 0, 0),
            "author": "Test Author",
            "resources": [],
            "tags": ["test", "example"],
            "notebook": "Test Notebook",
            "source_url": "https://example.com",
            "guid": "test-guid"
        }
        
        # Create a test markdown file with metadata
        self.md_file_path = self.temp_path / "test_with_metadata.md"
        md_content = """# Test Markdown Title
created: 2023-01-01
updated: 2023-01-02
tags: tag1, tag2, tag3

This is a test markdown file with metadata.
"""
        with open(self.md_file_path, 'w') as f:
            f.write(md_content)
            
        # Create a test markdown file without metadata
        self.md_file_no_meta_path = self.temp_path / "test_without_metadata.md"
        md_content_no_meta = """This is a test markdown file without metadata.
        
It has no title or other metadata.
"""
        with open(self.md_file_no_meta_path, 'w') as f:
            f.write(md_content_no_meta)
            
        # Initialize generator
        self.generator = ENEXGenerator(self.config)
        
    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
        
    def test_create_note_object(self):
        """Test creating a note object."""
        note = self.generator.create_note_object(
            title="Test Note",
            content="<en-note><p>Test content</p></en-note>",
            resources=[],
            created_date=datetime.datetime(2023, 1, 1, 12, 0, 0),
            updated_date=datetime.datetime(2023, 1, 2, 12, 0, 0),
            source_url="https://example.com",
            author="Test Author",
            tags=["test", "example"],
            notebook="Test Notebook"
        )
        
        self.assertEqual(note["title"], "Test Note")
        self.assertEqual(note["content"], "<en-note><p>Test content</p></en-note>")
        self.assertEqual(note["created"], datetime.datetime(2023, 1, 1, 12, 0, 0))
        self.assertEqual(note["updated"], datetime.datetime(2023, 1, 2, 12, 0, 0))
        self.assertEqual(note["author"], "Test Author")
        self.assertEqual(note["tags"], ["test", "example"])
        self.assertEqual(note["notebook"], "Test Notebook")
        self.assertEqual(note["source_url"], "https://example.com")
        self.assertTrue("guid" in note)
        
    def test_extract_note_metadata_with_metadata(self):
        """Test extracting metadata from a markdown file with metadata."""
        with open(self.md_file_path, 'r') as f:
            content = f.read()
            
        metadata = self.generator.extract_note_metadata(str(self.md_file_path), content)
        
        self.assertEqual(metadata["title"], "Test Markdown Title")
        self.assertEqual(metadata["created"], datetime.datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(metadata["updated"], datetime.datetime(2023, 1, 2, 0, 0, 0))
        self.assertEqual(metadata["tags"], ["tag1", "tag2", "tag3"])
        
    def test_extract_note_metadata_without_metadata(self):
        """Test extracting metadata from a markdown file without metadata."""
        with open(self.md_file_no_meta_path, 'r') as f:
            content = f.read()
            
        metadata = self.generator.extract_note_metadata(str(self.md_file_no_meta_path), content)
        
        # Should extract title from filename
        self.assertEqual(metadata["title"], "test_without_metadata")
        
        # Should have file created/modified times
        self.assertTrue("file_created" in metadata)
        self.assertTrue("file_modified" in metadata)
        
    def test_generate_note_xml(self):
        """Test generating XML for a note."""
        note_xml = self.generator._generate_note_xml(self.note)
        
        # Check basic structure
        self.assertIn("<note>", note_xml)
        self.assertIn("</note>", note_xml)
        
        # Check title
        self.assertIn("<title>Test Note</title>", note_xml)
        
        # Check dates
        self.assertIn("<created>20230101T120000Z</created>", note_xml)
        self.assertIn("<updated>20230102T120000Z</updated>", note_xml)
        
        # Check tags
        self.assertIn("<tag>test</tag>", note_xml)
        self.assertIn("<tag>example</tag>", note_xml)
        
        # Check note attributes
        self.assertIn("<note-attributes>", note_xml)
        self.assertIn("<author>Test Author</author>", note_xml)
        self.assertIn("<source-url>https://example.com</source-url>", note_xml)
        self.assertIn("<notebook>Test Notebook</notebook>", note_xml)
        
        # Check content
        self.assertIn("<content>", note_xml)
        self.assertIn("<en-note><p>Test content</p></en-note>", note_xml)
        
    def test_generate_enex_file(self):
        """Test generating a complete ENEX file."""
        # Create a test output path
        output_path = self.temp_path / "test_output.enex"
        
        # Generate ENEX file
        enex_content = self.generator.generate_enex_file([self.note], str(output_path))
        
        # Check that the file was created
        self.assertTrue(output_path.exists())
        
        # Check content of ENEX file
        with open(output_path, 'r') as f:
            file_content = f.read()
            
        self.assertEqual(file_content, enex_content)
        
        # Check basic structure
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', enex_content)
        self.assertIn('<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">', enex_content)
        self.assertIn('<en-export', enex_content)
        self.assertIn('</en-export>', enex_content)
        
        # Check application name and version
        self.assertIn('application="markdown-to-enex-test"', enex_content)
        self.assertIn('version="1.0"', enex_content)
        
        # Check that the note content is included
        self.assertIn('<title>Test Note</title>', enex_content)
        
        # Try to parse XML to ensure it's valid
        try:
            ET.fromstring(enex_content)
        except ET.ParseError as e:
            self.fail(f"Generated ENEX is not valid XML: {e}")
            
    def test_format_date(self):
        """Test date formatting."""
        date = datetime.datetime(2023, 1, 1, 12, 30, 45)
        formatted = self.generator._format_date(date)
        self.assertEqual(formatted, "20230101T123045Z")
        
    def test_parse_date(self):
        """Test date parsing."""
        # Test various date formats
        date_formats = {
            "2023-01-01": datetime.datetime(2023, 1, 1, 0, 0, 0),
            "2023-01-01 12:30:45": datetime.datetime(2023, 1, 1, 12, 30, 45),
            "2023-01-01T12:30:45": datetime.datetime(2023, 1, 1, 12, 30, 45),
            "2023-01-01T12:30:45Z": datetime.datetime(2023, 1, 1, 12, 30, 45),
            "20230101T123045Z": datetime.datetime(2023, 1, 1, 12, 30, 45),
            "01/01/2023": datetime.datetime(2023, 1, 1, 0, 0, 0),
            "Jan 01, 2023": datetime.datetime(2023, 1, 1, 0, 0, 0),
            "01 Jan 2023": datetime.datetime(2023, 1, 1, 0, 0, 0),
            "January 01, 2023": datetime.datetime(2023, 1, 1, 0, 0, 0),
            "01 January 2023": datetime.datetime(2023, 1, 1, 0, 0, 0),
            "2023/01/01": datetime.datetime(2023, 1, 1, 0, 0, 0)
        }
        
        for date_str, expected_date in date_formats.items():
            try:
                parsed = self.generator._parse_date(date_str)
                self.assertEqual(parsed, expected_date)
            except ValueError:
                # Only fail if dateutil is available
                try:
                    import dateutil
                    self.fail(f"Failed to parse valid date string: {date_str}")
                except ImportError:
                    # If dateutil is not available, some formats might fail
                    pass
                    
    def test_module_functions(self):
        """Test the module-level functions."""
        # Test create_note_object
        note = create_note_object(
            title="Test Note",
            content="<en-note><p>Test content</p></en-note>",
            resources=[],
            config=self.config,
            created_date=datetime.datetime(2023, 1, 1, 12, 0, 0)
        )
        
        self.assertEqual(note["title"], "Test Note")
        
        # Test extract_note_metadata
        with open(self.md_file_path, 'r') as f:
            content = f.read()
            
        metadata = extract_note_metadata(str(self.md_file_path), content, self.config)
        
        self.assertEqual(metadata["title"], "Test Markdown Title")
        
        # Test generate_enex_file
        enex_content = generate_enex_file([note], self.config)
        
        self.assertIn('<title>Test Note</title>', enex_content)


if __name__ == "__main__":
    unittest.main()