import subprocess
import os
import sys
import argparse
import logging
import shutil
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("github_update")

class GitHubUpdater:
    """Handles pushing updates to GitHub repository."""
    
    def __init__(self, repo_path=None):
        """Initialize with the repository path."""
        self.repo_path = Path(repo_path) if repo_path else Path(os.getcwd())
        logger.info(f"Initialized GitHub updater for repo at: {self.repo_path}")
        
        # Check if git is installed
        if not self._is_git_installed():
            raise ValueError("Git is not installed or not found in the system PATH")
        
        # Verify that we're in a git repository
        if not self._is_git_repo():
            raise ValueError(f"The directory {self.repo_path} is not a git repository")
    
    def _is_git_installed(self):
        """Check if git is installed and available."""
        try:
            # Check if git is in PATH
            git_path = shutil.which("git")
            if git_path:
                logger.info(f"Git found at: {git_path}")
                return True
            else:
                # Try common git installation paths
                common_paths = [
                    r"C:\Program Files\Git\bin\git.exe",
                    r"C:\Program Files (x86)\Git\bin\git.exe",
                    os.path.expanduser("~") + r"\AppData\Local\Programs\Git\bin\git.exe"
                ]
                
                for path in common_paths:
                    if os.path.exists(path):
                        logger.info(f"Git found at alternative path: {path}")
                        # Add to environment PATH for this process
                        os.environ["PATH"] += os.pathsep + os.path.dirname(path)
                        return True
                
                logger.error("Git not found in PATH or common installation locations")
                return False
        except Exception as e:
            logger.error(f"Error checking git installation: {e}")
            return False
    
    def _is_git_repo(self):
        """Check if the current directory is a git repository."""
        try:
            result = self._run_git_command(["status"])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Not a git repository: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error checking if directory is a git repository: {e}")
            return False
    
    def _run_git_command(self, args):
        """Run a git command and return the output."""
        try:
            # Try to get git executable path
            git_exe = shutil.which("git")
            if not git_exe:
                # If not in PATH, check common locations
                potential_paths = [
                    r"C:\Program Files\Git\bin\git.exe",
                    r"C:\Program Files (x86)\Git\bin\git.exe",
                    os.path.expanduser("~") + r"\AppData\Local\Programs\Git\bin\git.exe"
                ]
                
                for path in potential_paths:
                    if os.path.exists(path):
                        git_exe = path
                        break
            
            if not git_exe:
                raise FileNotFoundError("Git executable not found")
                
            logger.info(f"Running git command: {' '.join(args)}")
            process = subprocess.run(
                [git_exe] + args,
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            return process.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command error: {e.stderr.strip() if hasattr(e, 'stderr') else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error running git command: {e}")
            raise
    
    def check_status(self):
        """Check the current git status."""
        try:
            status_output = self._run_git_command(["status", "--porcelain"])
            
            if not status_output:
                logger.info("No changes to commit")
                return False, "No changes to commit"
            
            # Count number of changes
            changes = status_output.split('\n')
            added = sum(1 for line in changes if line.startswith('A ') or line.startswith('?? '))
            modified = sum(1 for line in changes if line.startswith('M '))
            deleted = sum(1 for line in changes if line.startswith('D '))
            
            logger.info(f"Found {len(changes)} change(s): {added} added, {modified} modified, {deleted} deleted")
            return True, {
                "total": len(changes),
                "added": added,
                "modified": modified,
                "deleted": deleted,
                "details": changes
            }
        except Exception as e:
            logger.error(f"Error checking git status: {e}")
            return False, str(e)
    
    def add_all_changes(self):
        """Stage all changes for commit."""
        try:
            result = self._run_git_command(["add", "--all"])
            logger.info("All changes staged for commit")
            return True, "All changes staged"
        except Exception as e:
            logger.error(f"Error staging changes: {e}")
            return False, str(e)
    
    def commit(self, message=None):
        """Commit staged changes with the given message."""
        if not message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Automatic update - {timestamp}"
        
        try:
            result = self._run_git_command(["commit", "-m", message])
            logger.info(f"Changes committed: {result}")
            return True, result
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            return False, str(e)
    
    def push(self, remote="origin", branch="main"):
        """Push committed changes to the remote repository."""
        try:
            # First check current branch
            current_branch = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
            if current_branch != branch:
                logger.warning(f"Current branch is {current_branch}, but pushing to {branch}")
            
            result = self._run_git_command(["push", remote, current_branch])
            logger.info(f"Changes pushed to {remote}/{current_branch}")
            return True, f"Pushed to {remote}/{current_branch}"
        except Exception as e:
            logger.error(f"Error pushing changes: {e}")
            return False, str(e)
    
    def update_github(self, commit_message=None, push=True, remote="origin", branch="main"):
        """Complete flow: add, commit, and push changes."""
        # Check if there are changes to commit
        has_changes, status = self.check_status()
        if not has_changes or (isinstance(status, dict) and status["total"] == 0):
            logger.info("No changes to update on GitHub")
            return False, "No changes detected"
        
        # Stage changes
        add_success, add_result = self.add_all_changes()
        if not add_success:
            return False, f"Failed to stage changes: {add_result}"
        
        # Commit changes
        commit_success, commit_result = self.commit(commit_message)
        if not commit_success:
            return False, f"Failed to commit changes: {commit_result}"
        
        # Push changes if requested
        if push:
            push_success, push_result = self.push(remote, branch)
            if not push_success:
                return False, f"Failed to push changes: {push_result}"
            return True, f"Successfully updated GitHub: {push_result}"
        
        return True, "Changes committed successfully, not pushed"
    
    def create_and_push_tag(self, tag_name, tag_message=None):
        """Create a new tag and push it to the remote."""
        if not tag_message:
            tag_message = f"Release {tag_name}"
        
        try:
            # Create annotated tag
            tag_result = self._run_git_command(["tag", "-a", tag_name, "-m", tag_message])
            logger.info(f"Created tag {tag_name}")
            
            # Push the tag
            push_result = self._run_git_command(["push", "origin", tag_name])
            logger.info(f"Pushed tag {tag_name} to origin")
            
            return True, f"Created and pushed tag {tag_name}"
        except Exception as e:
            logger.error(f"Error creating or pushing tag: {e}")
            return False, str(e)

def update_file(repo, path, message, content, branch="main"):
    """Update a file in the repository."""
    try:
        contents = repo.get_contents(path, ref=branch)
        repo.update_file(contents.path, message, content, contents.sha, branch=branch)
        logger.info(f"Updated {path}")
        return True
    except Exception as e:
        logger.error(f"Error updating {path}: {e}")
        return False

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Update GitHub repository with local changes")
    parser.add_argument("--message", "-m", type=str, help="Commit message (default: auto-generated timestamp)")
    parser.add_argument("--no-push", action="store_true", help="Commit changes without pushing")
    parser.add_argument("--remote", type=str, default="origin", help="Remote repository name")
    parser.add_argument("--branch", type=str, help="Branch name to push to (default: current branch)")
    parser.add_argument("--tag", type=str, help="Create and push a tag after committing")
    parser.add_argument("--tag-message", type=str, help="Message for the tag")
    parser.add_argument("--path", type=str, help="Path to the git repository (default: current directory)")
    args = parser.parse_args()
    
    try:
        # Check if git is installed first
        git_path = shutil.which("git")
        if not git_path:
            common_paths = [
                r"C:\Program Files\Git\bin\git.exe",
                r"C:\Program Files (x86)\Git\bin\git.exe",
                os.path.expanduser("~") + r"\AppData\Local\Programs\Git\bin\git.exe"
            ]
            
            git_found = False
            for path in common_paths:
                if os.path.exists(path):
                    os.environ["PATH"] += os.pathsep + os.path.dirname(path)
                    git_found = True
                    print(f"Found Git at {path}")
                    break
            
            if not git_found:
                print("❌ Error: Git is not installed or not in PATH")
                print("\nTo fix this issue:")
                print("1. Install Git from https://git-scm.com/downloads")
                print("2. Make sure to select the option to add Git to your PATH during installation")
                print("3. After installation, restart your terminal/command prompt and try again")
                return 1
        
        updater = GitHubUpdater(args.path)
        
        # Main update process
        success, result = updater.update_github(
            commit_message=args.message,
            push=not args.no_push,
            remote=args.remote,
            branch=args.branch
        )
        
        if success:
            print(f"✅ {result}")
            
            # Create and push tag if requested
            if args.tag and success:
                tag_success, tag_result = updater.create_and_push_tag(args.tag, args.tag_message)
                if tag_success:
                    print(f"🏷️ {tag_result}")
                else:
                    print(f"❌ Failed to create tag: {tag_result}")
                    return 1
        else:
            print(f"❌ {result}")
            return 1
        
        return 0
    except ValueError as e:
        print(f"❌ Error: {e}")
        if "git repository" in str(e).lower():
            print("\nThis directory is not a Git repository. To fix this:")
            print("1. Make sure you're in the correct directory")
            print("2. Initialize a git repository with: git init")
            print("3. Add a remote with: git remote add origin <your-github-url>")
        elif "git is not installed" in str(e).lower():
            print("\nTo fix this issue:")
            print("1. Install Git from https://git-scm.com/downloads")
            print("2. Make sure to select the option to add Git to your PATH during installation")
            print("3. After installation, restart your terminal/command prompt and try again")
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
