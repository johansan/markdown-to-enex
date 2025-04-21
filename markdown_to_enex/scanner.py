import os
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple


class Note:
    """Represents a markdown note with its metadata and resource references."""
    
    def __init__(self, file_path: Path, relative_path: Path):
        """Initialize a note object.
        
        Args:
            file_path: Absolute path to the markdown file
            relative_path: Path relative to the source directory
        """
        self.file_path = file_path
        self.relative_path = relative_path
        self.title = self._extract_title()
        self.resource_refs: Set[str] = set()
        self.folder_path = str(relative_path.parent) if str(relative_path.parent) != "." else ""
        self.enex_filename = self._generate_enex_filename()
        
    def _extract_title(self) -> str:
        """Extract the title from the file name or content."""
        # Default to filename without extension
        return self.file_path.stem
        
    def _generate_enex_filename(self) -> str:
        """Generate ENEX filename based on folder structure.
        
        For a note in folder/subfolder/note.md, the ENEX filename
        will be folder_subfolder.enex
        """
        if not self.folder_path:
            return "root.enex"
            
        # Replace slashes with underscores to create a flat filename
        return f"{self.folder_path.replace('/', '_')}.enex"
    
    def scan_resources(self) -> None:
        """Scan the note content for resource references."""
        if not self.file_path.exists():
            return
            
        try:
            content = self.file_path.read_text(encoding='utf-8')
            
            # Find all markdown image references: ![alt](path)
            image_refs = re.findall(r'!\[.*?\]\((.*?)\)', content)
            
            # Find all HTML image references: <img src="path" />
            html_refs = re.findall(r'<img.*?src=["\'](.*?)["\']', content)
            
            # Combine all references and normalize paths
            all_refs = image_refs + html_refs
            
            for ref in all_refs:
                # Convert path to normalized form
                norm_path = os.path.normpath(ref.strip())
                self.resource_refs.add(norm_path)
                
        except Exception as e:
            print(f"Error scanning resources in {self.file_path}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the note to a dictionary representation."""
        return {
            "file_path": str(self.file_path),
            "relative_path": str(self.relative_path),
            "title": self.title,
            "resource_refs": list(self.resource_refs),
            "folder_path": self.folder_path,
            "enex_filename": self.enex_filename
        }


class DirectoryScanner:
    """Scans a directory structure for markdown files and resources."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the directory scanner.
        
        Args:
            config: Configuration dictionary containing paths and options
        """
        self.source_dir = Path(config.get("source_directory", ""))
        self.resources: Dict[str, Path] = {}
        self.notes: List[Note] = []
        self.directories: Dict[str, List[str]] = {}
        
    def scan(self) -> Dict[str, Any]:
        """Scan the source directory for markdown files and resources.
        
        Returns:
            A dictionary containing the scan results
        """
        if not self.source_dir.exists() or not self.source_dir.is_dir():
            raise ValueError(f"Source directory does not exist: {self.source_dir}")
        
        # Then scan for markdown files
        self._scan_markdown_files()
        
        # Process resource references in notes
        for note in self.notes:
            note.scan_resources()
            
        # Return the structured representation
        return self._build_result()
        
    def _scan_markdown_files(self) -> None:
        """Recursively scan for markdown files in the source directory."""
        for path in self.source_dir.glob('**/*.md'):
            rel_path = path.relative_to(self.source_dir)
            note = Note(path, rel_path)
            self.notes.append(note)
            
            # Record directory structure
            dir_path = str(rel_path.parent)
            if dir_path == '.':
                dir_path = ''
                
            if dir_path not in self.directories:
                self.directories[dir_path] = []
                
            self.directories[dir_path].append(note.title)
    
    def _build_result(self) -> Dict[str, Any]:
        """Build a structured result of the scanning process."""
        return {
            "source_directory": str(self.source_dir),
            "total_notes": len(self.notes),
            "total_resources": len(self.resources),
            "notes": [note.to_dict() for note in self.notes],
            "resources": {k: str(v) for k, v in self.resources.items()},
            "directory_structure": self.directories
        }


def scan_directory(config: Dict[str, Any]) -> Dict[str, Any]:
    """Scan a directory for markdown files and resources.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        A dictionary containing the scan results
    """
    scanner = DirectoryScanner(config)
    return scanner.scan()