# Markdown to ENEX Converter

A tool for converting Obsidian-style markdown files into Evernote ENEX format, with special processing to ensure compatibility with Apple Notes.

## Features

- Converts Obsidian markdown files into ENEX format
- Special processing for Apple Notes compatibility:
  - Code blocks are preserved with proper line formatting
  - Horizontal rules are converted to simple text dividers (em dashes)
  - Header markers are removed while preserving the heading text
  - Handles Obsidian-style wiki links (`[[link]]`) and image references (`![[image.jpg]]`)
  - Lists with asterisks are converted to use dashes to prevent unwanted formatting
- Preserves frontmatter metadata (title, tags, creation date)
- Handles image resources and embeds them in the ENEX file
- Groups notes by folder structure

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/markdown-to-enex.git
cd markdown-to-enex

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Convert all markdown files in a directory to a single ENEX file
python -m markdown_to_enex --source /path/to/markdown/files --output output.enex

# Test conversion on a single file
python -m markdown_to_enex --test-convert file.md --output /path/to/output/dir
```

### Additional Options

```bash
# Verbose mode for more detailed output
python -m markdown_to_enex --verbose --source /path/to/markdown/files --output output.enex

# Scan only mode to see what files would be processed
python -m markdown_to_enex --scan-only --source /path/to/markdown/files
```

## Configuration

The converter can be configured using JSON configuration files in the `config` directory.

- `default_config.json` - Default configuration
- `user_config.json` - User-specific configuration (override default settings)

## Note for Apple Notes Users

This tool is specifically designed to create ENEX files that are compatible with Apple Notes import. It handles several formatting issues to ensure your notes appear correctly after import:

1. Code blocks are formatted with individual lines wrapped in divs
2. Horizontal rules are replaced with em dash dividers
3. Special characters are properly escaped

## How It Works

1. Scans the source directory for markdown files
2. Processes markdown content to handle Obsidian-specific features
3. Converts markdown to HTML with special handling for code blocks
4. Converts HTML to ENEX format with embedded resources
5. Generates ENEX files grouped by your preferred organization method

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)