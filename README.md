# Markdown to ENEX Converter

A tool for converting Obsidian-style markdown files into Evernote ENEX format, with special processing to ensure compatibility with Apple Notes.

## Features

- Converts Obsidian markdown files into ENEX format
- Special processing for Apple Notes compatibility:
  - Code block styling is removed (Apple Notes cannot import code blocks) but content is preserved with proper line-by-line formatting
  - Horizontal rules are converted to simple text dividers (em dashes) as Apple Notes cannot import horizontal rules
  - Header styling is removed (Apple Notes cannot import header styles) while preserving the heading text
  - Handles Obsidian-style wiki links (`[[link]]`) and image references (`![[image.jpg]]`)
  - Lists with asterisks are converted to use dashes to prevent unwanted formatting
- Frontmatter handling:
  - Only creation date is preserved from frontmatter
  - If creation date is not found in frontmatter, file creation date is used
  - Other frontmatter metadata is not preserved
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

This tool is specifically designed to create ENEX files that are compatible with Apple Notes import, which has limitations when importing ENEX files. Apple Notes cannot import:

1. Code block styling (code blocks appear as regular text)
2. Header styling (headers appear as regular text)
3. Horizontal rules (these are replaced with em dashes)
4. Many forms of rich text formatting

To work around these limitations, this converter:
1. Removes code block styling but preserves content with line-by-line div formatting
2. Removes header formatting but keeps the text intact
3. Converts horizontal rules to simple em dash dividers
4. Ensures special characters are properly escaped for maximum compatibility
5. Only preserves creation date from frontmatter (other metadata is lost)

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