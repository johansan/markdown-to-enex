import os
import mimetypes
import hashlib
import base64
import uuid
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional
import datetime

# Add conditional PIL import
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ResourceHandler:
    """Handles the processing of resources for ENEX conversion."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the resource handler.
        
        Args:
            config: Configuration dictionary containing resource handling options
        """
        self.config = config
        self.source_dir = config.get("source_directory", "")
        if self.source_dir:
            self.source_dir = Path(self.source_dir)
            
        # Resource options
        self.resource_options = config.get("resource_options", {})
        self.max_resource_size = self.resource_options.get("max_resource_size", 50 * 1024 * 1024)  # 50MB default
        self.include_resource_attributes = self.resource_options.get("include_resource_attributes", True)
        self.include_unknown_resources = self.resource_options.get("include_unknown_resources", True)
        
        # Initialize resource maps
        self.resource_map: Dict[str, Dict[str, Any]] = {}
        self.reference_map: Dict[str, str] = {}
        
        # Add known MIME types
        self._initialize_mime_types()
        
    def _initialize_mime_types(self):
        """Initialize additional MIME types."""
        mimetypes.init()
        
        # Add common MIME types that might be missing
        additional_types = {
            '.heic': 'image/heic',
            '.heif': 'image/heif',
            '.webp': 'image/webp',
            '.md': 'text/markdown',
            '.yaml': 'application/x-yaml',
            '.yml': 'application/x-yaml',
            '.epub': 'application/epub+zip',
            '.mobi': 'application/x-mobipocket-ebook',
            '.azw': 'application/vnd.amazon.ebook',
            '.psd': 'application/vnd.adobe.photoshop',
            '.ai': 'application/pdf',  # Often AI files are PDF compatible
            '.sketch': 'application/octet-stream',  # No official MIME type
            '.numbers': 'application/vnd.apple.numbers',
            '.pages': 'application/vnd.apple.pages',
            '.key': 'application/vnd.apple.keynote',
        }
        
        for ext, mime_type in additional_types.items():
            mimetypes.add_type(mime_type, ext)
    
    def process_resources(self, resource_refs: Set[str]) -> List[Dict[str, Any]]:
        """Process a set of resource references.
        
        Args:
            resource_refs: Set of resource references to process
            
        Returns:
            List of processed resource information dictionaries
        """
        # Clear existing maps
        self.resource_map = {}
        self.reference_map = {}
        
        for resource_ref in resource_refs:
            # Find the resource file
            resource_path = self._find_resource_path(resource_ref)
            
            # Skip if resource not found and we're not including unknown resources
            if not resource_path or not resource_path.exists():
                error_msg = f"Resource not found: {resource_ref}"
                if not self.include_unknown_resources:
                    print(f"Warning: {error_msg}")
                    continue
                else:
                    # Create a placeholder for missing resources
                    placeholder = self._create_placeholder_resource(resource_ref)
                    self.resource_map[resource_ref] = placeholder
                    continue
                    
            try:
                # Process resource
                resource_info = self._process_resource_file(resource_path, resource_ref)
                
                # Store in resource map
                self.resource_map[resource_ref] = resource_info
                
                # Create reference mapping
                self.reference_map[resource_path.name] = resource_ref
                
            except Exception as e:
                print(f"Error processing resource {resource_ref}: {e}")
        
        # Return list of resource info
        return list(self.resource_map.values())
    
    def get_resource_map(self) -> Dict[str, Dict[str, Any]]:
        """Get the resource map.
        
        Returns:
            Dictionary mapping resource references to resource information
        """
        return self.resource_map
    
    def get_reference_map(self) -> Dict[str, str]:
        """Get the reference map.
        
        Returns:
            Dictionary mapping resource filenames to resource references
        """
        return self.reference_map
    
    def get_resource_by_reference(self, reference: str) -> Optional[Dict[str, Any]]:
        """Get resource information by reference.
        
        Args:
            reference: Resource reference
            
        Returns:
            Resource information dictionary or None if not found
        """
        # Direct lookup
        if reference in self.resource_map:
            return self.resource_map[reference]
            
        # Try filename lookup
        filename = Path(reference).name
        if filename in self.reference_map:
            ref = self.reference_map[filename]
            return self.resource_map.get(ref)
            
        return None
    
    def generate_resource_xml(self, resource_info: Dict[str, Any]) -> str:
        """Generate XML structure for a resource.
        
        Args:
            resource_info: Resource information dictionary
            
        Returns:
            XML string for the resource
        """
        mime_type = resource_info.get("mime", "application/octet-stream")
        data_base64 = resource_info.get("data", "")
        md5_hash = resource_info.get("hash", "")
        filename = resource_info.get("filename", "")
        
        xml = f"    <resource>\n"
        xml += f"      <data encoding=\"base64\">{data_base64}</data>\n"
        xml += f"      <mime>{mime_type}</mime>\n"
        
        if self.include_resource_attributes and filename:
            xml += f"      <resource-attributes>\n"
            xml += f"        <file-name>{filename}</file-name>\n"
            xml += f"      </resource-attributes>\n"
            
        xml += f"    </resource>\n"
        
        return xml
    
    def _find_resource_path(self, resource_ref: str) -> Optional[Path]:
        """Find the full path for a resource reference.
        
        Args:
            resource_ref: Resource reference (filename or path)
            
        Returns:
            Full path to the resource or None if not found
        """
        # First try direct path
        if self.source_dir:
            # Look directly in source directory for the resource
            resource_path = self.source_dir / resource_ref
            if resource_path.exists():
                return resource_path
                
            # Look in source dir (for absolute paths)
            resource_path = self.source_dir / resource_ref
            if resource_path.exists():
                return resource_path
                
        # Check if it's a direct path
        direct_path = Path(resource_ref)
        if direct_path.exists():
            return direct_path
            
        # Check if it's relative to current directory
        current_path = Path.cwd() / resource_ref
        if current_path.exists():
            return current_path
            
        # Try just the filename in source directory
        if self.source_dir:
            filename = Path(resource_ref).name
            resource_path = self.source_dir / filename
            if resource_path.exists():
                return resource_path
                
        return None
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Determine MIME type for a file based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            return mime_type
            
        # Default based on category
        extension = file_path.suffix.lower()
        
        # Image formats
        if extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']:
            return f"image/{extension[1:]}"
            
        # Audio formats
        if extension in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']:
            return f"audio/{extension[1:]}"
            
        # Video formats
        if extension in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']:
            return f"video/{extension[1:]}"
            
        # Document formats
        if extension in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
            return "application/octet-stream"
            
        # Default fallback
        return "application/octet-stream"
    
    def _get_image_dimensions(self, file_path: Path) -> Optional[Tuple[int, int]]:
        """Get image dimensions using PIL.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Tuple of (width, height) in pixels or None if dimensions cannot be determined
        """
        if not PIL_AVAILABLE:
            # Don't print warning here, let caller handle it if needed
            return None
            
        try:
            with Image.open(file_path) as img:
                return img.size
        except Exception as e:
            # Print a warning but don't stop execution
            print(f"Warning: Could not read dimensions for image {file_path.name}: {e}")
            return None
    
    def _process_resource_file(self, file_path: Path, resource_ref: str) -> Dict[str, Any]:
        """Process a resource file.
        
        Args:
            file_path: Path to the resource file
            resource_ref: Original resource reference
            
        Returns:
            Resource information dictionary
        """
        # Check file size
        file_stat = file_path.stat()
        file_size = file_stat.st_size
        file_timestamp = datetime.datetime.fromtimestamp(file_stat.st_mtime) # Get timestamp

        if file_size > self.max_resource_size:
            print(f"Warning: Resource {resource_ref} exceeds maximum size limit ({file_size} bytes)")
            return self._create_placeholder_resource(resource_ref)
            
        # Read file content
        with open(file_path, 'rb') as f:
            data = f.read()
            
        # Calculate MD5 hash
        md5_hash = hashlib.md5(data).hexdigest()
        
        # Determine MIME type
        mime_type = self._get_mime_type(file_path)
        
        # Convert to base64
        data_base64 = base64.b64encode(data).decode('utf-8')
        
        # Create resource info dictionary first
        resource_info = {
            "data": data_base64,
            "mime": mime_type,
            "hash": md5_hash,
            "filename": file_path.name,
            "size": file_size,
            "timestamp": file_timestamp, # Add timestamp
            "reference": resource_ref
        }

        # Get dimensions if it's an image
        if mime_type.startswith('image/'):
            dimensions = self._get_image_dimensions(file_path)
            if dimensions:
                width, height = dimensions
                resource_info['width'] = width
                resource_info['height'] = height
        
        return resource_info
    
    def _create_placeholder_resource(self, resource_ref: str) -> Dict[str, Any]:
        """Create a placeholder for a missing resource.
        
        Args:
            resource_ref: Resource reference
            
        Returns:
            Placeholder resource information
        """
        # Generate placeholder data (a simple transparent 1x1 pixel PNG)
        placeholder_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        )
        
        # Calculate hash
        md5_hash = hashlib.md5(placeholder_data).hexdigest()
        
        # Determine type (assume image for simplicity)
        mime_type = "image/png"
        filename = Path(resource_ref).name
        
        # Convert to base64
        data_base64 = base64.b64encode(placeholder_data).decode('utf-8')
        
        # Create resource info
        return {
            "data": data_base64,
            "mime": mime_type,
            "hash": md5_hash,
            "filename": filename,
            "size": len(placeholder_data),
            "reference": resource_ref,
            "placeholder": True
        }


def process_resources(resource_refs: Set[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process resources for ENEX conversion.
    
    Args:
        resource_refs: Set of resource references to process
        config: Configuration dictionary
        
    Returns:
        List of processed resource information dictionaries
    """
    handler = ResourceHandler(config)
    return handler.process_resources(resource_refs)