"""
Script to update references after file restructuring
Removes references to io_manager and updates import paths to the new structure
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

def find_files(base_dir: str, extensions: List[str] = ['.py', '.md', '.bat']) -> List[Path]:
    """Find all files with specific extensions in a directory and its subdirectories"""
    base_path = Path(base_dir)
    
    all_files = []
    for ext in extensions:
        all_files.extend(base_path.glob(f"**/*{ext}"))
    
    return all_files

def remove_io_manager_references(file_path: Path) -> int:
    """
    Remove references to io_manager in a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Number of lines modified
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Lines to remove (exact matches)
    lines_to_remove = [
        "from modules.io_manager import get_instance as get_io_manager\n",
        "self.io_manager = get_io_manager(core_instance=self)\n",
        "self.components[\"io_manager\"] = self.io_manager\n",
        "self.io_manager = None\n"
    ]
    
    # Patterns to remove (regex)
    patterns_to_remove = [
        r'from .*io_manager import .*\n',
        r'import .*io_manager.*\n',
        r'self\.io_manager = .*\n',
        r'.*["\'"]io_manager["\'"]\]? ?= ?.*\n'
    ]
    
    # Keep track of how many lines are modified
    modified_count = 0
    
    # First remove exact matches
    new_lines = []
    for line in lines:
        if line in lines_to_remove:
            modified_count += 1
        else:
            new_lines.append(line)
    
    # Then check for pattern matches
    final_lines = []
    for line in new_lines:
        matched = False
        for pattern in patterns_to_remove:
            if re.match(pattern, line):
                matched = True
                modified_count += 1
                break
        
        if not matched:
            final_lines.append(line)
    
    # Write the modified file if changes were made
    if modified_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)
    
    return modified_count

def update_module_dependency_map(file_path: Path) -> int:
    """
    Update the module dependency map to remove io_manager references
    
    Args:
        file_path: Path to the module_dependency_map.md file
        
    Returns:
        Number of lines modified
    """
    if not file_path.exists() or file_path.name != "module_dependency_map.md":
        return 0
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Replace specific io_manager mentions
    old_content = content
    content = re.sub(r'- `io_manager\.py` appears to be a newer component.*\n', '', content)
    content = re.sub(r'.*io_manager.*\n', '', content)
    
    # Write the modified file if changes were made
    if content != old_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return 1
    
    return 0

def update_imports_in_file(file_path: Path) -> int:
    """
    Update import statements in a file to use the new module structure
    
    Args:
        file_path: Path to the file
        
    Returns:
        Number of imports updated
    """
    # Skip binary files and very large files
    if file_path.stat().st_size > 1_000_000:  # Skip files > 1MB
        return 0
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Update patterns:
        # 1. from modules.X import Y -> from modules.X import Y
        # 2. from core.X import Y -> from modules.X import Y
        # 3. from lyra.X import Y -> from modules.X import Y
        
        old_content = content
        
        # Only update core.X or lyra.X imports, not modules.X
        content = re.sub(r'from core\.([a-zA-Z0-9_]+) import', r'from modules.\1 import', content)
        content = re.sub(r'from lyra\.([a-zA-Z0-9_]+) import', r'from modules.\1 import', content)
        
        # Write the modified file if changes were made
        if content != old_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Count how many imports were updated
            import_count = len(re.findall(r'from (core|lyra)\.', old_content))
            return import_count
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return 0

def main():
    """Main function to update references"""
    # Get the base directory
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        # Use the parent directory of this script
        base_dir = str(Path(__file__).parent.parent)
    
    print(f"Updating references in {base_dir}")
    
    # Find all relevant files
    files = find_files(base_dir)
    print(f"Found {len(files)} files to check")
    
    # Track statistics
    stats = {
        "files_checked": 0,
        "files_modified": 0,
        "io_manager_refs_removed": 0,
        "imports_updated": 0
    }
    
    # Process each file
    for file_path in files:
        stats["files_checked"] += 1
        
        # Skip directories
        if file_path.is_dir():
            continue
        
        # Update imports
        imports_updated = update_imports_in_file(file_path)
        stats["imports_updated"] += imports_updated
        
        # Remove io_manager references
        removed_count = remove_io_manager_references(file_path)
        stats["io_manager_refs_removed"] += removed_count
        
        # Update module dependency map
        if file_path.name == "module_dependency_map.md":
            update_module_dependency_map(file_path)
        
        # Track if file was modified
        if removed_count > 0 or imports_updated > 0:
            stats["files_modified"] += 1
        
        # Print progress
        if stats["files_checked"] % 100 == 0:
            print(f"Processed {stats['files_checked']} files...")
    
    # Print statistics
    print("\nUpdate complete!")
    print(f"Files checked: {stats['files_checked']}")
    print(f"Files modified: {stats['files_modified']}")
    print(f"io_manager references removed: {stats['io_manager_refs_removed']}")
    print(f"Imports updated: {stats['imports_updated']}")

if __name__ == "__main__":
    main()
