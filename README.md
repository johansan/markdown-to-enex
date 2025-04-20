# Markdown to ENEX Converter

A Python application that converts a folder structure of markdown notes into Evernote's ENEX format.

## Features

- Convert markdown files to ENEX format for Evernote import
- Process resource references (images, attachments) and include them in the ENEX file
- Preserve metadata such as creation date, tags, and titles
- Flexible output options for creating single or multiple ENEX files
- Smart grouping by folders, notebooks, or custom criteria
- Split large exports into multiple files for easier importing
- Progress reporting for large exports
- Robust configuration options for customizing the conversion process
- Command-line interface for easy use

## Project Structure

```
markdown-to-enex/
├── config/                     # Configuration files
│   ├── default_config.json     # Default configuration
│   └── user_config.json        # User-specific configuration
├── markdown_to_enex/           # Main package
│   ├── __init__.py
│   ├── __main__.py             # Entry point
│   ├── config.py               # Configuration module
│   ├── scanner.py              # Directory scanner module
│   ├── markdown_processor.py   # Markdown preprocessing module
│   ├── html_converter.py       # HTML conversion module
│   ├── enml_processor.py       # ENML/ENEX conversion module
│   ├── resource_handler.py     # Resource processing module
│   ├── enex_generator.py       # ENEX file generation module
│   └── tests/                  # Tests
├── examples/                   # Example scripts
│   ├── scanner_example.py       
│   ├── markdown_processor_example.py
│   ├── html_converter_example.py
│   ├── full_conversion_example.py
│   ├── enex_converter_example.py
│   ├── resource_handler_example.py
│   ├── enex_generator_example.py
│   ├── _resources/             # Sample resources for examples
│   └── test.md                 # Sample markdown file
├── output/                     # Output directory for examples
├── README.md
├── requirements.txt            # Dependencies
└── setup.py
```

## Installation

This project requires Python 3.6 or higher.

### Using a Virtual Environment (recommended)

A virtual environment is the preferred way to run this application, especially on macOS or systems with externally managed Python environments.

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .

# Now you can run the CLI within the virtual environment
markdown-to-enex --help

# Or run it directly
python -m markdown_to_enex --help
```

If you're on macOS or a system with an externally managed Python environment and encounter errors like "externally-managed-environment", using a virtual environment is mandatory.

### Using the CLI

After setting up the virtual environment and installing the package, you can use the command-line interface:

```bash
# Make sure the virtual environment is activated
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the CLI command
markdown-to-enex --source /path/to/notes --output output.enex

# Or run it as a module
python -m markdown_to_enex --source /path/to/notes --output output.enex
```

The CLI provides a simple interface to convert your markdown notes to ENEX format, with various options for customization.

## Dependencies

The converter requires the following libraries:

- `markdown`: For converting markdown to HTML
- `commonmark`: Alternative markdown parsing (used as fallback)

These dependencies are specified in `requirements.txt`.

## Usage

After installation, you can use the command-line interface:

```bash
# Using default configuration with command line arguments
python -m markdown_to_enex --source /path/to/markdown/notes --output /path/to/output.enex

# Using a custom configuration file
python -m markdown_to_enex --config /path/to/custom/config.json --source /path/to/markdown/notes --output /path/to/output.enex

# Scan only (without conversion)
python -m markdown_to_enex --source /path/to/markdown/notes --output /path/to/output --scan-only

# Test conversion on a single file
python -m markdown_to_enex --test-convert /path/to/file.md --output /path/to/output

# Create separate ENEX files based on folder structure
python -m markdown_to_enex --source /path/to/markdown/notes --output /path/to/output/dir --separate-files

# Enable verbose output
python -m markdown_to_enex --source /path/to/markdown/notes --output /path/to/output.enex --verbose
```

### Command-line Options

| Option | Description |
|--------|-------------|
| `--source` | Path to source directory containing markdown files |
| `--output` | Path to output ENEX file or directory |
| `--config` | Path to custom configuration file (optional) |
| `--scan-only` | Only scan the directory structure without conversion |
| `--test-convert FILE` | Test conversion on a single markdown file |
| `--verbose` | Enable verbose output with detailed progress information |
| `--separate-files` | Create separate ENEX files based on folder structure |
| `--group-by` | Grouping strategy: single, top_folder, full_folder, notebook, or custom |
| `--max-notes` | Maximum number of notes per ENEX file (0 for no limit) |

### Using Example Scripts

The `examples` directory contains several scripts demonstrating specific features:

```bash
# Directory scanner example
python examples/scanner_example.py /path/to/markdown/notes

