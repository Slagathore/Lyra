import os
import sys
import json
import argparse
from getpass import getpass
from pathlib import Path

def setup_github_credentials():
    """Set up GitHub credentials for Lyra's self-improvement module"""
    print("===== GitHub Integration Setup =====\n")
    print("This script will set up GitHub credentials for Lyra's self-improvement capabilities.")
    print("You can create a Personal Access Token at: https://github.com/settings/tokens")
    print("Recommended scopes: repo, workflow, user\n")
    
    # Create credentials directory if it doesn't exist
    creds_dir = Path("data/credentials")
    creds_dir.mkdir(parents=True, exist_ok=True)
    
    # Get GitHub info
    github_username = input("Enter your GitHub username: ").strip()
    github_token = getpass("Enter your GitHub Personal Access Token: ").strip()
    
    # Ask if this is a fork or a main repo
    is_fork = input("Is this a fork of a main repository? (y/n): ").lower() == 'y'
    
    # If it's a fork, get the upstream repo info
    upstream_repo = None
    if is_fork:
        upstream_repo = input("Enter the upstream repository (format: owner/repo): ").strip()
    
    # Create credentials file
    creds_file = creds_dir / "github_credentials.json"
    
    # Read existing credentials if file exists
    existing_creds = {}
    if creds_file.exists():
        try:
            with open(creds_file, 'r') as f:
                existing_creds = json.load(f)
        except json.JSONDecodeError:
            print("Warning: Existing credentials file is corrupted. Creating a new one.")
    
    # Update or create credentials
    github_credentials = {
        "username": github_username,
        "token": github_token,
        "is_fork": is_fork,
        "upstream_repo": upstream_repo if is_fork else None
    }
    
    # Merge with existing credentials
    existing_creds.update({"github": github_credentials})
    
    # Write credentials to file
    with open(creds_file, 'w') as f:
        json.dump(existing_creds, f, indent=2)
    
    # Also set the token as an environment variable
    # This is useful for CI/CD environments or scripts
    with open(os.path.join(creds_dir, "set_github_env.bat"), 'w') as f:
        f.write(f"@echo off\nset GITHUB_TOKEN={github_token}\n")
    
    print(f"\nCredentials saved to {creds_file}")
    print("To use these credentials in a script, run:")
    print(f"  call {os.path.join('data/credentials', 'set_github_env.bat')}")

def check_github_connection():
    """Test the GitHub connection with the stored credentials"""
    try:
        # Add the current directory to the path for module imports
        sys.path.append(".")
        
        # Also add src to system path if needed
        src_path = os.path.join(os.getcwd(), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
            
        try:
            from lyra.self_improvement.github_integration import GitHubIntegration
            
            # Try to initialize the GitHub integration
            gh = GitHubIntegration("data/credentials/github_credentials.json")
            
            # Test the connection
            if gh.test_connection():
                print("✓ GitHub connection successful!")
                return True
            else:
                print("✗ Failed to connect to GitHub. Please check your credentials.")
                return False
        except ImportError as e:
            print(f"✗ Could not import GitHub integration module: {e}")
            print("  Please run self_improvement.bat first to set up the module.")
            return False
    except Exception as e:
        print(f"✗ Error testing GitHub connection: {e}")
        return False

def main():
    """Main function for the GitHub setup script"""
    parser = argparse.ArgumentParser(description='Setup GitHub integration for Lyra')
    parser.add_argument('--test', action='store_true', help='Test the GitHub connection with existing credentials')
    args = parser.parse_args()
    
    if args.test:
        check_github_connection()
    else:
        setup_github_credentials()
        # Test the connection after setup
        print("\nTesting GitHub connection with the new credentials...")
        check_github_connection()

if __name__ == "__main__":
    main()
