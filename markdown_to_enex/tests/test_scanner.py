import unittest
import tempfile
import os
from pathlib import Path

from markdown_to_enex.scanner import DirectoryScanner, Note, scan_directory


class TestScanner(unittest.TestCase):
    """Test cases for the directory scanner."""
    
    def setUp(self):
        """Create temporary directory structure for testing."""
        # Create a temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_dir = Path(self.temp_dir.name)
        
        # Create resources directory
        self.resources_dir = self.source_dir / "_resources"
        self.resources_dir.mkdir()
        
        # Create some resource files
        (self.resources_dir / "image1.png").touch()
        (self.resources_dir / "image2.jpg").touch()
        
        # Create directory structure
        (self.source_dir / "Folder1").mkdir()
        (self.source_dir / "Folder2").mkdir()
        (self.source_dir / "Folder2" / "SubFolder").mkdir()
        
        # Create sample markdown files
        root_note = self.source_dir / "root_note.md"
        folder1_note = self.source_dir / "Folder1" / "note1.md"
        folder2_note = self.source_dir / "Folder2" / "note2.md"
        subfolder_note = self.source_dir / "Folder2" / "SubFolder" / "subnote.md"
        
        # Write content with resource references
        root_note.write_text("# Root Note\n\nThis is a root note with image: ![Image](_resources/image1.png)")
        folder1_note.write_text("# Note 1\n\nThis is note 1 with no images.")
        folder2_note.write_text("# Note 2\n\nThis is note 2 with HTML image: <img src='../_resources/image2.jpg' />")
        subfolder_note.write_text("# Sub Note\n\nThis is a sub note with image: ![Image](../../_resources/image1.png)")
        
        # Create config for testing
        self.config = {
            "source_directory": str(self.source_dir),
            "resources_directory": "_resources"
        }
        
    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
        
    def test_note_initialization(self):
        """Test Note class initialization."""
        file_path = self.source_dir / "root_note.md"
        relative_path = Path("root_note.md")
        note = Note(file_path, relative_path)
        
        self.assertEqual(note.title, "root_note")
        self.assertEqual(note.file_path, file_path)
        self.assertEqual(note.relative_path, relative_path)
        
    def test_note_scan_resources(self):
        """Test scanning a note for resource references."""
        file_path = self.source_dir / "root_note.md"
        relative_path = Path("root_note.md")
        note = Note(file_path, relative_path)
        note.scan_resources()
        
        self.assertIn("_resources/image1.png", note.resource_refs)
        
    def test_directory_scanner_initialization(self):
        """Test DirectoryScanner initialization."""
        scanner = DirectoryScanner(self.config)
        
        self.assertEqual(scanner.source_dir, self.source_dir)
        self.assertEqual(scanner.resources_path, self.source_dir / "_resources")
        
    def test_scan_resources(self):
        """Test scanning for resources."""
        scanner = DirectoryScanner(self.config)
        scanner._scan_resources()
        
        self.assertEqual(len(scanner.resources), 2)
        self.assertIn("image1.png", scanner.resources)
        self.assertIn("image2.jpg", scanner.resources)
        
    def test_scan_markdown_files(self):
        """Test scanning for markdown files."""
        scanner = DirectoryScanner(self.config)
        scanner._scan_markdown_files()
        
        self.assertEqual(len(scanner.notes), 4)
        
        # Check directory structure
        self.assertIn("", scanner.directories)  # Root directory
        self.assertIn("Folder1", scanner.directories)
        self.assertIn("Folder2", scanner.directories)
        self.assertIn("Folder2/SubFolder", scanner.directories)
        
    def test_complete_scan(self):
        """Test complete scanning process."""
        result = scan_directory(self.config)
        
        self.assertEqual(result["total_notes"], 4)
        self.assertEqual(result["total_resources"], 2)
        self.assertEqual(len(result["directory_structure"]), 4)  # 4 directories
        
        # Check resource references in notes
        found_refs = False
        for note in result["notes"]:
            if "root_note" in note["title"]:
                self.assertIn("_resources/image1.png", note["resource_refs"])
                found_refs = True
                
        self.assertTrue(found_refs, "Resource references not found in root note")
        
    def test_nonexistent_source_dir(self):
        """Test scanning with nonexistent source directory."""
        config = {
            "source_directory": "/nonexistent/directory",
            "resources_directory": "_resources"
        }
        
        with self.assertRaises(ValueError):
            scan_directory(config)


if __name__ == "__main__":
    unittest.main()