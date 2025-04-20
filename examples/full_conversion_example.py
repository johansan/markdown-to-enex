#!/usr/bin/env python3
"""
Example script demonstrating the complete markdown to HTML conversion process.

Usage:
    python full_conversion_example.py /path/to/markdown/file.md
"""

import sys
from pathlib import Path

# Add the parent directory to the path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from markdown_to_enex import process_markdown_file, convert_markdown_to_html


def main():
    """Run the full conversion example."""
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
            "handle_special_chars": True,
            "preserve_image_markdown": False,
            "preserve_link_markdown": False
        },
        "html_options": {
            "markdown_engine": "python-markdown",  # Use the installed library
            "enable_tables": True,
            "enable_fenced_code": True,
            "create_full_document": True,
            "document_title": "Converted Note"
        }
    }
    
    print(f"Processing markdown file: {md_file}")
    
    try:
        # Step 1: Process markdown
        print("\nStep 1: Processing markdown...")
        processed_markdown, resources = process_markdown_file(md_file, config)
        print(f"Found {len(resources)} resource references")
        
        if resources:
            print("Resources:")
            for res in resources:
                print(f"  - {res}")
        
        # Step 2: Convert to HTML
        print("\nStep 2: Converting to HTML...")
        html_content = convert_markdown_to_html(processed_markdown, config)
        print(f"Generated {len(html_content)} bytes of HTML")
        
        # Save the results
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        md_output = output_dir / f"{Path(md_file).stem}_processed.md"
        html_output = output_dir / f"{Path(md_file).stem}.html"
        
        with open(md_output, "w", encoding="utf-8") as f:
            f.write(processed_markdown)
            
        with open(html_output, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"\nResults saved to:")
        print(f"  Processed markdown: {md_output}")
        print(f"  HTML content: {html_output}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()