import os
import re
import datetime
import uuid
import xml.sax.saxutils as saxutils
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional

# Regular expressions for extracting metadata
TITLE_RE = re.compile(r'^#\s+(.*?)$', re.MULTILINE)
DATE_RE = re.compile(r'^date:\s*(.*?)$', re.MULTILINE | re.IGNORECASE)
CREATED_RE = re.compile(r'^created:\s*(.*?)$', re.MULTILINE | re.IGNORECASE)
UPDATED_RE = re.compile(r'^updated:\s*(.*?)$', re.MULTILINE | re.IGNORECASE)
TAGS_RE = re.compile(r'^tags:\s*(.*?)$', re.MULTILINE | re.IGNORECASE)


class ENEXGenerator:
    """Generates ENEX files from processed notes and resources."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the ENEX generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.enex_options = config.get("enex_options", {})
        
        # Initialize options
        self.add_creation_date = self.enex_options.get("add_creation_date", True)
        self.add_update_date = self.enex_options.get("add_update_date", True)
        self.add_source_url = self.enex_options.get("add_source_url", False)
        self.extract_metadata = self.enex_options.get("extract_metadata", True)
        self.default_author = self.enex_options.get("default_author", "markdown-to-enex")
        self.enex_version = self.enex_options.get("enex_version", "1.0")
        self.application_name = self.enex_options.get("application_name", "markdown-to-enex")
        
    def generate_enex_file(self, notes: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
        """Generate an ENEX file from a list of notes.
        
        Args:
            notes: List of note dictionaries
            output_path: Optional path to save the ENEX file
            
        Returns:
            ENEX content as string
        """
        # Generate export date
        export_date = self._format_date(datetime.datetime.now())
        
        # Start ENEX document
        enex_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="{export_date}" application="{self.application_name}" version="{self.enex_version}">
"""
        
        # Add each note
        for note in notes:
            enex_content += self._generate_note_xml(note)
            
        # Close ENEX document
        enex_content += "</en-export>"
        
        # Save to file if path provided
        if output_path:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(enex_content)
                
        return enex_content
    
    def create_note_object(self, 
                           title: str, 
                           content: str, 
                           resources: List[Dict[str, Any]], 
                           created_date: Optional[datetime.datetime] = None,
                           updated_date: Optional[datetime.datetime] = None,
                           source_url: Optional[str] = None,
                           author: Optional[str] = None,
                           tags: Optional[List[str]] = None,
                           notebook: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a note object with all necessary components.
        
        Args:
            title: Note title
            content: Note content (ENML)
            resources: List of resource dictionaries
            created_date: Creation date (optional)
            updated_date: Update date (optional)
            source_url: Source URL (optional)
            author: Author name (optional)
            tags: List of tags (optional)
            notebook: Notebook name (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Note dictionary
        """
        # Use current time if dates not provided
        if created_date is None:
            created_date = datetime.datetime.now()
        if updated_date is None:
            updated_date = created_date
            
        # Set defaults
        author = author or self.default_author
        tags = tags or []
        metadata = metadata or {}
        
        # Create note object
        note = {
            "title": title,
            "content": content,
            "created": created_date,
            "updated": updated_date,
            "author": author,
            "resources": resources,
            "tags": tags,
            "notebook": notebook,
            "source_url": source_url,
            "guid": str(uuid.uuid4()),
            "metadata": metadata
        }
        
        return note
    
    def extract_note_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """Extract metadata from markdown content and file attributes.
        
        Args:
            file_path: Path to the markdown file
            content: Markdown content
            
        Returns:
            Metadata dictionary
        """
        metadata = {}
        
        # Extract file modification times
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            stat = file_path_obj.stat()
            metadata["file_created"] = datetime.datetime.fromtimestamp(stat.st_ctime)
            metadata["file_modified"] = datetime.datetime.fromtimestamp(stat.st_mtime)
        
        # Extract title from first heading or filename
        title_match = TITLE_RE.search(content)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        else:
            metadata["title"] = file_path_obj.stem
            
        # Extract dates
        date_match = DATE_RE.search(content)
        if date_match:
            date_str = date_match.group(1).strip()
            try:
                metadata["date"] = self._parse_date(date_str)
            except ValueError:
                pass
                
        created_match = CREATED_RE.search(content)
        if created_match:
            created_str = created_match.group(1).strip()
            try:
                metadata["created"] = self._parse_date(created_str)
            except ValueError:
                pass
                
        updated_match = UPDATED_RE.search(content)
        if updated_match:
            updated_str = updated_match.group(1).strip()
            try:
                metadata["updated"] = self._parse_date(updated_str)
            except ValueError:
                pass
                
        # Extract tags
        tags_match = TAGS_RE.search(content)
        if tags_match:
            tags_str = tags_match.group(1).strip()
            tags = [tag.strip() for tag in tags_str.split(',')]
            metadata["tags"] = tags
            
        return metadata
        
    def _generate_note_xml(self, note: Dict[str, Any]) -> str:
        """Generate XML for a single note.
        
        Args:
            note: Note dictionary
            
        Returns:
            Note XML as string
        """
        # Format dates
        created_date = self._format_date(note["created"])
        updated_date = self._format_date(note["updated"])
        
        # Escape title
        title = saxutils.escape(note["title"])
        
        # Start note element
        note_xml = "  <note>\n"
        
        # Add metadata
        note_xml += f"    <title>{title}</title>\n"
        
        if self.add_creation_date:
            note_xml += f"    <created>{created_date}</created>\n"
            
        if self.add_update_date:
            note_xml += f"    <updated>{updated_date}</updated>\n"
            
        # Add tags
        for tag in note.get("tags", []):
            tag_escaped = saxutils.escape(tag)
            note_xml += f"    <tag>{tag_escaped}</tag>\n"
            
        # Add note attributes
        note_xml += "    <note-attributes>\n"
        
        # Add author
        author = saxutils.escape(note.get("author", self.default_author))
        note_xml += f"      <author>{author}</author>\n"
        
        # Add source URL if available
        if self.add_source_url and "source_url" in note and note["source_url"]:
            source_url = saxutils.escape(note["source_url"])
            note_xml += f"      <source-url>{source_url}</source-url>\n"
            
        # Add source application
        note_xml += f"      <source-application>{self.application_name}</source-application>\n"
        
        # Add notebook if specified
        if "notebook" in note and note["notebook"]:
            notebook = saxutils.escape(note["notebook"])
            note_xml += f"      <notebook>{notebook}</notebook>\n"
            
        note_xml += "    </note-attributes>\n"
        
        # Add content directly (it should already be properly formatted with CDATA)
        content = note['content']
        note_xml += f"    <content>{content}</content>\n"
        
        # Add resources
        for resource in note.get("resources", []):
            note_xml += self._generate_resource_xml(resource)
            
        # Close note element
        note_xml += "  </note>\n"
        
        return note_xml
    
    def _generate_resource_xml(self, resource: Dict[str, Any]) -> str:
        """Generate XML for a resource.
        
        Args:
            resource: Resource dictionary
            
        Returns:
            Resource XML as string
        """
        mime_type = resource.get("mime", "application/octet-stream")
        data_base64 = resource.get("data", "")
        filename = resource.get("filename", "")
        
        resource_xml = "    <resource>\n"
        resource_xml += f"      <data encoding=\"base64\">{data_base64}</data>\n"
        resource_xml += f"      <mime>{mime_type}</mime>\n"
        
        # Add resource attributes if filename exists
        if filename:
            resource_xml += "      <resource-attributes>\n"
            resource_xml += f"        <file-name>{saxutils.escape(filename)}</file-name>\n"
            resource_xml += "      </resource-attributes>\n"
            
        resource_xml += "    </resource>\n"
        
        return resource_xml
    
    def _format_date(self, date: datetime.datetime) -> str:
        """Format a date in Evernote's expected format.
        
        Args:
            date: Datetime object
            
        Returns:
            Formatted date string
        """
        return date.strftime("%Y%m%dT%H%M%SZ")
        
    def _parse_date(self, date_str: str) -> datetime.datetime:
        """Parse a date string in various formats.
        
        Args:
            date_str: Date string
            
        Returns:
            Datetime object
            
        Raises:
            ValueError: If the date string cannot be parsed
        """
        # Try various date formats
        formats = [
            "%Y-%m-%d",             # 2023-01-01
            "%Y-%m-%d %H:%M:%S",    # 2023-01-01 12:30:45
            "%Y-%m-%dT%H:%M:%S",    # 2023-01-01T12:30:45
            "%Y-%m-%dT%H:%M:%SZ",   # 2023-01-01T12:30:45Z
            "%Y%m%dT%H%M%SZ",       # 20230101T123045Z
            "%d/%m/%Y",             # 01/01/2023
            "%m/%d/%Y",             # 01/01/2023
            "%b %d, %Y",            # Jan 01, 2023
            "%d %b %Y",             # 01 Jan 2023
            "%B %d, %Y",            # January 01, 2023
            "%d %B %Y",             # 01 January 2023
            "%Y/%m/%d",             # 2023/01/01
        ]
        
        for fmt in formats:
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        # If all fail, try parsing with dateutil
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except (ImportError, ValueError):
            # If dateutil is not available or fails, raise error
            raise ValueError(f"Unable to parse date: {date_str}")


def generate_enex_file(notes: List[Dict[str, Any]], config: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Generate an ENEX file from a list of notes.
    
    Args:
        notes: List of note dictionaries
        config: Configuration dictionary
        output_path: Optional path to save the ENEX file
        
    Returns:
        ENEX content as string
    """
    generator = ENEXGenerator(config)
    return generator.generate_enex_file(notes, output_path)


def extract_note_metadata(file_path: str, content: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from markdown content and file attributes.
    
    Args:
        file_path: Path to the markdown file
        content: Markdown content
        config: Configuration dictionary
        
    Returns:
        Metadata dictionary
    """
    generator = ENEXGenerator(config)
    return generator.extract_note_metadata(file_path, content)


def create_note_object(title: str, 
                      content: str, 
                      resources: List[Dict[str, Any]], 
                      config: Dict[str, Any],
                      **kwargs) -> Dict[str, Any]:
    """Create a note object with all necessary components.
    
    Args:
        title: Note title
        content: Note content (ENML)
        resources: List of resource dictionaries
        config: Configuration dictionary
        **kwargs: Additional arguments to pass to create_note_object
        
    Returns:
        Note dictionary
    """
    generator = ENEXGenerator(config)
    return generator.create_note_object(title, content, resources, **kwargs)