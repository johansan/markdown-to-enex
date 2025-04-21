import argparse
import json
import sys
import datetime
import logging
from pathlib import Path

from .config import Config, ConfigError
from .scanner import scan_directory
from .markdown_processor import process_markdown_file
from .html_converter import convert_markdown_to_html
from .enml_processor import process_html_to_enml
from .resource_handler import process_resources
from .enex_generator import extract_note_metadata, create_note_object, generate_enex_file
from .enex_output import generate_output, get_best_group_by, ENEXOutputError


def main():
    """Main entry point for the Markdown to ENEX converter."""
    parser = argparse.ArgumentParser(description="Convert markdown files to Evernote ENEX format")
    parser.add_argument(
        "--config", 
        help="Path to custom configuration file"
    )
    parser.add_argument(
        "--source", 
        help="Path to source directory containing markdown files"
    )
    parser.add_argument(
        "--output", 
        help="Path to output ENEX file or directory"
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Only scan the directory structure without conversion"
    )
    parser.add_argument(
        "--test-convert",
        metavar="FILE",
        help="Test conversion on a single markdown file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--separate-files",
        action="store_true",
        help="Create separate ENEX files based on folder structure"
    )
    parser.add_argument(
        "--group-by",
        choices=["single", "top_folder", "full_folder", "notebook", "custom"],
        help="Grouping strategy for ENEX files (overrides --separate-files)"
    )
    parser.add_argument(
        "--max-notes",
        type=int,
        help="Maximum number of notes per ENEX file (0 for no limit)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = Config(args.config)
        
        # Override config with command line arguments if provided
        if args.source:
            config.set("source_directory", args.source)
        if args.output:
            config.set("output_directory", str(Path(args.output).parent if args.output.endswith(".enex") else args.output))
        
        # Enable verbose mode if requested
        verbose = args.verbose
        
        # Validate required configuration
        if not config.get("source_directory"):
            print("Error: Source directory not specified. Use --source or config file.")
            sys.exit(1)
            
        # Check if output is specified on command line or in config
        output_specified = args.output or (config.get("output_directory") and not args.test_convert)
        if not output_specified and not args.scan_only and not args.test_convert:
            print("Error: Output path not specified. Use --output or configure output_directory in config file.")
            sys.exit(1)
            
        # Print loaded configuration if verbose
        if verbose:
            print(f"Loaded configuration:")
            for key, value in config.to_dict().items():
                print(f"  {key}: {value}")
            
        # Scan the directory
        print(f"Scanning directory: {config.get('source_directory')}")
        scan_result = scan_directory(config.to_dict())
        
        print(f"Found {scan_result['total_notes']} notes and {scan_result['total_resources']} resources.")
        
        # Show planned ENEX files based on folder structure
        enex_files = {}
        for note in scan_result['notes']:
            enex_file = note['enex_filename']
            if enex_file not in enex_files:
                enex_files[enex_file] = []
            enex_files[enex_file].append(note)
        
        if verbose or args.separate_files:
            print("\nPlanned ENEX files based on folder structure:")
            for enex_file, notes in enex_files.items():
                print(f"  - {enex_file}: {len(notes)} notes")
        
        # If scan-only mode, print the structure and exit
        if args.scan_only:
            output_file = Path(config.get("output_directory", ".")) / "scan_result.json"
            with open(output_file, "w") as f:
                json.dump(scan_result, f, indent=2)
            print(f"Scan result saved to: {output_file}")
            return
            
        # Test conversion on a single file if requested
        if args.test_convert:
            test_file = args.test_convert
            print(f"Testing conversion on: {test_file}")
            
            try:
                # Process markdown
                processed_markdown, resources, frontmatter, image_registry = process_markdown_file(test_file, config.to_dict())
                print(f"Processed markdown and found {len(resources)} resource references")
                print(f"Extracted metadata: {frontmatter}")
                
                # Convert to HTML
                html_content = convert_markdown_to_html(processed_markdown, config.to_dict())
                
                # Process HTML to ENML with image registry
                enml_content, _ = process_html_to_enml(html_content, resources, config.to_dict(), image_registry)
                
                # Save the results
                output_dir = Path(config.get("output_directory", "."))
                base_name = Path(test_file).stem
                
                md_output = output_dir / f"{base_name}_processed.md"
                html_output = output_dir / f"{base_name}.html"
                
                with open(md_output, "w", encoding="utf-8") as f:
                    f.write(processed_markdown)
                    
                with open(html_output, "w", encoding="utf-8") as f:
                    f.write(html_content)
                    
                print(f"Processed markdown saved to: {md_output}")
                print(f"HTML content saved to: {html_output}")
                
            except Exception as e:
                print(f"Error converting file: {e}")
                
            return
        
        # Configure output options
        if "output_options" not in config.to_dict():
            config.set("output_options", {})
            
        # Determine output path and directory
        if args.output:
            # Command-line output takes precedence
            output_path = args.output
            output_dir = Path(output_path).parent if output_path.endswith(".enex") else Path(output_path)
            config.set("output_directory", str(output_dir))
        else:
            # Use output directory from config
            output_dir = Path(config.get("output_directory", "."))
            # For backward compatibility with code that expects output_path
            output_path = str(output_dir / "notes.enex")
        
        # Determine grouping strategy
        # Start with the config value if it exists
        group_by = config.get("output_options", {}).get("group_by", "single")
        
        # Command line arguments override config file
        if args.group_by:
            group_by = args.group_by
        elif args.separate_files:
            # Get best grouping strategy based on folder structure
            folder_structure = scan_result.get("folder_structure", {})
            group_by = get_best_group_by(folder_structure)
            print(f"Using auto-detected grouping strategy: {group_by}")
        
        # Set output options
        output_options = config.get("output_options")
        output_options["group_by"] = group_by
        output_options["progress_reporting"] = verbose
        
        # Set max notes per file if specified
        if args.max_notes is not None:
            output_options["max_notes_per_file"] = args.max_notes
            
        # Update config with output options
        config.set("output_options", output_options)
            
        # Setup logging if verbose
        if verbose:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
            
        # Full conversion process
        print("Starting full conversion process...")
        
        # Process all notes
        final_notes = []
        all_resources = set()
        
        # Track processed notes for output module
        processed_notes = []
        note_count = 0
        resource_count = 0
        
        print(f"Processing {scan_result['total_notes']} notes...")
        for note_info in scan_result['notes']:
            note_count += 1
            file_path = note_info['file_path']
            if verbose:
                print(f"  Processing note {note_count}/{scan_result['total_notes']}: {Path(file_path).name}")
            
            # Process markdown
            try:
                processed_markdown, resources, frontmatter, image_registry = process_markdown_file(file_path, config.to_dict())
                
                # Track all resources
                all_resources.update(resources)
                resource_count += len(resources)
                
                # Convert to HTML
                html_content = convert_markdown_to_html(processed_markdown, config.to_dict())
                
                # Process HTML to ENML with image registry
                enml_content, _ = process_html_to_enml(html_content, resources, config.to_dict(), image_registry)
                
                # Extract metadata from file
                metadata = extract_note_metadata(file_path, processed_markdown, config.to_dict())
                
                # Override with frontmatter metadata (it takes precedence)
                for key, value in frontmatter.items():
                    # Special handling for string dates that didn't parse properly
                    if key in ('created', 'updated', 'date') and isinstance(value, str):
                        try:
                            # Try to use the ENEX generator's date parser
                            from .enex_generator import ENEXGenerator
                            generator = ENEXGenerator(config.to_dict())
                            parsed_date = generator._parse_date(value)
                            metadata[key] = parsed_date
                        except Exception:
                            # If parsing fails, keep the string value
                            metadata[key] = value
                    else:
                        metadata[key] = value
                
                # Create a note object
                title = metadata.get("title", Path(file_path).stem)
                created_date = metadata.get("created", metadata.get("file_created", datetime.datetime.now()))
                updated_date = metadata.get("updated", metadata.get("file_modified", created_date))
                tags = metadata.get("tags", [])
                
                # Add folder information as notebook if specified
                notebook = None
                if note_info.get("folder_path"):
                    notebook = note_info.get("folder_path")
                
                note = create_note_object(
                    title=title,
                    content=enml_content,
                    resources=[],  # We'll add resources in the next step
                    config=config.to_dict(),
                    created_date=created_date,
                    updated_date=updated_date,
                    tags=tags,
                    notebook=notebook
                )
                
                processed_notes.append((note, resources, note_info))
                
            except Exception as e:
                print(f"  Error processing note {file_path}: {e}")
        
        print(f"Processed {note_count} notes with {resource_count} total resource references")
        
        # Process all resources
        print(f"Processing resources...")
        resource_objects = process_resources(all_resources, config.to_dict())
        print(f"Processed {len(resource_objects)} unique resources")
        
        # Create a lookup map for resources
        resource_map = {}
        for resource in resource_objects:
            resource_map[resource['reference']] = resource
        
        # Build final notes with resources
        print(f"Building final notes with resources...")
        final_notes = []
        note_info_list = []
        
        for note, note_resources, note_info in processed_notes:
            # Add only the resources referenced by this note
            note_resource_objects = []
            for ref in note_resources:
                if ref in resource_map:
                    note_resource_objects.append(resource_map[ref])
            
            note['resources'] = note_resource_objects
            final_notes.append(note)
            note_info_list.append(note_info)
            
            # Count resources for reporting
            if verbose:
                print(f"  Note '{note['title']}' with {len(note_resource_objects)} resources")
        
        # Generate ENEX output
        print(f"Generating ENEX output...")
        try:
            # Use new ENEX output module to generate files
            output_files = generate_output(final_notes, note_info_list, config.to_dict())
            
            # Print summary
            print(f"\nSuccessfully created {len(output_files)} ENEX files:")
            for group_name, output_path in output_files.items():
                file_size = Path(output_path).stat().st_size
                print(f"  - {output_path} ({file_size:,} bytes)")
                
            print(f"\nYou can now import these files into Evernote.")
            
        except ENEXOutputError as e:
            print(f"Error generating ENEX output: {e}")
            sys.exit(1)
            
    except ConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()