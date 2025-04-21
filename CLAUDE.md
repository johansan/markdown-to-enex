# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Run converter: `python -m markdown_to_enex --source [directory] --output [file.enex]`
- Test single file: `python -m markdown_to_enex --test-convert [file.md] --output [directory]`
- Scan only mode: `python -m markdown_to_enex --scan-only --source [directory]`
- Verbose mode: `python -m markdown_to_enex --verbose [other options]`

## Code Style

- Imports: stdlib first, third-party next, local imports last
- Typing: Use type hints from typing module (Dict, List, Optional)
- Naming: Classes=PascalCase, functions/variables=snake_case, constants=UPPER_SNAKE_CASE
- Error handling: Use specific exceptions, meaningful error messages
- Docstrings: Google-style format (Args/Returns sections)
- Indentation: 4 spaces
- Private methods/attributes prefixed with underscore