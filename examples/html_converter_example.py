#!/usr/bin/env python3
"""
Example script demonstrating the use of the HTML converter.

Usage:
    python html_converter_example.py /path/to/markdown/file.md
"""

import sys
import json
from pathlib import Path

# Add the parent directory to the path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from markdown_to_enex import process_markdown_file, convert_markdown_to_html


def main():
    """Run the HTML converter example."""
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
        },
        "html_options": {
            "markdown_engine": "basic",  # Use basic for compatibility
            "enable_tables": True,
            "enable_fenced_code": True,
            "create_full_document": False
        }
    }
    
    print(f"Processing markdown file: {md_file}")
    
    try:
        # First process the markdown file
        processed_markdown, resources = process_markdown_file(md_file, config)
        
        print("\nProcessed Markdown:")
        print("----------------")
        print(processed_markdown)
        
        # Then convert to HTML
        html_content = convert_markdown_to_html(processed_markdown, config)
        
        print("\nHTML Content:")
        print("------------")
        print(html_content)
        
        # Save the HTML to a file
        output_file = Path(md_file).with_suffix('.html')
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"\nHTML content saved to: {output_file}")
        
        # Print resource references
        print("\nResource References:")
        print("------------------")
        for resource in resources:
            print(f"  - {resource}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()