# Markdown processor example
python examples/markdown_processor_example.py /path/to/file.md

# HTML converter example
python examples/html_converter_example.py /path/to/file.md

# Full conversion example
python examples/full_conversion_example.py /path/to/file.md

# Markdown to ENEX conversion
python examples/enex_converter_example.py /path/to/file.md

# Resource handling
python examples/resource_handler_example.py /path/to/resources_folder image1.png image2.jpg

# ENEX file generation
python examples/enex_generator_example.py /path/to/note1.md /path/to/note2.md output.enex

# ENEX output with different grouping options
python examples/enex_output_example.py /path/to/notes/folder /path/to/output/dir
```

## Configuration

Configuration is loaded from a JSON file with the following structure:

```json
{
  "source_directory": "/path/to/markdown/notes",
  "output_directory": "/path/to/output",
  "resources_directory": "_resources",
  "processing_options": {
    "remove_code_block_markers": true,
    "convert_inline_code": true,
    "remove_heading_markers": true,
    "handle_image_references": true,
    "process_links": true,
    "handle_special_chars": true,
    "preserve_image_markdown": false,
    "preserve_link_markdown": false,
    "escape_html_chars": true,
    "special_char_replacements": {
      "–": "--",
      "—": "---",
      "…": "..."
    }
  },
  "html_options": {
    "markdown_engine": "auto",
    "enable_tables": true,
    "enable_fenced_code": true,
    "create_full_document": false,
    "document_title": "Converted Note"
  },
  "enml_options": {
    "clean_html": true,
    "add_creation_date": true,
    "add_source_url": false
  },
  "resource_options": {
    "max_resource_size": 52428800,
    "include_resource_attributes": true,
    "include_unknown_resources": true
  },
  "enex_options": {
    "add_creation_date": true,
    "add_update_date": true,
    "add_source_url": false,
    "extract_metadata": true,
    "default_author": "markdown-to-enex",
    "enex_version": "1.0",
    "application_name": "markdown-to-enex"
  },
  "output_options": {
    "group_by": "single",
    "naming_pattern": "{name}.enex",
    "max_notes_per_file": 0,
    "progress_reporting": true,
    "replace_spaces": true
  }
}
```

You can create a custom configuration file by copying and modifying the default
configuration from `config/default_config.json`.

### Output Options Explained

The `output_options` section controls how ENEX files are generated:

| Option | Description |
|--------|-------------|
| `group_by` | How to group notes into ENEX files:<br>- `single`: All notes in one file<br>- `top_folder`: Group by top-level folder<br>- `full_folder`: Group by complete folder path<br>- `notebook`: Group by notebook metadata<br>- `custom`: Use enex_filename from note info |
| `naming_pattern` | Pattern for output filenames. Use `{name}` as a placeholder for the group name |
| `max_notes_per_file` | Maximum number of notes per file (0 = no limit). Useful for large exports |
| `progress_reporting` | Enable detailed progress reporting |
| `replace_spaces` | Replace spaces with underscores in filenames |

## Testing

Run tests using:

```bash
python -m unittest discover
```

## Example Workflow

### Scenario: Converting a folder of markdown notes to Evernote

Let's say you have a folder structure like this:

```
~/Notes/
├── Work/
│   ├── Project A/
│   │   ├── meeting-notes.md
│   │   ├── requirements.md
│   │   └── _resources/
│   │       ├── diagram.png
│   │       └── timeline.jpg
│   └── Project B/
│       ├── ideas.md
│       └── tasks.md
└── Personal/
    ├── Travel/
    │   ├── paris-trip.md
    │   └── _resources/
    │       └── eiffel-tower.jpg
    └── Recipes/
        ├── pasta.md
        └── bread.md
```

To convert this to ENEX format with separate notebooks:

```bash
markdown-to-enex --source ~/Notes --output ~/EvernoteExport --separate-files
```

This will create:

```
~/EvernoteExport/
├── Work.enex     # Contains Project A and Project B notes
├── Personal - Travel.enex
└── Personal - Recipes.enex
```

To convert everything to a single ENEX file:

```bash
markdown-to-enex --source ~/Notes --output ~/EvernoteExport/all_notes.enex
```

This will create one file with all notes:

```
~/EvernoteExport/all_notes.enex
```

### Metadata Support

You can include metadata in your markdown files using a YAML-like format at the top:

```markdown
---
title: My Custom Title
created: 2023-01-15T14:30:00
updated: 2023-01-16T10:15:00
tags: important, reference, work
---

# Note Content Begins Here

This is the actual content of the note...
```

The converter will recognize this metadata and use it in the generated ENEX file.