#!/usr/bin/env python3
"""
Example script demonstrating the resource handler.

Usage:
    python resource_handler_example.py /path/to/resources/folder resource1.png resource2.jpg ...
"""

import sys
from pathlib import Path
import pprint

# Add the parent directory to the path to import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from markdown_to_enex import ResourceHandler


def main():
    """Process resources using the ResourceHandler."""
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} /path/to/resources/folder resource1.png resource2.jpg ...")
        sys.exit(1)
        
    resources_dir = sys.argv[1]
    resource_refs = set(sys.argv[2:])
    
    # Configuration
    config = {
        "source_directory": resources_dir,
        "resources_directory": ".",  # Resources are in the specified folder directly
        "resource_options": {
            "max_resource_size": 10 * 1024 * 1024,  # 10MB
            "include_resource_attributes": True,
            "include_unknown_resources": True
        }
    }
    
    print(f"Processing resources in {resources_dir}...")
    
    try:
        # Initialize resource handler
        handler = ResourceHandler(config)
        
        # Process resources
        resources = handler.process_resources(resource_refs)
        
        # Print resource information (excluding base64 data for brevity)
        print(f"\nProcessed {len(resources)} resources:")
        for i, resource in enumerate(resources, 1):
            # Create a copy without the base64 data for display
            display_info = resource.copy()
            if "data" in display_info:
                data_length = len(display_info["data"])
                display_info["data"] = f"<{data_length} bytes of base64 data>"
                
            print(f"\nResource {i}:")
            pprint.pprint(display_info)
            
        # Generate XML for one resource as an example
        if resources:
            print("\nExample resource XML:")
            xml = handler.generate_resource_xml(resources[0])
            print(xml)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()