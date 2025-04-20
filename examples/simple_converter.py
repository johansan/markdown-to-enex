#!/usr/bin/env python3
"""
Simple script to convert a markdown file to HTML.

Usage:
    python simple_converter.py /path/to/file.md
"""

import sys
from pathlib import Path

# Add the parent directory to the path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from markdown_to_enex import process_markdown_file, convert_markdown_to_html


def main():
    """Convert a markdown file to HTML using the markdown-to-enex converter."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/file.md")
        sys.exit(1)
        
    md_file = sys.argv[1]
    
    # Simple configuration
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
            "markdown_engine": "python-markdown",
            "enable_tables": True,
            "enable_fenced_code": True,
            "create_full_document": True
        }
    }
    
    print(f"Converting {md_file} to HTML...")
    
    try:
        # Process markdown
        processed_markdown, resources = process_markdown_file(md_file, config)
        
        # Convert to HTML
        html_content = convert_markdown_to_html(processed_markdown, config)
        
        # Save output
        output_file = Path(md_file).with_suffix('.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"Conversion successful! Output saved to {output_file}")
        print(f"Found {len(resources)} resource references")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()