"""
Module for extracting and processing code blocks to preserve formatting.
"""
import re
import uuid
from typing import Dict, List, Tuple


def extract_code_blocks(markdown_content: str) -> Tuple[str, Dict[str, str]]:
    """
    Extract code blocks from markdown content and replace them with markers.
    
    Args:
        markdown_content: The markdown content
        
    Returns:
        Tuple of (content with markers, dictionary of code blocks)
    """
    code_blocks = {}
    
    # Function to process each code block match
    def replace_code_block(match):
        block_language = match.group(1) or ""
        block_content = match.group(2)
        
        # Generate a unique ID for this code block
        block_id = f"CODE_BLOCK_{uuid.uuid4().hex[:8]}"
        
        # Store the code block
        code_blocks[block_id] = {
            "language": block_language.strip(),
            "content": block_content
        }
        
        # Return a marker with minimal spacing
        # No preceding newline, only one following newline
        return f"{block_id}\n"
    
    # Match fenced code blocks ```lang\ncontent```
    pattern = r'```(.*?)\n(.*?)```'
    processed_content = re.sub(pattern, replace_code_block, markdown_content, flags=re.DOTALL)
    
    return processed_content, code_blocks


def restore_code_blocks(content: str, code_blocks: Dict[str, Dict[str, str]]) -> str:
    """
    Restore code blocks from markers.

    Args:
        content: Content with code block markers
        code_blocks: Dictionary of code block contents

    Returns:
        Content with code blocks restored
    """
    result = content

    # Replace each marker with the corresponding code block
    for block_id, block_data in code_blocks.items():
        language = block_data["language"]
        block_content = block_data["content"]

        # Escape HTML entities to prevent further processing
        # This is critical to prevent markdown processors from formatting inside code blocks
        escaped_content = (block_content
                          .replace('&', '&amp;')
                          .replace('<', '&lt;')
                          .replace('>', '&gt;')
                          .replace('*', '&#42;')  # Explicitly escape asterisks
                          .replace('_', '&#95;'))  # Explicitly escape underscores

        # Split the content by lines and wrap each line in a div
        wrapped_lines = []
        lines = escaped_content.split('\n')

        # Process all lines except potentially the last one
        for i, line in enumerate(lines):
            # Skip adding an empty div for the last line if it's empty
            # This avoids extra line breaks at the end of code blocks
            if i == len(lines) - 1 and not line.strip() and i > 0:
                continue

            # Empty lines need a <br/> tag
            if not line.strip():
                wrapped_lines.append('<div><br/></div>')
            else:
                wrapped_lines.append(f'<div>{line}</div>')

        # Join the wrapped lines without pre/code tags
        # Just return the div-wrapped lines directly
        replacement = ''.join(wrapped_lines)

        # Replace the marker with the HTML
        result = result.replace(block_id, replacement)

    return result


def extract_inline_code(markdown_content: str) -> Tuple[str, Dict[str, str]]:
    """
    Extract inline code from markdown content and replace with markers.
    
    Args:
        markdown_content: The markdown content
        
    Returns:
        Tuple of (content with markers, dictionary of inline code)
    """
    inline_codes = {}
    
    # Function to process each inline code match
    def replace_inline_code(match):
        inline_content = match.group(1)
        
        # Generate a unique ID for this inline code
        inline_id = f"INLINE_CODE_{uuid.uuid4().hex[:8]}"
        
        # Store the inline code
        inline_codes[inline_id] = inline_content
        
        # Return a marker
        return inline_id
    
    # Match inline code `content`
    pattern = r'`([^`]+)`'
    processed_content = re.sub(pattern, replace_inline_code, markdown_content)
    
    return processed_content, inline_codes


def restore_inline_code(content: str, inline_codes: Dict[str, str]) -> str:
    """
    Restore inline code from markers.

    Args:
        content: Content with inline code markers
        inline_codes: Dictionary of inline code

    Returns:
        Content with inline code restored
    """
    result = content

    # Replace each marker with the corresponding inline code
    for inline_id, inline_content in inline_codes.items():
        # Escape HTML entities to prevent further processing
        escaped_content = (inline_content
                          .replace('&', '&amp;')
                          .replace('<', '&lt;')
                          .replace('>', '&gt;')
                          .replace('*', '&#42;')  # Explicitly escape asterisks
                          .replace('_', '&#95;'))  # Explicitly escape underscores

        # Wrap in HTML code tags for direct HTML insertion
        replacement = f'<code>{escaped_content}</code>'

        # Replace the marker with the HTML
        result = result.replace(inline_id, replacement)

    return result