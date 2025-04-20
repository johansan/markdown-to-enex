#!/usr/bin/env python3
"""
Example script demonstrating the ENEX output module capabilities.

Usage:
    python enex_output_example.py /path/to/notes/folder /path/to/output/dir
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
    generate_output,
    get_best_group_by
)


def main():
    """Run the ENEX output example workflow."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} /path/to/notes/folder /path/to/output/dir")
        sys.exit(1)
        
    source_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Ensure output directory exists
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    
    # Configuration
    config_dict = {
        "source_directory": source_dir,
        "output_directory": output_dir,
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
        },
        "output_options": {
            "group_by": "top_folder",           # Try: "single", "top_folder", "full_folder", "notebook"
            "naming_pattern": "{name}.enex",    # Pattern for output filenames
            "max_notes_per_file": 100,          # Max notes per ENEX file (0 = no limit)
            "progress_reporting": True,         # Enable progress reporting
            "replace_spaces": True              # Replace spaces with underscores in filenames
        }
    }
    
    config = Config(None)
    for key, value in config_dict.items():
        config.set(key, value)
    
    print("\n" + "="*60)
    print(" MARKDOWN TO ENEX CONVERTER - ENEX OUTPUT EXAMPLE ")
    print("="*60)
    
    # Step 1: Scan source directory
    print(f"\nStep 1: Scanning source directory: {source_dir}")
    scan_result = scan_directory(config.to_dict())
    
    print(f"Found {scan_result['total_notes']} notes and {scan_result['total_resources']} resources")
    
    # Suggest best grouping strategy
    folder_structure = scan_result.get("folder_structure", {})
    best_group_by = get_best_group_by(folder_structure)
    print(f"Suggested grouping strategy: {best_group_by}")
    
    # Ask user for grouping preference
    print("\nGrouping options:")
    print("  single      - Create a single ENEX file for all notes")
    print("  top_folder  - Group notes by top-level folder")
    print("  full_folder - Group notes by full folder path")
    print("  notebook    - Group notes by notebook metadata")
    print("  custom      - Use enex_filename from note info")
    
    group_by = input(f"\nChoose grouping strategy [{best_group_by}]: ").strip()
    if not group_by:
        group_by = best_group_by
    
    # Update config with user's preference
    config.get("output_options")["group_by"] = group_by
    
    # Process all notes and resources
    print("\nProcessing notes and resources...")
    
    processed_notes = []
    note_info_list = []
    all_resources = set()
    
    for note_info in scan_result['notes']:
        file_path = note_info['file_path']
        try:
            # Process markdown to HTML to ENML
            processed_markdown, resources, frontmatter = process_markdown_file(file_path, config.to_dict())
            all_resources.update(resources)
            
            html_content = convert_markdown_to_html(processed_markdown, config.to_dict())
            enml_content, _ = process_html_to_enml(html_content, resources, config.to_dict())
            
            # Extract metadata from file
            metadata = extract_note_metadata(file_path, processed_markdown, config.to_dict())
            
            # Add frontmatter metadata (it takes precedence)
            for key, value in frontmatter.items():
                metadata[key] = value
            
            # Create note object
            title = metadata.get("title", Path(file_path).stem)
            created_date = metadata.get("created", metadata.get("file_created", datetime.datetime.now()))
            updated_date = metadata.get("updated", metadata.get("file_modified", created_date))
            tags = metadata.get("tags", [])
            
            # Set notebook based on folder_path
            notebook = note_info.get("folder_path", "Default")
            
            note = create_note_object(
                title=title,
                content=enml_content,
                resources=[],  # We'll add resources after processing them all
                config=config.to_dict(),
                created_date=created_date,
                updated_date=updated_date,
                tags=tags,
                notebook=notebook
            )
            
            processed_notes.append(note)
            note_info_list.append(note_info)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Process all resources
    print(f"Processing {len(all_resources)} resources...")
    resource_objects = process_resources(all_resources, config.to_dict())
    
    # Assign resources to notes
    print("Assigning resources to notes...")
    
    # Create mapping from file paths to resources
    resource_map = {}
    for resource in resource_objects:
        resource_map[resource['reference']] = resource
    
    # Add resources to each note
    for i, note_info in enumerate(note_info_list):
        if i < len(processed_notes):
            note = processed_notes[i]
            
            # Get resources for this note
            file_path = note_info['file_path']
            _, note_resources, _ = process_markdown_file(file_path, config.to_dict())
            
            # Add resources to note
            note_resource_objects = []
            for ref in note_resources:
                if ref in resource_map:
                    note_resource_objects.append(resource_map[ref])
            
            note['resources'] = note_resource_objects
    
    # Generate output with different grouping options
    print(f"\nGenerating ENEX output with '{group_by}' grouping...")
    output_files = generate_output(processed_notes, note_info_list, config.to_dict())
    
    # Print summary
    print("\nOutput files:")
    for group_name, output_path in output_files.items():
        file_size = Path(output_path).stat().st_size
        file_size_str = f"{file_size:,} bytes"
        print(f"  - {output_path} ({file_size_str})")
    
    print("\n" + "="*60)
    print(f"Success! Generated {len(output_files)} ENEX files")
    print("You can now import these files into Evernote")
    print("="*60)


if __name__ == "__main__":
    main()