#!/usr/bin/env python3
"""
Example script demonstrating the complete markdown to ENEX conversion process.

Usage:
    python enex_converter_example.py /path/to/markdown/file.md
"""

import sys
import datetime
from pathlib import Path
import uuid

# Add the parent directory to the path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from markdown_to_enex import process_markdown_file, convert_markdown_to_html, process_html_to_enml, process_resources


def create_enex_file(note_title, enml_content, resources, output_path=None):
    """Create an ENEX file with the given note content and resources.
    
    Args:
        note_title: Title of the note
        enml_content: ENML content of the note
        resources: List of resources to include
        output_path: Path where to save the ENEX file (optional)
            
    Returns:
        ENEX content as string
    """
    # Create ENEX content
    created_date = datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")
    note_guid = str(uuid.uuid4())
    
    # Start ENEX file
    enex_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="{created_date}" application="markdown-to-enex" version="1.0">
  <note>
    <title>{note_title}</title>
    <created>{created_date}</created>
    <updated>{created_date}</updated>
    <note-attributes>
      <author>markdown-to-enex</author>
    </note-attributes>
    <content>{enml_content}</content>
"""
    
    # Add resources
    for resource in resources:
        mime_type = resource.get("mime", "application/octet-stream")
        resource_hash = resource.get("hash", "")
        filename = resource.get("filename", "")
        data = resource.get("data", "")
        
        enex_content += f"""    <resource>
      <data encoding="base64">{data}</data>
      <mime>{mime_type}</mime>
      <resource-attributes>
        <file-name>{filename}</file-name>
      </resource-attributes>
    </resource>
"""
    
    # Close note and export
    enex_content += "  </note>\n</en-export>"
    
    # Save to file if output path is provided
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(enex_content)
    
    return enex_content


def main():
    """Convert a markdown file to ENEX format."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/file.md")
        sys.exit(1)
        
    md_file = sys.argv[1]
    
    # Configuration
    config = {
        "source_directory": str(Path(md_file).parent),
        "resources_directory": "_resources",
        "processing_options": {
            "remove_code_block_markers": True,
            "convert_inline_code": True,
            "remove_heading_markers": True,
            "handle_image_references": True,
            "process_links": True,
            "handle_special_chars": True
        },
        "html_options": {
            "markdown_engine": "python-markdown",
            "enable_tables": True,
            "enable_fenced_code": True
        },
        "enml_options": {
            "clean_html": True,
            "add_creation_date": True
        }
    }
    
    print(f"Converting {md_file} to ENEX...")
    
    try:
        # Step 1: Process markdown
        print("\nStep 1: Processing markdown...")
        processed_markdown, resources = process_markdown_file(md_file, config)
        print(f"Found {len(resources)} resource references")
        
        # Step 2: Convert to HTML
        print("\nStep 2: Converting to HTML...")
        html_content = convert_markdown_to_html(processed_markdown, config)
        
        # Step 3: Process resources
        print("\nStep 3: Processing resources...")
        resource_objects = process_resources(resources, config)
        print(f"Processed {len(resource_objects)} resources")
        
        # Step 4: Process HTML to ENML
        print("\nStep 4: Processing HTML to ENML...")
        enml_content, _ = process_html_to_enml(html_content, resources, config)
        
        # Step 5: Create ENEX file
        print("\nStep 5: Creating ENEX file...")
        note_title = Path(md_file).stem
        output_file = Path(md_file).with_suffix('.enex')
        
        enex_content = create_enex_file(note_title, enml_content, resource_objects, output_file)
        
        print(f"\nConversion successful! Output saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()