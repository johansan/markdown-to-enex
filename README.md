# Markdown to ENEX Converter

A tool for converting Obsidian-style markdown files into Evernote ENEX format, with special processing to ensure compatibility with Apple Notes.

## Features

- Converts Obsidian markdown files into ENEX format
- Special processing for Apple Notes compatibility:
  - Code block styling is removed (Apple Notes cannot import code blocks) but content is preserved with proper line-by-line formatting
  - Horizontal rules are converted to simple text dividers (em dashes) as Apple Notes cannot import horizontal rules
  - Header styling is removed (Apple Notes cannot import header styles) while preserving the heading text
  - Highlight formatting (==highlighted text==) is removed while preserving the text
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

The converter can be configured using JSON configuration files in the `config` directory:

- `default_config.json` - Default configuration (should not be modified)
- `user_config.json` - User-specific configuration (overrides default settings)

### Configuration Options

#### Core Settings
- `source_directory`: Path to the directory containing markdown files
- `output_directory`: Path where ENEX files will be saved

#### Processing Options
Controls how markdown content is processed:
- `remove_code_block_markers`: Controls whether to strip ``` markers from code blocks
- `convert_inline_code`: Controls processing of inline code (between backticks)
- `remove_heading_markers`: If true, removes # symbols from headings
- `handle_image_references`: Processes image references in markdown
- `process_links`: Converts markdown links to HTML links
- `handle_special_chars`: Enables special character handling
- `escape_html_chars`: Controls HTML entity escaping (<, >, &, etc.)
- `special_char_replacements`: Map of special characters to their replacements

#### HTML Options
Controls HTML conversion:
- `markdown_engine`: Which markdown engine to use ("auto", "python-markdown")
- `enable_tables`: Enables table support in the converter
- `enable_fenced_code`: Supports fenced code blocks (```code```)
- `create_full_document`: Whether to create a complete HTML document with headers

#### Resource Options
Controls handling of embedded resources (images):
- `max_resource_size`: Maximum size for resources in bytes (default: 50MB)
- `include_resource_attributes`: Whether to include attributes like filename
- `include_unknown_resources`: Whether to include placeholder for unfound resources

#### ENEX Options
Controls ENEX file generation:
- `add_creation_date`: Whether to include creation date in notes
- `add_update_date`: Whether to include update date in notes
- `add_source_url`: Whether to include source URL (not used for Apple Notes)
- `extract_metadata`: Whether to extract metadata from markdown
- `default_author`: Default author name for notes

#### Output Options
Controls how ENEX files are organized:
- `group_by`: How to group notes into ENEX files:
  - `single`: All notes in one ENEX file
  - `top_folder`: Group by top-level folder
  - `full_folder`: Preserve full folder structure
- `naming_pattern`: Pattern for ENEX filenames ({name} gets replaced)
- `max_notes_per_file`: Maximum notes per ENEX file (0 = unlimited)
- `replace_spaces`: Whether to replace spaces in filenames

## Note for Apple Notes Users

This tool is specifically designed to create ENEX files that are compatible with Apple Notes import, which has limitations when importing ENEX files. Apple Notes cannot import:

1. Code block styling (code blocks appear as regular text)
2. Header styling (headers appear as regular text)
3. Horizontal rules (these are replaced with em dashes)
4. Highlighted text (Obsidian ==highlights== are removed)
5. Many forms of rich text formatting

To work around these limitations, this converter:
1. Removes code block styling but preserves content with line-by-line div formatting
2. Removes header formatting but keeps the text intact
3. Converts horizontal rules to simple em dash dividers
4. Preserves highlight text but removes the highlighting markers
5. Ensures special characters are properly escaped for maximum compatibility
6. Only preserves creation date from frontmatter (other metadata is lost)

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