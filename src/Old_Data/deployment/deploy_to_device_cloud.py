#!/usr/bin/env python3
"""
Deployment Script for Dragon X Fall Detection
Deploys files from Mac development environment to Qualcomm Device Cloud Windows environment
"""

import os
import sys
import time
import subprocess
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_SSH_KEY = "qdc_id_2025-8-11_62.pem"
DEFAULT_USERNAME = "hcktest"
DEFAULT_PORT = 2222
DEFAULT_TARGET_DIR = "C:/dragon_x_fall_detection"

def run_command(command, verbose=True):
    """Run a shell command and return output"""
    if verbose:
        logger.info(f"Running: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,  # Don't raise exception on non-zero exit
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

def create_remote_directory(ssh_key, username, port, directory):
    """Create a directory on the remote device"""
    logger.info(f"Creating remote directory: {directory}")
    
    command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@localhost "mkdir -p {directory}"'
    success, output = run_command(command)
    
    if success:
        logger.info(f"Created directory: {directory}")
        return True
    else:
        logger.error(f"Failed to create directory: {directory}")
        return False

def deploy_file(ssh_key, username, port, local_file, remote_file):
    """Deploy a single file to the remote device"""
    logger.info(f"Deploying file: {local_file} -> {remote_file}")
    
    if not os.path.exists(local_file):
        logger.warning(f"Local file doesn't exist: {local_file}")
        return False
    
    # Create remote directory if needed
    remote_dir = os.path.dirname(remote_file)
    if remote_dir:
        create_remote_directory(ssh_key, username, port, remote_dir)
    
    # Copy file
    command = f'scp -i "{ssh_key}" -P {port} -o StrictHostKeyChecking=no "{local_file}" {username}@localhost:"{remote_file}"'
    success, output = run_command(command, verbose=False)
    
    if success:
        logger.info(f"Deployed: {os.path.basename(local_file)}")
        return True
    else:
        logger.error(f"Failed to deploy: {os.path.basename(local_file)}")
        return False

def get_deployment_files(core_only=False):
    """Get the list of files to deploy, organized by priority"""
    core_files = [
        # Core detection modules (ASCII versions for Windows)
        "unified_ai_detector_windows.py",
        "dragon_x_fall_detection_system_windows.py",
        "fall_detector.py",
        "fall_detector_opencv.py",
        
        # AWS Virtual Camera integration
        "aws_virtual_camera_rfc.py",
        "aws_virtual_camera_test_windows.py",
        
        # Snapdragon demos (Windows versions)
        "snapdragon_realtime_demo_windows.py", 
        "snapdragon_video_demo_windows.py",
        "snapdragon_performance_benchmark_windows.py",
    ]
    
    if core_only:
        return core_files
    
    extended_files = [
        # Core detection modules (original versions)
        "unified_ai_detector.py",
        "unified_ai_detector_ascii.py",
        "dragon_x_fall_detection_system.py",
        
        # QAI Hub integration
        "qai_hub_integration.py",
        "qai_hub_onnx_integration.py",
        "real_qai_hub_onnx_detector.py",
        
        # Standard MediaPipe modules
        "fall_detector.py", 
        "fall_detector_opencv.py",
        
        # Configuration files
        "cross_platform_config.json",
        
        # Snapdragon demos (standard versions)
        "snapdragon_realtime_demo.py",
        "snapdragon_video_demo.py",
        "snapdragon_performance_benchmark.py",
        
        # Hackathon demo
        "hackathon_demo.py",
        "hackathon_launcher.py",
        "hackathon_main.py",
        
        # Documentation
        "README_HACKATHON.md",
        "HACKATHON_FINAL_REPORT.md",
    ]
    
    return core_files + extended_files

def deploy_files(ssh_key, username, port, target_dir, files, source_dir):
    """Deploy multiple files to the remote device"""
    logger.info(f"Deploying {len(files)} files to {username}@localhost:{target_dir}")
    
    # Create target directory
    create_remote_directory(ssh_key, username, port, target_dir)
    
    # Deploy files
    successful = 0
    failed = 0
    
    for local_file in files:
        local_path = os.path.join(source_dir, local_file)
        remote_path = f"{target_dir}/{local_file.replace('/', '\\')}"
        
        if deploy_file(ssh_key, username, port, local_path, remote_path):
            successful += 1
        else:
            failed += 1
    
    logger.info(f"Deployment summary: {successful} successful, {failed} failed")
    return successful, failed

def deploy_test_images(ssh_key, username, port, target_dir, source_dir):
    """Deploy test images to the remote device"""
    test_images_dir = os.path.join(source_dir, "test_images")
    if not os.path.exists(test_images_dir) or not os.path.isdir(test_images_dir):
        logger.warning("Test images directory not found, skipping")
        return 0, 0
    
    # Create target directory
    remote_test_dir = f"{target_dir}/test_images"
    create_remote_directory(ssh_key, username, port, remote_test_dir)
    
    # Find image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    
    for filename in os.listdir(test_images_dir):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            image_files.append(os.path.join("test_images", filename))
    
    logger.info(f"Found {len(image_files)} test images to deploy")
    
    # Deploy images
    successful = 0
    failed = 0
    
    for local_file in image_files:
        local_path = os.path.join(source_dir, local_file)
        remote_path = f"{target_dir}/{local_file.replace('/', '\\')}"
        
        if deploy_file(ssh_key, username, port, local_path, remote_path):
            successful += 1
        else:
            failed += 1
    
    logger.info(f"Test images deployment summary: {successful} successful, {failed} failed")
    return successful, failed

def main():
    parser = argparse.ArgumentParser(description="Deploy Dragon X Fall Detection to Qualcomm Device Cloud")
    parser.add_argument("--ssh-key", default=DEFAULT_SSH_KEY, help=f"SSH key file (default: {DEFAULT_SSH_KEY})")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help=f"SSH username (default: {DEFAULT_USERNAME})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"SSH port (default: {DEFAULT_PORT})")
    parser.add_argument("--target-dir", default=DEFAULT_TARGET_DIR, help=f"Target directory (default: {DEFAULT_TARGET_DIR})")
    parser.add_argument("--source-dir", default=os.getcwd(), help="Source directory (default: current directory)")
    parser.add_argument("--core-only", action="store_true", help="Deploy only core files")
    parser.add_argument("--skip-test-images", action="store_true", help="Skip deploying test images")
    parser.add_argument("--test-connection", action="store_true", help="Only test SSH connection")
    
    args = parser.parse_args()
    
    # Check SSH connection
    if not check_ssh_connection(args.ssh_key, args.username, args.port):
        logger.error("Cannot proceed without SSH connection")
        return 1
    
    if args.test_connection:
        logger.info("Connection test successful, exiting")
        return 0
    
    # Get files to deploy
    files = get_deployment_files(args.core_only)
    
    # Deploy files
    deploy_files(args.ssh_key, args.username, args.port, args.target_dir, files, args.source_dir)
    
    # Deploy test images if needed
    if not args.skip_test_images:
        deploy_test_images(args.ssh_key, args.username, args.port, args.target_dir, args.source_dir)
    
    logger.info("Deployment completed")
    
    # Print instructions
    print("\nDeployment completed!")
    print("\nTo run the core demo on the device, execute:")
    print(f"  python {args.target_dir}\\snapdragon_realtime_demo_windows.py")
    print("\nTo test camera functionality:")
    print(f"  python {args.target_dir}\\aws_virtual_camera_test_windows.py --list")
    print("\nTo run performance benchmark:")
    print(f"  python {args.target_dir}\\snapdragon_performance_benchmark_windows.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
