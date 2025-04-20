#!/usr/bin/env python3
"""
Example script demonstrating the use of the directory scanner.

Usage:
    python scanner_example.py /path/to/markdown/notes
"""

import json
import sys
from pathlib import Path

# Add the parent directory to the path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from markdown_to_enex import Config, scan_directory


def main():
    """Run the directory scanner example."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/markdown/notes")
        sys.exit(1)
        
    source_dir = sys.argv[1]
    
    # Create a configuration with just the source directory
    config = {
        "source_directory": source_dir,
        "resources_directory": "_resources"
    }
    
    print(f"Scanning directory: {source_dir}")
    
    # Scan the directory
    try:
        result = scan_directory(config)
        
        # Print summary
        print(f"\nScan Results:")
        print(f"  Total notes: {result['total_notes']}")
        print(f"  Total resources: {result['total_resources']}")
        print(f"\nDirectory Structure:")
        
        for dir_path, notes in result['directory_structure'].items():
            if dir_path:
                print(f"  {dir_path}/")
            else:
                print(f"  (root)/")
                
            for note in notes:
                print(f"    - {note}")
                
        # Save the full result to a JSON file
        output_file = Path("scan_result.json")
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
            
        print(f"\nDetailed scan result saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()