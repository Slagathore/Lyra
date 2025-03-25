"""
GitHub integration for Lyra to interact with repositories.
"""
import os
import json
import requests
from typing import Dict, Any, Optional, List 
# Removing unused imports

try:
    import subprocess
    HAS_SUBPROCESS = True
except ImportError:
    HAS_SUBPROCESS = False

from pathlib import Path

class GitHubIntegration:
    """A class to interact with GitHub repositories"""

    def __init__(self, token_file=None):
        """Initialize with a token file or environment variable"""
        self.token = os.environ.get("GITHUB_TOKEN")
        if token_file:
            try:
                token_path = Path(token_file)
                if token_path.exists():
                    with open(token_path, 'r') as f:
                        creds = json.load(f)
                        if isinstance(creds, dict) and "github" in creds:
                            self.token = creds["github"].get("token", self.token)
                        else:
                            self.token = creds
            except Exception as e:
                print(f"Error loading GitHub token: {e}")

        self.headers = {"Authorization": f"token {self.token}"} if self.token else {}
        self.api_base = "https://api.github.com"

    def test_connection(self) -> bool:
        """Test the GitHub API connection"""
        if not self.token:
            print("No GitHub token found")
            return False

        try:
            response = requests.get(f"{self.api_base}/user", headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            print(f"Error testing GitHub connection: {e}")
            return False

    def create_pull_request(self, owner: str, repo: str, title: str, body: str, 
                          head: str, base: str = "master") -> Optional[Dict[str, Any]]:
        """Create a pull request"""
        try:
            data = {
                "title": title,
                "body": body,
                "head": head,
                "base": base
            }
            response = requests.post(
                f"{self.api_base}/repos/{owner}/{repo}/pulls",
                headers=self.headers,
                json=data
            )
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Error creating PR: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            print(f"Error creating pull request: {e}")
            return None

    def clone_repo(self, owner: str, repo: str, destination: str) -> bool:
        """Clone a repository to a local directory"""
        try:
            cmd = ["git", "clone", f"https://github.com/{owner}/{repo}.git", destination]
            result = subprocess.run(cmd, check=True, capture_output=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error cloning repository: {e}")
            return False
