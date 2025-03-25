from git import Repo, GitCommandError
import os

def commit_and_push(repo_dir: str, commit_message: str) -> None:
    """
    Adds all changes in the repo, commits with the provided message, and pushes to the remote repository if one exists.
    
    Parameters:
        repo_dir (str): Path to the local Git repository.
        commit_message (str): The commit message to use.
    """
    try:
        repo = Repo(repo_dir)
    except Exception as e:
        print(f"Error: Unable to locate a Git repository at {repo_dir}. {e}")
        return

    try:
        # Stage all changes (including untracked files)
        repo.git.add('--all')
        
        # Check if there are changes to commit
        if repo.is_dirty(untracked_files=True):
            commit = repo.index.commit(commit_message)
            print(f"Committed changes: {commit.hexsha}")
        else:
            print("No changes detected. Nothing to commit.")

        # Attempt to push if a remote exists
        if repo.remotes:
            # Try to use remote 'origin' if it exists, otherwise use the first available remote
            remote = repo.remotes.origin if "origin" in repo.remotes else repo.remotes[0]
            try:
                # Check if the local 'master' branch exists
                if 'master' not in repo.heads:
                    print("Local 'master' branch does not exist. Creating it...")
                    repo.git.checkout('-b', 'master')  # Create and switch to 'master' branch

                # Pull changes from the remote 'master' branch with --allow-unrelated-histories
                print("Pulling changes from remote 'master' branch...")
                pull_output = repo.git.pull(remote.name, 'master', '--allow-unrelated-histories')

                # Check if there are merge conflicts
                if "CONFLICT" in pull_output:
                    print("Merge conflict detected. Please resolve the conflicts manually.")
                    print("After resolving conflicts, stage the files and run the script again.")
                    return

                # Check if the remote 'master' branch exists
                remote_master_exists = any(ref.name == 'refs/heads/master' for ref in remote.refs)
                
                if not remote_master_exists:
                    print("Remote 'master' branch does not exist. Creating it...")
                    repo.git.push(remote.name, 'master:master', '--set-upstream')
                else:
                    # Push changes
                    push_info = remote.push()
                    for info in push_info:
                        if info.flags & info.ERROR:
                            print(f"Push failed: {info.summary}")
                        else:
                            print(f"Push succeeded: {info.summary}")
            except GitCommandError as push_error:
                print(f"Git push error: {push_error}")
        else:
            print("No remote found. Skipping push.")

    except GitCommandError as git_error:
        print(f"Git command error: {git_error}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage:
if __name__ == "__main__":
    # Replace with your local repository path and commit message
    repository_path = r"G:\AI\Lyra"  # Path to your local repository
    message = "Automated commit from git_integration.py"
    commit_and_push(repository_path, message)