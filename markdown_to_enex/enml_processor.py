import re
import hashlib
import base64
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional
from xml.sax.saxutils import escape
import html


class ENMLProcessor:
    """Processes HTML content to make it compatible with ENEX/ENML format."""
    
    # ENML permitted elements
    PERMITTED_ELEMENTS = {
        'a', 'abbr', 'acronym', 'address', 'area', 'b', 'bdo', 'big', 'blockquote',
        'br', 'caption', 'center', 'cite', 'code', 'col', 'colgroup', 'dd', 'del',
        'dfn', 'div', 'dl', 'dt', 'em', 'font', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'hr', 'i', 'img', 'ins', 'kbd', 'li', 'map', 'ol', 'p', 'pre', 'q', 's', 
        'samp', 'small', 'span', 'strike', 'strong', 'sub', 'sup', 'table', 'tbody', 
        'td', 'tfoot', 'th', 'thead', 'title', 'tr', 'tt', 'u', 'ul', 'var', 'xmp'
    }
    
    # ENML prohibited elements
    PROHIBITED_ELEMENTS = {
        'applet', 'base', 'basefont', 'bgsound', 'blink', 'body', 'button', 'dir', 
        'embed', 'fieldset', 'form', 'frame', 'frameset', 'head', 'html', 'iframe', 
        'ilayer', 'input', 'isindex', 'label', 'layer', 'legend', 'link', 'marquee', 
        'menu', 'meta', 'noframes', 'noscript', 'object', 'optgroup', 'option', 
        'param', 'plaintext', 'script', 'select', 'style', 'textarea', 'xml'
    }
    
    # ENML prohibited attributes
    PROHIBITED_ATTRIBUTES = {
        'id', 'class', 'onclick', 'ondblclick', 'accesskey', 'data', 'dynsrc', 'tabindex'
    }
    
    # Add all event handlers (on*)
    PROHIBITED_ATTRIBUTES.update({f'on{evt}' for evt in [
        'abort', 'blur', 'change', 'click', 'dblclick', 'error', 'focus', 'keydown',
        'keypress', 'keyup', 'load', 'mousedown', 'mousemove', 'mouseout', 'mouseover',
        'mouseup', 'reset', 'resize', 'scroll', 'select', 'submit', 'unload'
    ]})
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the ENML processor.
        
        Args:
            config: Configuration dictionary containing processing options
        """
        self.config = config
        self.resources_dir = Path(config.get("resources_directory", "_resources"))
        
        # Get base source directory for resolving resource paths
        self.source_dir = config.get("source_directory", "")
        if self.source_dir:
            self.source_dir = Path(self.source_dir)
            
        self.resource_map: Dict[str, Dict[str, Any]] = {}
        self.enml_options = config.get("enml_options", {})
        
    def process_html_to_enml(self, html_content: str, resource_refs: Set[str]) -> Tuple[str, List[Dict[str, Any]]]:
        """Convert HTML content to ENML format suitable for Evernote.
        
        Args:
            html_content: HTML content to process
            resource_refs: Set of resource references found in the content
            
        Returns:
            Tuple of (enml_content, resources list)
        """
        # Process resources
        self._prepare_resources(resource_refs)
        
        # Clean HTML content
        cleaned_html = self._clean_html(html_content)
        
        # Process image references
        processed_html = self._process_image_references(cleaned_html)
        
        # Convert to Evernote-style formatting
        processed_html = self._convert_to_evernote_format(processed_html)
        
        # Wrap in en-note with CDATA and inner XML declaration (without linebreaks)
        inner_xml = f'<?xml version="1.0" encoding="UTF-8" standalone="no"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd"><en-note>{processed_html}</en-note>'
        enml_content = f'<![CDATA[{inner_xml}]]>'
        
        # Return ENML content and resources
        return enml_content, list(self.resource_map.values())
    
    def _prepare_resources(self, resource_refs: Set[str]) -> None:
        """Prepare resources for inclusion in ENEX.
        
        Args:
            resource_refs: Set of resource references found in the content
        """
        self.resource_map = {}
        
        for resource_ref in resource_refs:
            # Find the resource file
            resource_path = self._find_resource_path(resource_ref)
            
            if not resource_path or not resource_path.exists():
                print(f"Warning: Resource not found: {resource_ref}")
                continue
                
            try:
                # Read resource data
                with open(resource_path, 'rb') as f:
                    data = f.read()
                    
                # Calculate MD5 hash
                md5_hash = hashlib.md5(data).hexdigest()
                
                # Determine MIME type
                mime_type = self._get_mime_type(resource_path)
                
                # Convert to base64
                data_base64 = base64.b64encode(data).decode('utf-8')
                
                # Store in resource map
                self.resource_map[resource_ref] = {
                    'data': data_base64,
                    'mime': mime_type,
                    'hash': md5_hash,
                    'filename': resource_path.name
                }
                
            except Exception as e:
                print(f"Error processing resource {resource_ref}: {e}")
    
    def _find_resource_path(self, resource_ref: str) -> Optional[Path]:
        """Find the full path for a resource reference.
        
        Args:
            resource_ref: Resource reference (filename or path)
            
        Returns:
            Full path to the resource or None if not found
        """
        # First try direct path
        if self.source_dir:
            # Look in resources directory relative to source
            resource_path = self.source_dir / self.resources_dir / resource_ref
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
        current_path = Path.cwd() / self.resources_dir / resource_ref
        if current_path.exists():
            return current_path
            
        return None
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Determine MIME type for a file based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        extension = file_path.suffix.lower()
        
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.mp3': 'audio/mpeg',
            '.mp4': 'video/mp4',
            '.wav': 'audio/wav',
            '.ogg': 'audio/ogg',
            '.txt': 'text/plain',
            '.zip': 'application/zip',
            '.html': 'text/html',
            '.csv': 'text/csv'
        }
        
        return mime_types.get(extension, 'application/octet-stream')
    
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content to be ENML-compatible.
        
        Args:
            html_content: HTML content to clean
            
        Returns:
            Cleaned HTML
        """
        # Use a simple regex-based approach for cleaning
        # For a more robust solution, a proper HTML parser would be better
        
        result = html_content
        
        # Remove doctype
        result = re.sub(r'<!DOCTYPE[^>]*>', '', result)
        
        # Remove html and body tags
        result = re.sub(r'<html[^>]*>|</html>|<body[^>]*>|</body>', '', result)
        
        # Remove prohibited elements with their content
        for element in self.PROHIBITED_ELEMENTS:
            result = re.sub(f'<{element}[^>]*>.*?</{element}>', '', result, flags=re.DOTALL)
            result = re.sub(f'<{element}[^>]*/?>', '', result)
        
        # Fix unclosed tags (img, br, hr)
        result = re.sub(r'<(img|br|hr)([^>]*)(?<!\/)>', r'<\1\2/>', result)
        
        # Fix quotes in attribute values
        def fix_quotes(match):
            attr_value = match.group(2)
            attr_value = attr_value.replace('"', "&quot;")
            attr_value = attr_value.replace("'", "&apos;")
            return f'{match.group(1)}="{attr_value}"'
            
        result = re.sub(r'([a-zA-Z0-9_-]+)=["\'](.*?)["\']', fix_quotes, result)
        
        # Remove prohibited attributes
        for attr in self.PROHIBITED_ATTRIBUTES:
            result = re.sub(f' {attr}=["\'"][^\'"]*["\']', '', result)
        
        # Fix any malformed tags
        result = re.sub(r'<(?!/)([a-z0-9]+)(?:\s+[^>]*)?(?<![/\"])>', r'<\1>', result)
        
        # Ensure proper entity encoding for special characters
        result = result.replace('&nbsp;', '&#160;')
        
        return result
    
    def _process_image_references(self, html_content: str) -> str:
        """Convert HTML img tags to ENML en-media tags.
        
        Args:
            html_content: HTML content with img tags
            
        Returns:
            HTML content with en-media tags
        """
        def replace_img(match):
            src = match.group(1)
            attrs = match.group(2) or ''
            
            # Skip external images (keep as is)
            if src.startswith(('http://', 'https://')):
                return match.group(0)
                
            # Get resource info
            resource_info = self.resource_map.get(src)
            
            if not resource_info:
                # Try to find by basename
                src_basename = Path(src).name
                for ref, info in self.resource_map.items():
                    if Path(ref).name == src_basename:
                        resource_info = info
                        break
            
            if resource_info:
                # Extract width, height, and alt attributes
                width_match = re.search(r'width=["\'](.*?)["\']', attrs)
                height_match = re.search(r'height=["\'](.*?)["\']', attrs)
                alt_match = re.search(r'alt=["\'](.*?)["\']', attrs)
                
                width = f' width="{width_match.group(1)}"' if width_match else ''
                height = f' height="{height_match.group(1)}"' if height_match else ''
                alt = f' alt="{alt_match.group(1)}"' if alt_match else ''
                
                return f'<en-media type="{resource_info["mime"]}" hash="{resource_info["hash"]}"{width}{height}{alt}/>'
            else:
                print(f"Warning: Resource not found for image: {src}")
                return f'<span style="color:red;">[Image not found: {html.escape(src)}]</span>'
                
        # Replace img tags
        result = re.sub(r'<img\s+src=["\'](.*?)["\'](.*?)/?>', replace_img, html_content)
        
        return result
    
    def _convert_to_evernote_format(self, html_content: str) -> str:
        """Convert HTML to Evernote's specific format.
        
        Args:
            html_content: HTML content to convert
            
        Returns:
            Converted HTML in Evernote's format
        """
        # 1. Convert paragraph tags to div tags (but keep list items as-is)
        result = re.sub(r'<p>(.*?)</p>', r'<div>\1</div>', html_content, flags=re.DOTALL)
        
        # 2. Convert plain URLs to hyperlinks
        # Find URLs not already in hyperlinks
        def url_to_link(match):
            url = match.group(0)
            # Don't convert if already inside a link or HTML tag
            pre_char = match.string[max(0, match.start() - 1):match.start()]
            if pre_char == '"' or pre_char == "'":
                return url
            return f'<a href="{url}" rev="en_rl_none">{url}</a>'
            
        # Match URLs not already in a link
        url_pattern = r'(?<!["\'=])(https?://[^\s<>"\']+)'
        result = re.sub(url_pattern, url_to_link, result)
        
        # 3. Add proper <br/> spacing between content blocks
        # Add <div><br/></div> after each </div> if not followed by another tag
        result = re.sub(r'</div>(?!\s*<)', r'</div><div><br/></div>', result)
        
        # 4. Process markdown image references for remaining unprocessed images
        # Look for markdown style images: ![[path/to/image.jpg]]
        def replace_markdown_image(match):
            img_path = match.group(1)
            resource_info = None
            
            # Try to find resource in our resource map
            for ref, info in self.resource_map.items():
                if Path(ref).name == Path(img_path).name:
                    resource_info = info
                    break
            
            if resource_info:
                # Calculate image dimensions (default to 440x440 like in the example)
                width = "440px"
                height = "440px"
                alt = Path(img_path).stem.replace('_', ' ')
                
                return f'<en-media style="--en-naturalWidth:440; --en-naturalHeight:440;" ' \
                       f'alt="{alt}" height="{height}" width="{width}" ' \
                       f'hash="{resource_info["hash"]}" type="{resource_info["mime"]}" />'
            else:
                return f'<div>[Image not found: {html.escape(img_path)}]</div>'
                
        result = re.sub(r'!\[\[([^\]]+)\]\]', replace_markdown_image, result)
        
        # 5. Add a <div><br/></div> at the beginning if not already present
        if not result.startswith('<div><br/></div>'):
            result = '<div><br/></div>' + result
        
        # 6. Add a <div><br/></div> at the end if not already present
        if not result.endswith('<div><br/></div>'):
            result = result + '<div><br/></div>'
            
        # 7. Remove any metadata block at the beginning (content between --- markers)
        result = re.sub(r'<div>-{3,}</div>.*?<div>-{3,}</div>', '<div><br/></div>', result, flags=re.DOTALL)
            
        # Final clean-up
        # Remove empty divs (except those with just <br/>)
        result = re.sub(r'<div>\s*</div>', '', result)
        
        # Ensure proper xml:lang attribute
        result = re.sub(r'<([a-z0-9]+) lang=', r'<\1 xml:lang=', result)
        
        # Normalize whitespace and remove unnecessary line breaks for cleaner XML
        # Remove all whitespace between tags
        result = re.sub(r'>\s+<', '><', result, flags=re.DOTALL)
        
        return result
        
    def _post_process_enml(self, enml_content: str) -> str:
        """Apply final post-processing to ENML content.
        
        Args:
            enml_content: ENML content to process
            
        Returns:
            Post-processed ENML content
        """
        # Ensure proper CDATA for scripts, if any survived
        result = re.sub(r'<script>(.*?)</script>', r'<script><![CDATA[\1]]></script>', enml_content, flags=re.DOTALL)
        
        # Ensure proper xml:lang attribute
        result = re.sub(r'<([a-z0-9]+) lang=', r'<\1 xml:lang=', result)
        
        # Normalize whitespace and remove unnecessary line breaks for cleaner XML
        # Remove all whitespace between tags
        result = re.sub(r'>\s+<', '><', result, flags=re.DOTALL)
        
        return result


def process_html_to_enml(html_content: str, resource_refs: Set[str], config: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    """Convert HTML content to ENML format for ENEX export.
    
    Args:
        html_content: HTML content to process
        resource_refs: Set of resource references found in the content
        config: Configuration dictionary
        
    Returns:
        Tuple of (enml_content, resources list)
    """
    processor = ENMLProcessor(config)
    return processor.process_html_to_enml(html_content, resource_refs)