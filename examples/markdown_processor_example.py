#!/usr/bin/env python3
"""
Example script demonstrating the use of the markdown processor.

Usage:
    python markdown_processor_example.py /path/to/markdown/file.md
"""

import json
import sys
from pathlib import Path

# Add the parent directory to the path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from markdown_to_enex import Config, process_markdown_file


def main():
    """Run the markdown processor example."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/markdown/file.md")
        sys.exit(1)
        
    md_file = sys.argv[1]
    
    # Create a configuration with default options
    config = {
        "resources_directory": "_resources",
        "processing_options": {
            "remove_code_block_markers": True,
            "convert_inline_code": True,
            "remove_heading_markers": True,
            "handle_image_references": True,
            "process_links": True,
            "handle_special_chars": True
        }
    }
    
    print(f"Processing markdown file: {md_file}")
    
    try:
        # Process the markdown file
        processed_content, resources = process_markdown_file(md_file, config)
        
        # Display the results
        print("\nProcessed Content:")
        print("----------------")
        print(processed_content)
        
        print("\nResource References:")
        print("------------------")
        for resource in resources:
            print(f"  - {resource}")
            
        # Save the processed content to a file
        output_file = Path(md_file).with_suffix('.processed.txt')
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(processed_content)
            
        print(f"\nProcessed content saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()