"""
Markdown to ENEX Converter

A Python application that converts a folder structure of markdown notes into Evernote's ENEX format.
"""

from .config import Config, ConfigError
from .scanner import DirectoryScanner, Note, scan_directory
from .markdown_processor import MarkdownProcessor, process_markdown_file
from .html_converter import HTMLConverter, convert_markdown_to_html
from .enml_processor import ENMLProcessor, process_html_to_enml
from .resource_handler import ResourceHandler, process_resources
from .enex_generator import ENEXGenerator, generate_enex_file, extract_note_metadata, create_note_object
from .enex_output import ENEXOutput, generate_output, get_best_group_by, ENEXOutputError

__version__ = "0.1.0"