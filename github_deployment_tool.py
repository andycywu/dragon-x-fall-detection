#!/usr/bin/env python3
"""
GitHub Deployment Script for Dragon X Fall Detection
Automates the process of deploying code to GitHub and pulling it to the device cloud
"""

import os
import sys
import time
import subprocess
import argparse
import logging
import json
import platform
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_REPO_URL = "https://github.com/username/dragon-x-fall-detection.git"
DEFAULT_SSH_KEY = "qdc_id_2025-8-11_62.pem"
DEFAULT_USERNAME = "hcktest"
DEFAULT_PORT = 2222
DEFAULT_TARGET_DIR = "C:/dragon_x_fall_detection"

def run_command(command, verbose=True, check=False):
    """Run a shell command and return output
    
    Args:
        command (str): Command to run
        verbose (bool): Whether to log the command
        check (bool): Whether to raise an exception on non-zero exit
        
    Returns:
        tuple: (success, output) where success is a boolean and output is the command output
    """
    if verbose:
        logger.info(f"Running: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Command failed with code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            return False, result.stderr
        
        return True, result.stdout
    except Exception as e:
        logger.error(f"Exception running command: {e}")
        return False, str(e)

def get_git_status(repo_dir):
    """Get the current git status
    
    Args:
        repo_dir (str): Repository directory
        
    Returns:
        dict: Git status information
    """
    logger.info(f"Getting git status for {repo_dir}")
    
    git_status = {}
    
    # Check if repo exists
    if not os.path.exists(os.path.join(repo_dir, ".git")):
        return {"initialized": False}
    
    # Get current branch
    success, output = run_command(f"cd {repo_dir} && git rev-parse --abbrev-ref HEAD", verbose=False)
    if success:
        git_status["branch"] = output.strip()
    
    # Get remote URL
    success, output = run_command(f"cd {repo_dir} && git config --get remote.origin.url", verbose=False)
    if success:
        git_status["remote"] = output.strip()
    
    # Get modified files
    success, output = run_command(f"cd {repo_dir} && git status --porcelain", verbose=False)
    if success:
        modified_files = [line.strip() for line in output.splitlines() if line.strip()]
        git_status["modified_files"] = modified_files
        git_status["has_changes"] = len(modified_files) > 0
    
    # Get last commit
    success, output = run_command(f"cd {repo_dir} && git log -1 --pretty=format:\"%h|%an|%at|%s\"", verbose=False)
    if success:
        try:
            commit_hash, author, timestamp, message = output.strip().split("|", 3)
            git_status["last_commit"] = {
                "hash": commit_hash,
                "author": author,
                "timestamp": int(timestamp),
                "message": message
            }
        except:
            pass
    
    git_status["initialized"] = True
    return git_status

def init_git_repo(repo_dir, repo_url=None):
    """Initialize a git repository
    
    Args:
        repo_dir (str): Repository directory
        repo_url (str): Optional repository URL
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Create directory if it doesn't exist
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir, exist_ok=True)
    
    # Check if git is already initialized
    if os.path.exists(os.path.join(repo_dir, ".git")):
        logger.info(f"Git repository already initialized in {repo_dir}")
        return True
    
    # Initialize git
    logger.info(f"Initializing git repository in {repo_dir}")
    success, _ = run_command(f"cd {repo_dir} && git init")
    if not success:
        return False
    
    # Configure git
    run_command(f"cd {repo_dir} && git config user.name \"Dragon X Developer\"")
    run_command(f"cd {repo_dir} && git config user.email \"dragon-x-dev@example.com\"")
    
    # Add remote if provided
    if repo_url:
        logger.info(f"Adding remote: {repo_url}")
        run_command(f"cd {repo_dir} && git remote add origin {repo_url}")
    
    return True

def push_to_github(repo_dir, commit_message=None, branch="main"):
    """Push changes to GitHub
    
    Args:
        repo_dir (str): Repository directory
        commit_message (str): Commit message
        branch (str): Branch to push to
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Check git status
    git_status = get_git_status(repo_dir)
    if not git_status.get("initialized", False):
        logger.error(f"Git not initialized in {repo_dir}")
        return False
    
    if not git_status.get("has_changes", False):
        logger.info("No changes to push")
        return True
    
    # Set default commit message if not provided
    if not commit_message:
        commit_message = f"Update Dragon X Fall Detection ({time.strftime('%Y-%m-%d %H:%M:%S')})"
    
    # Stage all changes
    logger.info("Staging changes...")
    success, _ = run_command(f"cd {repo_dir} && git add --all")
    if not success:
        return False
    
    # Commit changes
    logger.info(f"Committing with message: {commit_message}")
    success, _ = run_command(f"cd {repo_dir} && git commit -m \"{commit_message}\"")
    if not success:
        return False
    
    # Push changes
    logger.info(f"Pushing to branch: {branch}")
    success, output = run_command(f"cd {repo_dir} && git push -u origin {branch}")
    if not success:
        # If branch doesn't exist, create it
        if "error: src refspec" in output or "error: failed to push" in output:
            logger.info(f"Branch {branch} doesn't exist. Creating...")
            run_command(f"cd {repo_dir} && git checkout -b {branch}")
            success, output = run_command(f"cd {repo_dir} && git push -u origin {branch}")
            if not success:
                return False
    
    logger.info("Successfully pushed to GitHub")
    return True

def pull_from_github_to_device(ssh_key, username, port, target_dir, repo_url, branch="main"):
    """Pull code from GitHub to the device
    
    Args:
        ssh_key (str): SSH key file
        username (str): SSH username
        port (int): SSH port
        target_dir (str): Target directory on the device
        repo_url (str): Repository URL
        branch (str): Branch to pull from
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Pulling code from GitHub to device: {username}@localhost:{target_dir}")
    
    # Check if SSH connection works
    command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no -o ConnectTimeout=5 {username}@localhost "echo Connection successful"'
    success, _ = run_command(command)
    if not success:
        logger.error("SSH connection failed")
        return False
    
    # Check if git is installed on the device
    command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@localhost "git --version"'
    success, _ = run_command(command)
    if not success:
        logger.error("Git not installed on the device")
        return False
    
    # Check if repo directory exists
    command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@localhost "if exist {target_dir} (echo yes) else (echo no)"'
    success, output = run_command(command)
    
    if success and "yes" in output:
        # Directory exists, check if it's a git repo
        command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@localhost "if exist {target_dir}\\.git (echo yes) else (echo no)"'
        success, output = run_command(command)
        
        if success and "yes" in output:
            # Git repo exists, pull changes
            logger.info("Git repository exists. Pulling changes...")
            command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@localhost "cd {target_dir} && git pull origin {branch}"'
            success, _ = run_command(command)
            return success
        else:
            # Directory exists but not a git repo
            logger.error(f"Directory {target_dir} exists but is not a git repository")
            return False
    else:
        # Directory doesn't exist, clone repo
        logger.info(f"Directory {target_dir} doesn't exist. Cloning repository...")
        
        # Create parent directory if needed
        parent_dir = os.path.dirname(target_dir)
        if parent_dir:
            command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@localhost "mkdir -p {parent_dir}"'
            run_command(command)
        
        # Clone repo
        command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@localhost "git clone -b {branch} {repo_url} {target_dir}"'
        success, _ = run_command(command)
        return success

def get_project_files(directory):
    """Get all project files excluding git-related files and certain patterns
    
    Args:
        directory (str): Directory to scan
        
    Returns:
        list: List of project files
    """
    project_files = []
    
    exclude_dirs = [".git", "__pycache__", ".history", ".idea", ".vscode"]
    exclude_extensions = [".pyc", ".pyo", ".pyd", ".git", ".DS_Store"]
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            # Skip excluded extensions
            if any(file.endswith(ext) for ext in exclude_extensions):
                continue
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, directory)
            project_files.append(rel_path)
    
    return project_files

def setup_github_repo(repo_dir, repo_url=None):
    """Set up GitHub repository with a proper structure
    
    Args:
        repo_dir (str): Repository directory
        repo_url (str): Optional repository URL
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Initialize git repo
    if not init_git_repo(repo_dir, repo_url):
        return False
    
    # Create README.md if it doesn't exist
    readme_path = os.path.join(repo_dir, "README.md")
    if not os.path.exists(readme_path):
        logger.info("Creating README.md")
        with open(readme_path, "w") as f:
            f.write("# Dragon X Fall Detection\n\n")
            f.write("Fall detection system for Snapdragon X Elite\n\n")
            f.write("## Overview\n\n")
            f.write("This project implements a fall detection system for Snapdragon X Elite using computer vision and machine learning.\n\n")
            f.write("## Features\n\n")
            f.write("- Real-time fall detection using camera feed\n")
            f.write("- Support for AWS Virtual Camera RFC\n")
            f.write("- Windows compatibility on Snapdragon X Elite\n")
    
    # Create .gitignore if it doesn't exist
    gitignore_path = os.path.join(repo_dir, ".gitignore")
    if not os.path.exists(gitignore_path):
        logger.info("Creating .gitignore")
        with open(gitignore_path, "w") as f:
            f.write("# Python\n")
            f.write("__pycache__/\n")
            f.write("*.py[cod]\n")
            f.write("*$py.class\n")
            f.write("*.so\n")
            f.write(".Python\n")
            f.write("env/\n")
            f.write("build/\n")
            f.write("develop-eggs/\n")
            f.write("dist/\n")
            f.write("downloads/\n")
            f.write("eggs/\n")
            f.write(".eggs/\n")
            f.write("lib/\n")
            f.write("lib64/\n")
            f.write("parts/\n")
            f.write("sdist/\n")
            f.write("var/\n")
            f.write("*.egg-info/\n")
            f.write(".installed.cfg\n")
            f.write("*.egg\n\n")
            f.write("# OS files\n")
            f.write(".DS_Store\n")
            f.write("Thumbs.db\n\n")
            f.write("# Editor files\n")
            f.write(".idea/\n")
            f.write(".vscode/\n")
            f.write("*.swp\n")
            f.write("*.swo\n\n")
            f.write("# Project-specific\n")
            f.write("*.jpg\n")
            f.write("*.png\n")
            f.write("*.mp4\n")
            f.write("*.avi\n")
            f.write("*.log\n")
    
    return True

def deploy_project_to_github(source_dir, repo_dir, repo_url=None, commit_message=None, files=None):
    """Deploy project to GitHub
    
    Args:
        source_dir (str): Source directory containing the project
        repo_dir (str): Repository directory (where to initialize git)
        repo_url (str): Optional repository URL
        commit_message (str): Optional commit message
        files (list): Optional list of files to copy (if None, all files are copied)
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Setup GitHub repo
    if not setup_github_repo(repo_dir, repo_url):
        return False
    
    # Get files to copy if not provided
    if files is None:
        files = get_project_files(source_dir)
    
    # Copy files
    logger.info(f"Copying {len(files)} files from {source_dir} to {repo_dir}...")
    
    for file in files:
        source_file = os.path.join(source_dir, file)
        target_file = os.path.join(repo_dir, file)
        
        # Create directories if needed
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        
        # Copy file
        try:
            with open(source_file, "rb") as src, open(target_file, "wb") as dst:
                dst.write(src.read())
        except Exception as e:
            logger.error(f"Error copying {file}: {e}")
    
    # Push to GitHub
    return push_to_github(repo_dir, commit_message)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="GitHub Deployment for Dragon X Fall Detection")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize GitHub repository")
    init_parser.add_argument("--repo-dir", required=True, help="Repository directory")
    init_parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help=f"Repository URL (default: {DEFAULT_REPO_URL})")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy project to GitHub")
    deploy_parser.add_argument("--source-dir", required=True, help="Source directory")
    deploy_parser.add_argument("--repo-dir", required=True, help="Repository directory")
    deploy_parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help=f"Repository URL (default: {DEFAULT_REPO_URL})")
    deploy_parser.add_argument("--message", help="Commit message")
    
    # Pull command
    pull_parser = subparsers.add_parser("pull", help="Pull code from GitHub to device")
    pull_parser.add_argument("--ssh-key", default=DEFAULT_SSH_KEY, help=f"SSH key file (default: {DEFAULT_SSH_KEY})")
    pull_parser.add_argument("--username", default=DEFAULT_USERNAME, help=f"SSH username (default: {DEFAULT_USERNAME})")
    pull_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"SSH port (default: {DEFAULT_PORT})")
    pull_parser.add_argument("--target-dir", default=DEFAULT_TARGET_DIR, help=f"Target directory (default: {DEFAULT_TARGET_DIR})")
    pull_parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help=f"Repository URL (default: {DEFAULT_REPO_URL})")
    pull_parser.add_argument("--branch", default="main", help="Branch to pull from (default: main)")
    
    # Full workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Run full deployment workflow")
    workflow_parser.add_argument("--source-dir", required=True, help="Source directory")
    workflow_parser.add_argument("--repo-dir", required=True, help="Repository directory")
    workflow_parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help=f"Repository URL (default: {DEFAULT_REPO_URL})")
    workflow_parser.add_argument("--ssh-key", default=DEFAULT_SSH_KEY, help=f"SSH key file (default: {DEFAULT_SSH_KEY})")
    workflow_parser.add_argument("--username", default=DEFAULT_USERNAME, help=f"SSH username (default: {DEFAULT_USERNAME})")
    workflow_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"SSH port (default: {DEFAULT_PORT})")
    workflow_parser.add_argument("--target-dir", default=DEFAULT_TARGET_DIR, help=f"Target directory (default: {DEFAULT_TARGET_DIR})")
    workflow_parser.add_argument("--branch", default="main", help="Branch to use (default: main)")
    workflow_parser.add_argument("--message", help="Commit message")
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == "init":
        success = setup_github_repo(args.repo_dir, args.repo_url)
        if success:
            print(f"GitHub repository initialized in {args.repo_dir}")
        else:
            print("Failed to initialize GitHub repository")
            return 1
    
    elif args.command == "deploy":
        success = deploy_project_to_github(args.source_dir, args.repo_dir, args.repo_url, args.message)
        if success:
            print(f"Project deployed to GitHub repository in {args.repo_dir}")
        else:
            print("Failed to deploy project to GitHub")
            return 1
    
    elif args.command == "pull":
        success = pull_from_github_to_device(args.ssh_key, args.username, args.port, args.target_dir, args.repo_url, args.branch)
        if success:
            print(f"Code pulled from GitHub to device: {args.username}@localhost:{args.target_dir}")
        else:
            print("Failed to pull code from GitHub to device")
            return 1
    
    elif args.command == "workflow":
        # Step 1: Initialize GitHub repo
        print("Step 1: Initializing GitHub repository...")
        success = setup_github_repo(args.repo_dir, args.repo_url)
        if not success:
            print("Failed to initialize GitHub repository")
            return 1
        
        # Step 2: Deploy project to GitHub
        print("Step 2: Deploying project to GitHub...")
        success = deploy_project_to_github(args.source_dir, args.repo_dir, args.repo_url, args.message)
        if not success:
            print("Failed to deploy project to GitHub")
            return 1
        
        # Step 3: Pull code from GitHub to device
        print("Step 3: Pulling code from GitHub to device...")
        success = pull_from_github_to_device(args.ssh_key, args.username, args.port, args.target_dir, args.repo_url, args.branch)
        if not success:
            print("Failed to pull code from GitHub to device")
            return 1
        
        print("\nDeployment workflow completed successfully!")
        print(f"Source: {args.source_dir}")
        print(f"GitHub: {args.repo_dir}")
        print(f"Device: {args.username}@localhost:{args.target_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
