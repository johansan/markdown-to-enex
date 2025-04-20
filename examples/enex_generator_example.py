#!/usr/bin/env python3
"""
Example script demonstrating the ENEX generator.

Usage:
    python enex_generator_example.py /path/to/note1.md /path/to/note2.md ... output.enex
"""

import sys
import datetime
from pathlib import Path

# Add the parent directory to the path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from markdown_to_enex import (
    process_markdown_file,
    convert_markdown_to_html,
    process_html_to_enml,
    process_resources,
    extract_note_metadata,
    create_note_object,
    generate_enex_file
)


def main():
    """Create an ENEX file from multiple markdown files."""
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} /path/to/note1.md /path/to/note2.md ... output.enex")
        sys.exit(1)
        
    # Last argument is the output file
    output_path = sys.argv[-1]
    
    # All other arguments are markdown files
    markdown_files = sys.argv[1:-1]
    
    # Check that all files exist
    for file_path in markdown_files:
        if not Path(file_path).exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
            
    # Configuration
    config = {
        "source_directory": str(Path.cwd()),
        "resources_directory": "examples/_resources",
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
        },
        "resource_options": {
            "max_resource_size": 10 * 1024 * 1024,
            "include_resource_attributes": True,
            "include_unknown_resources": True
        },
        "enex_options": {
            "add_creation_date": True,
            "add_update_date": True,
            "add_source_url": False,
            "extract_metadata": True,
            "default_author": "ENEX Generator Example",
            "application_name": "markdown-to-enex"
        }
    }
    
    print(f"Converting {len(markdown_files)} markdown files to ENEX...")
    
    try:
        # Process each markdown file
        notes = []
        
        for file_path in markdown_files:
            print(f"\nProcessing: {file_path}")
            
            # Process markdown
            processed_markdown, resources = process_markdown_file(file_path, config)
            print(f"Found {len(resources)} resource references")
            
            # Extract metadata
            metadata = extract_note_metadata(file_path, processed_markdown, config)
            print(f"Extracted metadata: {', '.join(metadata.keys())}")
            
            # Convert to HTML
            html_content = convert_markdown_to_html(processed_markdown, config)
            
            # Process resources
            resource_objects = process_resources(resources, config)
            print(f"Processed {len(resource_objects)} resources")
            
            # Process HTML to ENML
            enml_content, _ = process_html_to_enml(html_content, resources, config)
            
            # Create a note object
            title = metadata.get("title", Path(file_path).stem)
            created_date = metadata.get("created", metadata.get("file_created", datetime.datetime.now()))
            updated_date = metadata.get("updated", metadata.get("file_modified", created_date))
            tags = metadata.get("tags", [])
            
            note = create_note_object(
                title=title,
                content=enml_content,
                resources=resource_objects,
                config=config,
                created_date=created_date,
                updated_date=updated_date,
                tags=tags
            )
            
            notes.append(note)
            
        # Generate ENEX file
        print(f"\nGenerating ENEX file with {len(notes)} notes...")
        enex_content = generate_enex_file(notes, config, output_path)
        
        print(f"\nSuccessfully created ENEX file: {output_path}")
        print(f"File size: {Path(output_path).stat().st_size} bytes")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()