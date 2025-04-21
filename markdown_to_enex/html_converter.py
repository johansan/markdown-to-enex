import re
import html
from typing import Dict, Any, Optional, Tuple, List

# Import markdown libraries directly since we're now requiring them as dependencies
import markdown
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
import commonmark


class HTMLConverter:
    """Converts processed markdown content to HTML for ENEX conversion."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the HTML converter.
        
        Args:
            config: Configuration dictionary containing HTML conversion options
        """
        self.config = config
        self.html_options = config.get("html_options", {})
        
        # Determine which markdown library to use
        self.markdown_engine = self.html_options.get("markdown_engine", "python-markdown")
        if self.markdown_engine == "auto":
            self.markdown_engine = "python-markdown"
                
        # Initialize extensions based on config
        self.extensions = []
        if self.markdown_engine == "python-markdown":
            if self.html_options.get("enable_tables", True):
                self.extensions.append(TableExtension())
            if self.html_options.get("enable_fenced_code", True):
                self.extensions.append(FencedCodeExtension())
                
        # Add custom converters for special markdown elements
        self.custom_converters = [
            self._convert_image_placeholders,
            self._convert_link_placeholders,
            self._fix_html_entities
        ]
        
    def convert_to_html(self, processed_markdown: str) -> str:
        """Convert processed markdown to HTML.
        
        Args:
            processed_markdown: Markdown content that has been pre-processed
            
        Returns:
            HTML content
        """
        # Check if the original content ends with a newline
        original_ends_with_newline = processed_markdown.endswith('\n')
        
        # Mark empty lines with placeholders
        marked_content = self._mark_empty_lines(processed_markdown)
        
        # Pre-process list patterns to ensure proper list rendering
        marked_content = self._process_text_with_lists(marked_content)
        
        # Convert to HTML using the selected markdown engine
        if self.markdown_engine == "python-markdown":
            html_content = markdown.markdown(
                marked_content,
                extensions=self.extensions,
                output_format='html5'
            )
        elif self.markdown_engine == "commonmark":
            parser = commonmark.Parser()
            ast = parser.parse(marked_content)
            renderer = commonmark.HtmlRenderer()
            html_content = renderer.render(ast)
        else:
            # Basic markdown conversion as fallback
            html_content = self._basic_markdown_to_html(marked_content)
            
        # Restore empty lines
        html_content = self._restore_empty_lines(html_content)
            
        # Apply custom converters for special elements
        for converter in self.custom_converters:
            html_content = converter(html_content)
            
        # Apply additional formatting for elements not handled by basic conversion
        html_content = self._convert_basic_formatting(html_content)
        
        # Wrap in HTML document structure if needed
        if self.html_options.get("create_full_document", False):
            html_content = self._create_html_document(html_content)
            
        return html_content
    
    def _mark_empty_lines(self, content: str) -> str:
        """Mark empty lines with special placeholders that survive markdown conversion.
        
        Args:
            content: The markdown content
            
        Returns:
            Content with empty lines marked with placeholders
        """
        lines = content.split('\n')
        for i in range(len(lines)):
            if not lines[i].strip():
                lines[i] = "<!-- empty-line-placeholder -->"
        return '\n'.join(lines)
    
    def _restore_empty_lines(self, html_content: str) -> str:
        """Replace empty line placeholders with proper HTML breaks.
        
        Args:
            html_content: HTML content with placeholders
            
        Returns:
            HTML content with proper empty line breaks
        """
        return html_content.replace("<!-- empty-line-placeholder -->", "<div><br/></div>")
        
    def _process_text_with_lists(self, markdown_content: str) -> str:
        """Ensure list items are properly formatted for better Markdown conversion.
        
        Args:
            markdown_content: Markdown content to process
            
        Returns:
            Processed markdown with improved list formatting
        """
        lines = markdown_content.split('\n')
        result_lines = []
        
        # Add an extra newline before lists to ensure they're recognized as lists
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            
            # If this is a list item and the previous line wasn't blank,
            # add a blank line to ensure the list is properly recognized
            if i > 0 and (stripped.startswith('- ') or stripped.startswith('* ')) and lines[i-1].strip():
                # Only add a blank line if the previous line isn't already blank
                # and isn't a list item itself
                prev_stripped = lines[i-1].lstrip()
                if not (prev_stripped.startswith('- ') or prev_stripped.startswith('* ')):
                    result_lines.append('')
                    
            result_lines.append(line)
            
        return '\n'.join(result_lines)
        
    def _basic_markdown_to_html(self, markdown_content: str) -> str:
        """Provide a basic markdown to HTML conversion using regex.
        
        This is a fallback when no markdown library is available.
        
        Args:
            markdown_content: Processed markdown content
            
        Returns:
            Basic HTML conversion
        """
        # A more reliable approach to paragraph conversion
        paragraphs = re.split(r'\n\s*\n', markdown_content.strip())
        html_parts = []
        
        for paragraph in paragraphs:
            # Always process paragraph, even if empty
            # Replace newlines with <br> within paragraphs
            paragraph = re.sub(r'\n', '<br>\n', paragraph)
            html_parts.append(f"<p>{paragraph}</p>")
        
        html_content = ''.join(html_parts)
        
        return html_content
        
    def _convert_image_placeholders(self, html_content: str) -> str:
        """Preserve image markers in HTML.
        
        Args:
            html_content: HTML content with image markers
            
        Returns:
            HTML with preserved image markers
        """
        # Our image markers are already in valid HTML format: <en-media-marker id="..."></en-media-marker>
        # We just need to make sure they're not modified during HTML processing
        
        # If there are any remaining old-style image placeholders, convert them
        pattern = r'\[\[image:(.*?)\|(.*?)\]\]'
        
        def replace_image(match):
            path = match.group(1)
            alt_text = match.group(2)
            # Create a placeholder that will be handled later
            return f'<div>[Image: {alt_text} ({path})]</div>'
            
        return re.sub(pattern, replace_image, html_content)
        
    def _convert_link_placeholders(self, html_content: str) -> str:
        """Convert link placeholders to HTML anchor tags.
        
        Args:
            html_content: HTML content with link placeholders
            
        Returns:
            HTML with proper anchor tags
        """
        # Convert [[link:url|text]] to <a href="url">text</a>
        pattern = r'\[\[link:(.*?)\|(.*?)\]\]'
        
        def replace_link(match):
            url = match.group(1)
            text = match.group(2)
            return f'<a href="{url}">{text}</a>'
            
        return re.sub(pattern, replace_link, html_content)
        
    def _fix_html_entities(self, html_content: str) -> str:
        """Fix HTML entities to ensure they're properly encoded.
        
        Args:
            html_content: HTML content that may contain entities
            
        Returns:
            HTML with properly encoded entities
        """
        # Entities that should be replaced in HTML content
        entities_to_replace = {
            '&amp;amp;': '&amp;',
            '&amp;lt;': '&lt;',
            '&amp;gt;': '&gt;',
            '&amp;quot;': '&quot;',
            '&amp;apos;': '&apos;'
        }
        
        result = html_content
        
        for entity, replacement in entities_to_replace.items():
            result = result.replace(entity, replacement)
            
        return result
        
    def _convert_basic_formatting(self, html_content: str) -> str:
        """Convert basic markdown formatting like bold, italic, and lists.
        
        Args:
            html_content: HTML content that may contain basic markdown formatting
            
        Returns:
            HTML with proper formatting tags
        """
        result = html_content
        
        # Bold text: **text** -> <strong>text</strong>
        result = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', result)
        
        # Italic text: *text* -> <em>text</em>
        result = re.sub(r'(?<!\*)\*([^\*]+)\*(?!\*)', r'<em>\1</em>', result)
        
        # We'll process list conversion later in the _process_text_with_lists method instead
        # This allows us to handle lists in paragraphs more precisely
        
        # Improve table formatting for better ENEX compatibility
        if '<table>' not in result and '|' in result:
            # Look for potential markdown tables and convert them
            table_pattern = r'\|(.+?)\|[\r\n]+\|([\-:]+?\|)+[\r\n]+(\|.+?[\r\n]+)+'
            
            def convert_table(match):
                table_text = match.group(0)
                rows = table_text.strip().split('\n')
                
                # Extract header
                header_row = rows[0].strip()
                header_cells = [cell.strip() for cell in header_row.split('|')[1:-1]]
                header_html = '<tr>' + ''.join([f'<th>{cell}</th>' for cell in header_cells]) + '</tr>'
                
                # Skip the separator row (row[1])
                
                # Extract data rows
                data_html = []
                for row in rows[2:]:
                    if not row.strip():
                        continue
                    cells = [cell.strip() for cell in row.split('|')[1:-1]]
                    data_html.append('<tr>' + ''.join([f'<td>{cell}</td>' for cell in cells]) + '</tr>')
                
                # Combine into table
                return f'<table>\n<thead>\n{header_html}\n</thead>\n<tbody>\n{"".join(data_html)}\n</tbody>\n</table>'
                
            result = re.sub(table_pattern, convert_table, result, flags=re.DOTALL)
            
        return result
        
    def _create_html_document(self, html_content: str) -> str:
        """Wrap HTML content in a complete HTML document structure.
        
        Args:
            html_content: HTML content to wrap
            
        Returns:
            Complete HTML document
        """
        document_title = self.html_options.get("document_title", "Converted Note")
        
        html_document = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{html.escape(document_title)}</title>
</head>
<body>
{html_content}
</body>
</html>"""
        
        return html_document


def convert_markdown_to_html(markdown_content: str, config: Dict[str, Any]) -> str:
    """Convert markdown content to HTML.
    
    Args:
        markdown_content: Processed markdown content
        config: Configuration dictionary
        
    Returns:
        HTML content
    """
    converter = HTMLConverter(config)
    return converter.convert_to_html(markdown_content)