"""
ENEX Output Module

This module handles the final ENEX file generation and output, combining processed notes
and resources into complete ENEX files according to the configured grouping rules.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional
from collections import defaultdict

from .enex_generator import generate_enex_file, create_note_object


class ENEXOutputError(Exception):
    """Exception raised for errors during ENEX output generation."""
    pass


class ENEXOutput:
    """Handles the final ENEX file generation and output."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the ENEX output handler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.output_options = config.get("output_options", {})
        
        # Initialize options
        self.output_directory = config.get("output_directory", ".")
        self.group_by = self.output_options.get("group_by", "single")  # "single", "top_folder", "full_folder"
        self.naming_pattern = self.output_options.get("naming_pattern", "{name}.enex")
        self.max_notes_per_file = self.output_options.get("max_notes_per_file", 0)  # 0 = no limit
        self.progress_reporting = self.output_options.get("progress_reporting", True)
        
        # Create logger
        self.logger = logging.getLogger("enex_output")
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def generate(self, notes: List[Dict[str, Any]], note_info: List[Dict[str, Any]] = None) -> Dict[str, str]:
        """Generate ENEX file(s) from processed notes.
        
        Args:
            notes: List of note objects (with content, resources, etc.)
            note_info: Optional list of note info objects from scanner
            
        Returns:
            Dictionary mapping ENEX filenames to output paths
        """
        # Ensure output directory exists
        output_dir = Path(self.output_directory)
        output_dir.mkdir(exist_ok=True, parents=True)
        
        if self.progress_reporting:
            self.logger.info(f"Generating ENEX output in {output_dir}")
            self.logger.info(f"Group by: {self.group_by}")
            self.logger.info(f"Total notes: {len(notes)}")
        
        # Group notes
        grouped_notes = self._group_notes(notes, note_info)
        
        # Generate ENEX files
        output_files = {}
        
        total_groups = len(grouped_notes)
        for i, (group_name, group_notes) in enumerate(grouped_notes.items(), 1):
            if self.progress_reporting:
                self.logger.info(f"Generating ENEX file {i}/{total_groups}: {group_name}")
            
            # Apply note limit if configured
            if self.max_notes_per_file > 0 and len(group_notes) > self.max_notes_per_file:
                output_files.update(self._split_large_group(group_name, group_notes, output_dir))
            else:
                # Generate a single file for this group
                filename = self._format_filename(group_name)
                output_path = output_dir / filename
                
                if self.progress_reporting:
                    self.logger.info(f"Writing {len(group_notes)} notes to {output_path}")
                
                try:
                    start_time = time.time()
                    generate_enex_file(group_notes, self.config, str(output_path))
                    end_time = time.time()
                    
                    if self.progress_reporting:
                        file_size = output_path.stat().st_size
                        self.logger.info(f"Created {filename} ({self._format_size(file_size)}) in {end_time - start_time:.2f} seconds")
                    
                    output_files[group_name] = str(output_path)
                except Exception as e:
                    error_msg = f"Error generating ENEX file {filename}: {str(e)}"
                    self.logger.error(error_msg)
                    raise ENEXOutputError(error_msg) from e
        
        if self.progress_reporting:
            self.logger.info(f"Successfully generated {len(output_files)} ENEX files")
        
        return output_files
    
    def _group_notes(self, notes: List[Dict[str, Any]], note_info: List[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Group notes according to the configured grouping rule.
        
        Args:
            notes: List of note objects
            note_info: Optional list of note info objects from scanner
            
        Returns:
            Dictionary mapping group names to lists of notes
        """
        grouped_notes = defaultdict(list)
        
        # If note_info is not provided, default to single file
        if note_info is None or self.group_by == "single":
            grouped_notes["All Notes"] = notes
            return grouped_notes
        
        # Create a mapping from file paths to note objects
        note_map = {}
        for i, note_info_item in enumerate(note_info):
            if i < len(notes):
                note_map[note_info_item["file_path"]] = notes[i]
        
        # Group by top-level folder
        if self.group_by == "top_folder":
            for note_info_item in note_info:
                file_path = note_info_item["file_path"]
                if file_path in note_map:
                    # Get top-level folder
                    relative_path = note_info_item.get("relative_path", file_path)
                    parts = Path(relative_path).parts
                    
                    if len(parts) > 1:
                        group_name = parts[0]
                    else:
                        group_name = "Root"
                    
                    grouped_notes[group_name].append(note_map[file_path])
        
        # Group by full folder path
        elif self.group_by == "full_folder":
            for note_info_item in note_info:
                file_path = note_info_item["file_path"]
                if file_path in note_map:
                    # Use folder path
                    folder_path = note_info_item.get("folder_path", "Root")
                    grouped_notes[folder_path].append(note_map[file_path])
        
        # Group by notebook (if specified in note metadata)
        elif self.group_by == "notebook":
            for note_info_item in note_info:
                file_path = note_info_item["file_path"]
                if file_path in note_map:
                    note = note_map[file_path]
                    notebook = note.get("notebook", "Default")
                    grouped_notes[notebook].append(note)
        
        # Group by custom (use enex_filename from note_info)
        elif self.group_by == "custom":
            for note_info_item in note_info:
                file_path = note_info_item["file_path"]
                if file_path in note_map:
                    # Use custom filename from note_info
                    enex_filename = note_info_item.get("enex_filename", "notes.enex")
                    # Remove .enex extension for group name
                    if enex_filename.lower().endswith(".enex"):
                        group_name = enex_filename[:-5]
                    else:
                        group_name = enex_filename
                    
                    grouped_notes[group_name].append(note_map[file_path])
        
        # If no grouping was done (e.g., invalid group_by), default to single file
        if not grouped_notes:
            grouped_notes["All Notes"] = notes
        
        return grouped_notes
    
    def _split_large_group(self, group_name: str, notes: List[Dict[str, Any]], output_dir: Path) -> Dict[str, str]:
        """Split a large group of notes into multiple files.
        
        Args:
            group_name: Name of the group
            notes: List of notes in the group
            output_dir: Output directory
            
        Returns:
            Dictionary mapping group names to output paths
        """
        output_files = {}
        chunk_size = self.max_notes_per_file
        
        # Calculate number of chunks
        num_chunks = (len(notes) + chunk_size - 1) // chunk_size
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(notes))
            
            chunk_notes = notes[start_idx:end_idx]
            chunk_name = f"{group_name} (Part {i+1})"
            
            if self.progress_reporting:
                self.logger.info(f"Generating part {i+1}/{num_chunks} for {group_name} with {len(chunk_notes)} notes")
            
            filename = self._format_filename(chunk_name)
            output_path = output_dir / filename
            
            try:
                start_time = time.time()
                generate_enex_file(chunk_notes, self.config, str(output_path))
                end_time = time.time()
                
                if self.progress_reporting:
                    file_size = output_path.stat().st_size
                    self.logger.info(f"Created {filename} ({self._format_size(file_size)}) in {end_time - start_time:.2f} seconds")
                
                output_files[chunk_name] = str(output_path)
            except Exception as e:
                error_msg = f"Error generating ENEX file {filename}: {str(e)}"
                self.logger.error(error_msg)
                raise ENEXOutputError(error_msg) from e
        
        return output_files
    
    def _format_filename(self, name: str) -> str:
        """Format a filename according to the naming pattern.
        
        Args:
            name: Base name for the file
            
        Returns:
            Formatted filename
        """
        # Remove invalid characters from filename
        safe_name = "".join(c for c in name if c.isalnum() or c in " -_.")
        safe_name = safe_name.strip()
        
        # Replace spaces with underscores if they remain
        if self.output_options.get("replace_spaces", True):
            safe_name = safe_name.replace(" ", "_")
        
        # Add .enex extension if not in the pattern
        if "{name}" in self.naming_pattern:
            filename = self.naming_pattern.format(name=safe_name)
            if not filename.lower().endswith(".enex"):
                filename += ".enex"
        else:
            filename = f"{safe_name}.enex"
        
        return filename
    
    def _format_size(self, size_bytes: int) -> str:
        """Format a file size in a human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024 or unit == "GB":
                break
            size_bytes /= 1024
        
        return f"{size_bytes:.1f} {unit}"


def generate_output(notes: List[Dict[str, Any]], 
                   note_info: List[Dict[str, Any]], 
                   config: Dict[str, Any]) -> Dict[str, str]:
    """Generate ENEX output files.
    
    Args:
        notes: List of note objects
        note_info: List of note info objects from scanner
        config: Configuration dictionary
        
    Returns:
        Dictionary mapping group names to output paths
    """
    output_handler = ENEXOutput(config)
    return output_handler.generate(notes, note_info)


def get_best_group_by(folder_structure: Dict[str, Any]) -> str:
    """Determine the best grouping strategy based on folder structure.
    
    Args:
        folder_structure: Dictionary representing folder structure
        
    Returns:
        Suggested grouping strategy
    """
    if not folder_structure:
        return "single"
    
    # Count total notes and folders
    total_notes = folder_structure.get("total_notes", 0)
    
    # If very few notes, just use a single file
    if total_notes < 10:
        return "single"
    
    # Count top-level folders
    top_folders = []
    for key, value in folder_structure.items():
        if key != "total_notes" and key != "total_resources" and isinstance(value, dict):
            top_folders.append(key)
    
    # If there are multiple top-level folders, group by top folder
    if len(top_folders) > 1:
        return "top_folder"
    
    # If there's just one top folder but it has subfolders, try full path
    if len(top_folders) == 1:
        top_folder = top_folders[0]
        if isinstance(folder_structure[top_folder], dict):
            has_subfolders = False
            for key, value in folder_structure[top_folder].items():
                if key != "notes" and key != "resources" and isinstance(value, dict):
                    has_subfolders = True
                    break
            
            if has_subfolders:
                return "full_folder"
    
    # Default to single file
    return "single"