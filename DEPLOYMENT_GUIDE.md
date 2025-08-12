# Dragon X Fall Detection Deployment Guide

This document provides detailed instructions for deploying the Dragon X Fall Detection system from a Mac development environment to the Qualcomm Device Cloud Windows environment.

## Prerequisites

The deployment system requires the following tools:

- Python 3.7+
- Git
- SSH client
- SCP file transfer tool
- SSH key (default: `qdc_id_2025-8-11_62.pem`)

## Deployment Methods Overview

We provide three deployment methods:

1. **Direct Deployment**: Deploy files directly to the target device via SSH/SCP
2. **AWS Virtual Camera Deployment**: Deploy and test AWS Virtual Camera related functionality
3. **GitHub Deployment**: Publish the project to GitHub and pull from the device

You can choose one or a combination of these methods. For daily development, GitHub deployment is recommended for easy updates and code management.

## Main Deployment Scripts

The system provides four main deployment scripts:

1. `integrated_deployment.py` - Integrates all deployment methods
2. `deploy_to_device_cloud.py` - Direct deployment to the device
3. `aws_virtual_camera_integration_tool.py` - AWS Virtual Camera deployment and testing
4. `github_deployment_tool.py` - GitHub publishing and pulling

### Integrated Deployment (Recommended)

The integrated deployment script combines all deployment methods and is the simplest to use:

```bash
# Use all deployment methods
python integrated_deployment.py

# Use only direct deployment
python integrated_deployment.py --method direct

# Use only GitHub deployment
python integrated_deployment.py --method github --repo-dir /path/to/repo --repo-url https://github.com/username/repo.git

# Deploy only AWS Virtual Camera related functionality
python integrated_deployment.py --method aws-camera
```

### Direct Deployment

The direct deployment script deploys files to the target device via SSH/SCP:

```bash
# Deploy all files
python deploy_to_device_cloud.py --ssh-key "qdc_id_2025-8-11_62.pem" --username hcktest --port 2222

# Deploy only core files
python deploy_to_device_cloud.py --core-only

# Test SSH connection
python deploy_to_device_cloud.py --test-connection
```

### AWS Virtual Camera Tool

The AWS Virtual Camera tool is used to deploy and test camera-related functionality:

```bash
# List available cameras
python aws_virtual_camera_integration_tool.py list

# Test a specific camera (default is ID 1)
python aws_virtual_camera_integration_tool.py test --id 1 --duration 20

# Deploy camera-related files
python aws_virtual_camera_integration_tool.py deploy --ssh-key "qdc_id_2025-8-11_62.pem" --username hcktest
```

### GitHub Deployment Tool

The GitHub deployment tool is used to publish the project to GitHub and pull it from the device:

```bash
# Initialize GitHub repository
python github_deployment_tool.py init --repo-dir /path/to/repo --repo-url https://github.com/username/repo.git

# Publish project to GitHub
python github_deployment_tool.py deploy --source-dir /path/to/source --repo-dir /path/to/repo

# Pull from GitHub to device
python github_deployment_tool.py pull --ssh-key "key.pem" --target-dir "C:/dragon_x"

# Complete workflow (initialize, publish, pull)
python github_deployment_tool.py workflow --source-dir /path/to/source --repo-dir /path/to/repo --ssh-key "key.pem"
```

## Common Parameters

All scripts support the following common parameters:

- `--ssh-key`: SSH key file path (default: `qdc_id_2025-8-11_62.pem`)
- `--username`: SSH username (default: `hcktest`)
- `--port`: SSH port (default: `2222`)
- `--target-dir`: Target directory on the target device (default: `C:/dragon_x_fall_detection`)
- `--source-dir`: Local source code directory (default: current directory)

## Running on the Windows Device

After deployment, you can run the following commands on the Windows device:

```bash
# Test camera
python C:/dragon_x_fall_detection/aws_virtual_camera_test_windows.py --list

# Run real-time demo
python C:/dragon_x_fall_detection/snapdragon_realtime_demo_windows.py

# Run video demo
python C:/dragon_x_fall_detection/snapdragon_video_demo_windows.py

# Run performance benchmark
python C:/dragon_x_fall_detection/snapdragon_performance_benchmark_windows.py
```

## Troubleshooting

1. **SSH Connection Failure**
   - Ensure SSH key path is correct
   - Ensure username and port are correct
   - Ensure target device is accessible

2. **Camera Cannot Open**
   - On Windows devices, camera ID 1 is typically used instead of 0
   - Use the `--list` option to check available cameras
   - Ensure camera permissions are granted

3. **GitHub Operations Failure**
   - Ensure GitHub repository URL is correct
   - Ensure Git is installed on the Windows device
   - Ensure you have sufficient permissions to push to the repository

## Automatic Update Process

After setting up GitHub deployment, you can use the following process for automatic updates:

1. Develop and test code on Mac
2. Push to GitHub: `python github_deployment_tool.py deploy`
3. Pull updates on Windows device: `cd C:/dragon_x_fall_detection && git pull`

This process minimizes manual deployment work and is especially suitable for frequently updated development environments.

## Contact Support

For deployment issues, please contact:

- Technical Support: `support@example.com`
- Development Team: `dev@example.com`
