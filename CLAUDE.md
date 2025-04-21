# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Use virtual environment for all commands
- Run converter: `python -m markdown_to_enex --source [directory] --output [file.enex]`
- Test single file: `python -m markdown_to_enex --test-convert [file.md] --output [directory]`
- Scan only mode: `python -m markdown_to_enex --scan-only --source [directory]`
- Verbose mode: `python -m markdown_to_enex --verbose [other options]`

## Project Files

- `__main__.py` - Entry point for the application, handles CLI arguments and orchestrates processing
- `config.py` - Configuration management, loads default and user settings from JSON files
- `scanner.py` - Scans directory structure and identifies markdown files for conversion
- `markdown_processor.py` - Processes markdown content, handles formatting and special characters
- `html_converter.py` - Converts processed markdown to HTML using markdown libraries
- `enml_processor.py` - Converts HTML to Evernote's ENML format, handles resources
- `resource_handler.py` - Processes images and other resources for inclusion in ENEX files
- `enex_generator.py` - Generates ENEX file content for individual notes
- `enex_output.py` - Handles grouping notes and generating final ENEX output files

## Processing Flow

1. **Configuration**: Load settings from default and user config files
2. **Scanning**: Scan source directory for markdown files and resources
3. **Markdown Processing**: For each note:
   - Extract frontmatter metadata
   - Clean problematic Unicode characters
   - Convert star lists to dashes
   - Process wiki-links and highlights
   - Handle special characters
   - Process image references
4. **HTML Conversion**: Convert processed markdown to HTML
   - Apply proper list formatting
   - Format tables and other elements
5. **ENML Processing**: Convert HTML to Evernote's ENML format
   - Process and preserve list structure
   - Convert HTML tags to Evernote-compatible format
   - Process image references to en-media tags
6. **Resource Handling**: Process all referenced resources (images)
7. **ENEX Generation**: Create note objects with content and resources
8. **Output**: Group notes based on configuration and write to ENEX files

## Code Style

- Imports: stdlib first, third-party next, local imports last
- Typing: Use type hints from typing module (Dict, List, Optional)
- Naming: Classes=PascalCase, functions/variables=snake_case, constants=UPPER_SNAKE_CASE
- Error handling: Use specific exceptions, meaningful error messages
- Docstrings: Google-style format (Args/Returns sections)
- Indentation: 4 spaces
- Private methods/attributes prefixed with underscore