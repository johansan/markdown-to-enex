#!/usr/bin/env python3
"""
Complete end-to-end example showing the entire workflow for converting markdown to ENEX.

Usage:
    python complete_workflow.py /path/to/notes/folder /path/to/output.enex
"""

import os
import sys
import datetime
from pathlib import Path

# Add the parent directory to the path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from markdown_to_enex import (
    Config,
    scan_directory,
    process_markdown_file,
    convert_markdown_to_html, 
    process_html_to_enml,
    process_resources,
    extract_note_metadata,
    create_note_object,
    generate_enex_file
)


def main():
    """Run the complete workflow for converting markdown notes to ENEX."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} /path/to/notes/folder /path/to/output.enex")
        sys.exit(1)
        
    source_dir = sys.argv[1]
    output_file = sys.argv[2]
    
    # Configuration
    config_dict = {
        "source_directory": source_dir,
        "output_directory": str(Path(output_file).parent),
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
        },
        "resource_options": {
            "max_resource_size": 50 * 1024 * 1024,  # 50MB
            "include_resource_attributes": True,
            "include_unknown_resources": True
        },
        "enex_options": {
            "add_creation_date": True,
            "add_update_date": True,
            "add_source_url": False,
            "extract_metadata": True,
            "default_author": "markdown-to-enex",
            "application_name": "markdown-to-enex"
        }
    }
    
    config = Config(None)
    for key, value in config_dict.items():
        config.set(key, value)
    
    print("\n" + "="*60)
    print(" MARKDOWN TO ENEX CONVERTER - COMPLETE WORKFLOW EXAMPLE ")
    print("="*60)
    
    # Step 1: Scan source directory
    print(f"\nStep 1: Scanning source directory: {source_dir}")
    scan_result = scan_directory(config.to_dict())
    
    print(f"Found {scan_result['total_notes']} notes and {scan_result['total_resources']} resources")
    
    # Group notes by target ENEX file
    print("\nNotes will be organized as follows:")
    for note in scan_result['notes']:
        print(f"  - {note['file_path']} -> {Path(note['file_path']).stem}")
        
    # Resource information    
    if scan_result['total_resources'] > 0:
        print("\nResources found:")
        for resource in scan_result['resources']:
            print(f"  - {resource}")
    
    # Step 2: Process all notes to prepare for ENEX
    print(f"\nStep 2: Processing notes...")
    
    enex_notes = []
    all_resources = set()
    
    note_count = 0
    resource_count = 0
    
    # Process each note
    for note_info in scan_result['notes']:
        note_count += 1
        file_path = note_info['file_path']
        print(f"  Processing note {note_count}/{scan_result['total_notes']}: {Path(file_path).name}")
        
        # Process markdown
        try:
            processed_markdown, resources = process_markdown_file(file_path, config.to_dict())
            
            # Track all resources
            all_resources.update(resources)
            resource_count += len(resources)
            
            # Convert to HTML
            html_content = convert_markdown_to_html(processed_markdown, config.to_dict())
            
            # Process HTML to ENML
            enml_content, _ = process_html_to_enml(html_content, resources, config.to_dict())
            
            # Extract metadata
            metadata = extract_note_metadata(file_path, processed_markdown, config.to_dict())
            
            # Create a note object
            title = metadata.get("title", Path(file_path).stem)
            created_date = metadata.get("created", metadata.get("file_created", datetime.datetime.now()))
            updated_date = metadata.get("updated", metadata.get("file_modified", created_date))
            tags = metadata.get("tags", [])
            
            note = create_note_object(
                title=title,
                content=enml_content,
                resources=[],  # We'll add resources in the next step
                config=config.to_dict(),
                created_date=created_date,
                updated_date=updated_date,
                tags=tags
            )
            
            enex_notes.append((note, resources))
            
            # Save intermediate files for inspection (for this example)
            output_dir = Path(config.get("output_directory", "."))
            md_output = output_dir / f"{Path(file_path).stem}_processed.md"
            html_output = output_dir / f"{Path(file_path).stem}.html"
            
            with open(md_output, "w", encoding="utf-8") as f:
                f.write(processed_markdown)
                
            with open(html_output, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            print(f"    Metadata: Title='{title}', Tags={tags}")
            print(f"    Intermediate files saved for inspection:")
            print(f"      - Processed Markdown: {md_output}")
            print(f"      - HTML: {html_output}")
            
        except Exception as e:
            print(f"  Error processing note {file_path}: {e}")
    
    print(f"\nProcessed {note_count} notes with {resource_count} total resource references")
    
    # Step 3: Process all resources
    print(f"\nStep 3: Processing resources...")
    resource_objects = process_resources(all_resources, config.to_dict())
    print(f"Processed {len(resource_objects)} unique resources")
    
    # Create a lookup map for resources
    resource_map = {}
    for resource in resource_objects:
        resource_map[resource['reference']] = resource
        print(f"  - {resource['reference']} ({resource['mime']})")
    
    # Step 4: Build final notes with resources
    print(f"\nStep 4: Building final notes with resources...")
    final_notes = []
    for note, note_resources in enex_notes:
        # Add only the resources referenced by this note
        note_resource_objects = []
        for ref in note_resources:
            if ref in resource_map:
                note_resource_objects.append(resource_map[ref])
        
        note['resources'] = note_resource_objects
        final_notes.append(note)
        print(f"  - Added {len(note_resource_objects)} resources to '{note['title']}'")
    
    # Step 5: Generate ENEX file
    print(f"\nStep 5: Generating ENEX file: {output_file}")
    enex_content = generate_enex_file(final_notes, config.to_dict(), output_file)
    
    print("\n" + "="*60)
    print(f"SUCCESS! Created ENEX file with {len(final_notes)} notes")
    print(f"File size: {Path(output_file).stat().st_size:,} bytes")
    print(f"Output file: {output_file}")
    print("="*60)
    print("\nYou can now import this file into Evernote using:")
    print("File > Import > ENEX (.enex) File...")
    print("="*60)


if __name__ == "__main__":
    main()