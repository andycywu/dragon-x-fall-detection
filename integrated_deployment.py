#!/usr/bin/env python3
"""
Integrated Deployment Script for Dragon X Fall Detection
Combines direct deployment, AWS Virtual Camera integration, and GitHub deployment
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
DEFAULT_SSH_KEY = "qdc_id_2025-8-11_62.pem"
DEFAULT_USERNAME = "hcktest"
DEFAULT_PORT = 2222
DEFAULT_TARGET_DIR = "C:/dragon_x_fall_detection"
DEFAULT_REPO_URL = "https://github.com/username/dragon-x-fall-detection.git"

def run_command(command, verbose=True, check=False):
    """Run a shell command and return output"""
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

def check_ssh_connection(ssh_key, username, port):
    """Check if SSH connection to the device is working"""
    logger.info("Checking SSH connection to the device...")
    
    command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no -o ConnectTimeout=5 {username}@localhost "echo Connection successful"'
    success, output = run_command(command)
    
    if success:
        logger.info("SSH connection successful!")
        return True
    else:
        logger.error("SSH connection failed")
        return False

def check_requirements():
    """Check if all required tools are installed"""
    requirements = {
        "git": "git --version",
        "ssh": "ssh -V",
        "scp": "scp -V",
        "python": "python --version"
    }
    
    missing = []
    
    for tool, command in requirements.items():
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode != 0:
                missing.append(tool)
        except:
            missing.append(tool)
    
    return missing

def find_deployment_scripts(current_dir):
    """Find deployment scripts in the current directory"""
    scripts = {
        "direct": os.path.join(current_dir, "deploy_to_device_cloud.py"),
        "aws_camera": os.path.join(current_dir, "aws_virtual_camera_integration_tool.py"),
        "github": os.path.join(current_dir, "github_deployment_tool.py")
    }
    
    # Check which scripts exist
    for key in list(scripts.keys()):
        if not os.path.exists(scripts[key]):
            logger.warning(f"Script not found: {scripts[key]}")
            scripts[key] = None
    
    return scripts

def run_direct_deployment(script_path, args):
    """Run direct deployment script"""
    command = f"python {script_path}"
    
    if args.ssh_key:
        command += f" --ssh-key \"{args.ssh_key}\""
    if args.username:
        command += f" --username {args.username}"
    if args.port:
        command += f" --port {args.port}"
    if args.target_dir:
        command += f" --target-dir \"{args.target_dir}\""
    if args.source_dir:
        command += f" --source-dir \"{args.source_dir}\""
    if args.core_only:
        command += " --core-only"
    if args.skip_test_images:
        command += " --skip-test-images"
    
    logger.info("Running direct deployment...")
    return run_command(command, check=False)

def run_aws_camera_deployment(script_path, args):
    """Run AWS Virtual Camera integration deployment"""
    command = f"python {script_path} deploy"
    
    if args.ssh_key:
        command += f" --ssh-key \"{args.ssh_key}\""
    if args.username:
        command += f" --username {args.username}"
    if args.port:
        command += f" --port {args.port}"
    if args.target_dir:
        command += f" --target \"{args.target_dir}\""
    if args.source_dir:
        command += f" --source \"{args.source_dir}\""
    
    logger.info("Running AWS Camera deployment...")
    return run_command(command, check=False)

def run_github_deployment(script_path, args):
    """Run GitHub deployment script"""
    if not args.repo_dir or not args.repo_url:
        logger.error("Repository directory and URL required for GitHub deployment")
        return False, "Repository directory and URL required"
    
    command = f"python {script_path} workflow"
    
    if args.source_dir:
        command += f" --source-dir \"{args.source_dir}\""
    if args.repo_dir:
        command += f" --repo-dir \"{args.repo_dir}\""
    if args.repo_url:
        command += f" --repo-url \"{args.repo_url}\""
    if args.ssh_key:
        command += f" --ssh-key \"{args.ssh_key}\""
    if args.username:
        command += f" --username {args.username}"
    if args.port:
        command += f" --port {args.port}"
    if args.target_dir:
        command += f" --target-dir \"{args.target_dir}\""
    if args.branch:
        command += f" --branch {args.branch}"
    if args.message:
        command += f" --message \"{args.message}\""
    
    logger.info("Running GitHub deployment workflow...")
    return run_command(command, check=False)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Integrated Deployment for Dragon X Fall Detection")
    
    # Deployment method
    parser.add_argument("--method", choices=["direct", "github", "aws-camera", "all"], default="all",
                      help="Deployment method (default: all)")
    
    # Common arguments
    parser.add_argument("--ssh-key", default=DEFAULT_SSH_KEY, help=f"SSH key file (default: {DEFAULT_SSH_KEY})")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help=f"SSH username (default: {DEFAULT_USERNAME})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"SSH port (default: {DEFAULT_PORT})")
    parser.add_argument("--target-dir", default=DEFAULT_TARGET_DIR, help=f"Target directory (default: {DEFAULT_TARGET_DIR})")
    parser.add_argument("--source-dir", default=os.getcwd(), help="Source directory (default: current directory)")
    
    # Direct deployment arguments
    parser.add_argument("--core-only", action="store_true", help="Deploy only core files (direct method)")
    parser.add_argument("--skip-test-images", action="store_true", help="Skip deploying test images (direct method)")
    
    # GitHub deployment arguments
    parser.add_argument("--repo-dir", help="Repository directory (GitHub method)")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help=f"Repository URL (default: {DEFAULT_REPO_URL})")
    parser.add_argument("--branch", default="main", help="Branch to use (default: main)")
    parser.add_argument("--message", help="Commit message")
    
    args = parser.parse_args()
    
    # Check requirements
    missing_tools = check_requirements()
    if missing_tools:
        logger.error(f"Missing required tools: {', '.join(missing_tools)}")
        logger.error("Please install the missing tools and try again.")
        return 1
    
    # Find deployment scripts
    scripts = find_deployment_scripts(os.path.dirname(os.path.abspath(__file__)))
    
    # Check SSH connection
    if not check_ssh_connection(args.ssh_key, args.username, args.port):
        logger.error("Cannot proceed without SSH connection")
        return 1
    
    # Run selected deployment method
    if args.method == "direct" or args.method == "all":
        if scripts["direct"]:
            success, output = run_direct_deployment(scripts["direct"], args)
            if not success:
                logger.error("Direct deployment failed")
                if args.method != "all":
                    return 1
        else:
            logger.error("Direct deployment script not found")
            if args.method != "all":
                return 1
    
    if args.method == "aws-camera" or args.method == "all":
        if scripts["aws_camera"]:
            success, output = run_aws_camera_deployment(scripts["aws_camera"], args)
            if not success:
                logger.error("AWS Camera deployment failed")
                if args.method != "all":
                    return 1
        else:
            logger.error("AWS Camera deployment script not found")
            if args.method != "all":
                return 1
    
    if args.method == "github" or args.method == "all":
        if scripts["github"]:
            # For GitHub deployment, repo_dir is required
            if not args.repo_dir and args.method == "github":
                logger.error("Repository directory (--repo-dir) is required for GitHub deployment")
                return 1
            
            # Use a default repo_dir if not specified for "all" method
            if not args.repo_dir and args.method == "all":
                args.repo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "github_repo")
                logger.info(f"Using default repository directory: {args.repo_dir}")
            
            # Proceed with GitHub deployment if repo_dir is set
            if args.repo_dir:
                success, output = run_github_deployment(scripts["github"], args)
                if not success:
                    logger.error("GitHub deployment failed")
                    if args.method != "all":
                        return 1
        else:
            logger.error("GitHub deployment script not found")
            if args.method != "all":
                return 1
    
    logger.info("Deployment completed!")
    
    # Print instructions
    if args.method == "all" or args.method == "direct":
        print("\nTo run the core demo on the device, execute:")
        print(f"  python {args.target_dir}\\snapdragon_realtime_demo_windows.py")
    
    if args.method == "all" or args.method == "aws-camera":
        print("\nTo test camera functionality:")
        print(f"  python {args.target_dir}\\aws_virtual_camera_test_windows.py --list")
        print(f"  python {args.target_dir}\\aws_virtual_camera_test_windows.py")
    
    if args.method == "all" or args.method == "github":
        print("\nTo update from GitHub in the future:")
        print(f"  cd {args.target_dir}")
        print("  git pull")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
