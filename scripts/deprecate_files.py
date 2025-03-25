import os
import shutil
from pathlib import Path
import logging
from datetime import datetime
import stat
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("deprecate_files")

# Main repository path
REPO_PATH = Path("G:/AI/Lyra")

# Create deprecated folder if it doesn't exist
DEPRECATED_PATH = REPO_PATH / "deprecated"
DEPRECATED_PATH.mkdir(exist_ok=True)
logger.info(f"Ensuring deprecated folder exists at {DEPRECATED_PATH}")

# List of files and directories to deprecate
# Format: (source_path, reason_for_deprecation)
TO_DEPRECATE = [
    # Node.js related files
    ("oobabooga", "Entire oobabooga directory with JS files no longer in use"),
    ("node_modules", "Node.js dependencies no longer needed"),
    ("package.json", "Node.js package file no longer needed"),
    ("package-lock.json", "Node.js package lock file no longer needed"),
    
    # Redundant runners and wrappers
    ("run_lyra_chat.py", "Replaced by more current runners"),
    ("simple_chat.py", "Using lyra_app.py as the main entry point instead"),
    ("chat_app.py", "Using lyra_app.py as the main entry point instead"),
    ("run_llama_server.py", "Using server_config.py directly instead"),
    
    # Old github updaters (keep scripts/github_update.py)
    ("github_update.py", "Using scripts/github_update.py instead"),
    ("update_github.py", "Using scripts/github_update.py instead"),
    ("git_push.py", "Using scripts/github_update.py instead"),
    
    # GPU/Hardware checkers
    ("check_gpu.py", "Functionality integrated into model_manager.py"),
    ("gpu_info.py", "Functionality integrated into model_manager.py"),
    ("hardware_check.py", "Functionality integrated into model_manager.py"),
    
    # Old configuration files
    ("old_configs", "Using the new config structure"),
    ("config_old.json", "Using new configuration format"),
    
    # Miscellaneous unused files
    ("upgrade_gradio.py", "One-time upgrade script no longer needed"),
    ("server_config.py", "Functionality integrated into llama_server_provider.py"),
    
    # Keep the following commented out unless you're sure:
    # ("collaborative_improvement_app.py", "Using lyra_app.py with --mode collaborative instead"),
]

def handle_readonly_files(func, path, exc_info):
    """
    Error handler for shutil.rmtree to handle read-only files.
    This is especially helpful for Git-managed files.
    """
    # Check if the error is due to read-only files
    if not os.access(path, os.W_OK):
        # Make the file writable
        os.chmod(path, stat.S_IWRITE)
        # Try the operation again
        func(path)
    else:
        # If it's a different error, re-raise the exception
        raise

def handle_git_repo(source_path, target_path):
    """Special handling for Git repositories."""
    try:
        logger.info(f"Detected Git repo at {source_path}, using alternative method")
        # Create target directory if it doesn't exist
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Create a .nojekyll file to indicate this is not a normal Git repo
        with open(target_path / ".nojekyll", "w") as f:
            f.write(f"This is a deprecated Git repository from {source_path}\n")
            f.write(f"Moved on: {datetime.now().strftime('%Y-%m-%d')}\n")
        
        # Create a placeholder file explaining the situation
        with open(target_path / "README.md", "w") as f:
            f.write(f"# Deprecated Git Repository\n\n")
            f.write(f"This was a Git repository from `{source_path}` that was deprecated.\n")
            f.write(f"Due to permission issues, only this placeholder was created.\n")
            f.write(f"Deprecated on: {datetime.now().strftime('%Y-%m-%d')}\n")
        
        # Try to use git operations if git is available
        try:
            # Clone the repository without working files (bare clone)
            subprocess.run(["git", "clone", "--bare", str(source_path), str(target_path / "repo.git")], 
                          check=True, capture_output=True, text=True)
            logger.info(f"Created bare clone of repository at {target_path / 'repo.git'}")
        except Exception as e:
            logger.warning(f"Could not create bare clone: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error handling Git repository: {e}")
        return False

def deprecate_files():
    """Move deprecated files to the deprecated folder."""
    deprecated_count = 0
    
    for file_path, reason in TO_DEPRECATE:
        source_path = REPO_PATH / file_path
        
        # Skip if source doesn't exist
        if not source_path.exists():
            logger.warning(f"Source path does not exist: {source_path}")
            continue
        
        # Create target directory
        target_dir = DEPRECATED_PATH / os.path.dirname(file_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Move file or directory
        target_path = DEPRECATED_PATH / file_path
        try:
            # If it's a directory
            if source_path.is_dir():
                # Check if it's a git repository
                if (source_path / ".git").exists():
                    if handle_git_repo(source_path, target_path):
                        # Remove the original with permissions fix
                        shutil.rmtree(source_path, onerror=handle_readonly_files)
                    else:
                        # Skip this path if we couldn't handle it as a Git repo
                        continue
                else:
                    # Normal directory handling
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(source_path, target_path)
                    shutil.rmtree(source_path, onerror=handle_readonly_files)
            # If it's a file
            else:
                if target_path.exists():
                    os.remove(target_path)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(source_path, target_path)
            
            # Create a reason file
            with open(f"{target_path}.reason.txt", "w") as f:
                f.write(f"Deprecated on: {datetime.now().strftime('%Y-%m-%d')}\n")
                f.write(f"Reason: {reason}\n")
            
            logger.info(f"Deprecated: {file_path} -> {target_path}")
            deprecated_count += 1
        
        except Exception as e:
            logger.error(f"Error deprecating {file_path}: {e}")
    
    logger.info(f"Deprecated {deprecated_count} files/directories")
    return deprecated_count

def update_gitignore():
    """Update .gitignore to include the deprecated folder."""
    gitignore_path = REPO_PATH / ".gitignore"
    
    # Create .gitignore if it doesn't exist
    if not gitignore_path.exists():
        with open(gitignore_path, "w") as f:
            f.write("# Lyra .gitignore file\n\n")
        logger.info("Created new .gitignore file")
    
    # Read current .gitignore
    with open(gitignore_path, "r") as f:
        content = f.read()
    
    # Check if deprecated folder is already in .gitignore
    if "deprecated/" in content or "/deprecated/" in content:
        logger.info("deprecated/ already in .gitignore")
        return False
    
    # Add deprecated folder to .gitignore
    with open(gitignore_path, "a") as f:
        f.write("\n# Deprecated files\n")
        f.write("deprecated/\n")
    
    logger.info("Added deprecated/ to .gitignore")
    return True

if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Deprecate unused files in the Lyra repository")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deprecated without moving files")
    parser.add_argument("--list", action="store_true", help="List files to be deprecated")
    parser.add_argument("--force", action="store_true", help="Force operation even on files with permission issues")
    args = parser.parse_args()
    
    if args.list:
        print("Files to be deprecated:")
        for file_path, reason in TO_DEPRECATE:
            source_path = REPO_PATH / file_path
            status = "Exists" if source_path.exists() else "Not found"
            print(f"- {file_path} ({status}): {reason}")
        exit(0)
    
    if args.dry_run:
        print("Dry run - no files will be moved")
        for file_path, reason in TO_DEPRECATE:
            source_path = REPO_PATH / file_path
            if source_path.exists():
                print(f"Would deprecate: {file_path} (Reason: {reason})")
        exit(0)
    
    # Update .gitignore first
    update_gitignore()
    
    # Deprecate files
    deprecated_count = deprecate_files()
    
    print(f"Deprecated {deprecated_count} files/directories")
    print(f"Deprecated items can be found in: {DEPRECATED_PATH}")
