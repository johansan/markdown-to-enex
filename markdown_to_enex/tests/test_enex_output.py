"""Unit tests for the ENEX output module."""

import os
import unittest
import datetime
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from markdown_to_enex.enex_output import (
    ENEXOutput, generate_output, get_best_group_by, ENEXOutputError
)


class TestEnexOutput(unittest.TestCase):
    """Test cases for the ENEX output module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "output_directory": tempfile.gettempdir(),
            "output_options": {
                "group_by": "single",
                "naming_pattern": "{name}.enex",
                "max_notes_per_file": 0,
                "progress_reporting": False,
                "replace_spaces": True
            },
            "enex_options": {
                "add_creation_date": True,
                "add_update_date": True,
                "default_author": "test-author",
                "enex_version": "1.0",
                "application_name": "test-app"
            }
        }
        
        # Create sample notes
        self.notes = []
        self.note_info = []
        
        # Create 5 sample notes
        for i in range(5):
            note = {
                "title": f"Test Note {i+1}",
                "content": f"<en-note>Test content {i+1}</en-note>",
                "created": datetime.datetime.now(),
                "updated": datetime.datetime.now(),
                "author": "test-author",
                "resources": [],
                "tags": [f"tag{i+1}"],
                "notebook": f"Notebook {i//2 + 1}",  # Group into 3 notebooks
                "guid": f"guid-{i+1}"
            }
            
            note_info = {
                "file_path": f"/test/path/note{i+1}.md",
                "relative_path": f"folder{i//3 + 1}/note{i+1}.md",  # Group into 2 folders
                "folder_path": f"folder{i//3 + 1}",
                "enex_filename": f"folder{i//3 + 1}.enex"
            }
            
            self.notes.append(note)
            self.note_info.append(note_info)
    
    @patch('markdown_to_enex.enex_output.generate_enex_file')
    def test_single_file_output(self, mock_generate_enex):
        """Test generating a single ENEX file."""
        # Configure for single file output
        config = self.config.copy()
        config["output_options"]["group_by"] = "single"
        
        # Create the output handler
        output_handler = ENEXOutput(config)
        
        # Generate output
        result = output_handler.generate(self.notes, self.note_info)
        
        # Verify results
        self.assertEqual(len(result), 1)
        self.assertIn("All Notes", result)
        
        # Verify generate_enex_file was called once with all notes
        mock_generate_enex.assert_called_once()
        args, _ = mock_generate_enex.call_args
        self.assertEqual(len(args[0]), 5)  # All 5 notes
    
    @patch('markdown_to_enex.enex_output.generate_enex_file')
    def test_folder_grouping(self, mock_generate_enex):
        """Test grouping by folder."""
        # Configure for folder grouping
        config = self.config.copy()
        config["output_options"]["group_by"] = "top_folder"
        
        # Create the output handler
        output_handler = ENEXOutput(config)
        
        # Generate output
        result = output_handler.generate(self.notes, self.note_info)
        
        # Verify results - should have 2 folders
        self.assertEqual(len(result), 2)
        
        # Verify generate_enex_file was called twice
        self.assertEqual(mock_generate_enex.call_count, 2)
    
    @patch('markdown_to_enex.enex_output.generate_enex_file')
    def test_notebook_grouping(self, mock_generate_enex):
        """Test grouping by notebook."""
        # Configure for notebook grouping
        config = self.config.copy()
        config["output_options"]["group_by"] = "notebook"
        
        # Create the output handler
        output_handler = ENEXOutput(config)
        
        # Generate output
        result = output_handler.generate(self.notes, self.note_info)
        
        # Verify results - should have 3 notebooks
        self.assertEqual(len(result), 3)
        
        # Verify generate_enex_file was called three times
        self.assertEqual(mock_generate_enex.call_count, 3)
    
    @patch('markdown_to_enex.enex_output.generate_enex_file')
    def test_max_notes_limit(self, mock_generate_enex):
        """Test max notes per file limit."""
        # Configure with max 2 notes per file
        config = self.config.copy()
        config["output_options"]["group_by"] = "single"
        config["output_options"]["max_notes_per_file"] = 2
        
        # Create the output handler
        output_handler = ENEXOutput(config)
        
        # Generate output
        result = output_handler.generate(self.notes, self.note_info)
        
        # Verify results - should have 3 files (5 notes with max 2 per file)
        self.assertEqual(len(result), 3)
        
        # Verify generate_enex_file was called three times
        self.assertEqual(mock_generate_enex.call_count, 3)
    
    @patch('markdown_to_enex.enex_output.generate_enex_file')
    def test_custom_naming(self, mock_generate_enex):
        """Test custom naming pattern."""
        # Configure custom naming pattern
        config = self.config.copy()
        config["output_options"]["naming_pattern"] = "export_{name}_notes.enex"
        
        # Create the output handler
        output_handler = ENEXOutput(config)
        
        # Generate output
        result = output_handler.generate(self.notes, self.note_info)
        
        # Verify results
        self.assertEqual(len(result), 1)
        
        # Get the generated filename
        output_path = list(result.values())[0]
        filename = os.path.basename(output_path)
        
        # Verify naming pattern was applied
        self.assertEqual(filename, "export_All_Notes_notes.enex")
    
    def test_filename_sanitization(self):
        """Test filename sanitization."""
        # Create the output handler
        output_handler = ENEXOutput(self.config)
        
        # Test various input names
        test_cases = [
            ("My Notes", "My_Notes.enex"),
            ("Invalid/Chars?", "InvalidChars.enex"),
            ("  Trim Spaces  ", "Trim_Spaces.enex"),
            ("dots...and-dashes", "dots...and-dashes.enex"),
        ]
        
        for input_name, expected in test_cases:
            result = output_handler._format_filename(input_name)
            self.assertEqual(result, expected)
    
    def test_get_best_group_by(self):
        """Test get_best_group_by function."""
        # Empty folder structure
        self.assertEqual(get_best_group_by({}), "single")
        
        # Simple folder structure with few notes
        simple_structure = {
            "total_notes": 5,
            "total_resources": 2,
            "folder1": {
                "notes": ["note1.md", "note2.md"]
            }
        }
        self.assertEqual(get_best_group_by(simple_structure), "single")
        
        # Multiple top-level folders
        multi_folder = {
            "total_notes": 20,
            "total_resources": 5,
            "folder1": {"notes": ["note1.md"]},
            "folder2": {"notes": ["note2.md"]},
            "folder3": {"notes": ["note3.md"]}
        }
        self.assertEqual(get_best_group_by(multi_folder), "top_folder")
        
        # Single top folder with subfolders
        nested_folder = {
            "total_notes": 20,
            "total_resources": 5,
            "main_folder": {
                "subfolder1": {"notes": ["note1.md"]},
                "subfolder2": {"notes": ["note2.md"]}
            }
        }
        self.assertEqual(get_best_group_by(nested_folder), "full_folder")
        
        # Single top folder without subfolders
        single_folder = {
            "total_notes": 20,
            "total_resources": 5,
            "main_folder": {
                "notes": ["note1.md", "note2.md", "note3.md"]
            }
        }
        self.assertEqual(get_best_group_by(single_folder), "single")


if __name__ == '__main__':
    unittest.main()