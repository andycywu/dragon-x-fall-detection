#!/usr/bin/env python3
"""
AWS Virtual Camera Integration Tool for Snapdragon X Elite
Provides tools to deploy and test AWS Virtual Camera on Windows
"""

import os
import sys
import time
import subprocess
import argparse
import platform
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    logger.warning("OpenCV not available. Limited functionality.")
    OPENCV_AVAILABLE = False

class CameraTestTool:
    """Tool for testing AWS Virtual Camera on Windows"""
    
    @staticmethod
    def list_available_cameras(max_cameras=10):
        """List all available camera devices
        
        Args:
            max_cameras (int): Maximum number of cameras to check
            
        Returns:
            list: List of available camera info
        """
        if not OPENCV_AVAILABLE:
            logger.error("OpenCV not available. Cannot list cameras.")
            return []
            
        available_cameras = []
        
        logger.info(f"Scanning for available cameras (max: {max_cameras})...")
        
        for i in range(max_cameras):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Try to read a frame to confirm camera works
                    ret, frame = cap.read()
                    if ret:
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        available_cameras.append({
                            'id': i,
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'working': True
                        })
                        logger.info(f"Found camera {i}: {width}x{height} @ {fps}fps")
                    else:
                        available_cameras.append({
                            'id': i,
                            'working': False,
                            'note': "Failed to read frame"
                        })
                        logger.warning(f"Camera {i} opened but failed to read frame")
                    
                    cap.release()
            except Exception as e:
                logger.debug(f"Error checking camera {i}: {e}")
        
        if not available_cameras:
            logger.warning("No cameras found")
        else:
            logger.info(f"Found {len(available_cameras)} camera(s)")
            
            # On Windows, suggest using camera ID 1
            if platform.system() == "Windows":
                logger.info("On Windows, camera ID 1 is recommended for AWS Virtual Camera RFC")
        
        return available_cameras
    
    @staticmethod
    def test_camera(camera_id=1, resolution=None, duration=10, save_frame=True):
        """Test a specific camera
        
        Args:
            camera_id (int): Camera ID to test
            resolution (tuple): Optional resolution as (width, height)
            duration (int): Test duration in seconds
            save_frame (bool): Whether to save a test frame
            
        Returns:
            dict: Test results
        """
        if not OPENCV_AVAILABLE:
            logger.error("OpenCV not available. Cannot test camera.")
            return {"success": False, "error": "OpenCV not available"}
            
        logger.info(f"Testing camera ID {camera_id}...")
        
        # Initialize camera
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            logger.error(f"Failed to open camera ID {camera_id}")
            
            # Try alternative camera IDs on Windows
            if platform.system() == "Windows":
                alternative_ids = [0, 2, 3] if camera_id != 1 else [1, 0, 2, 3]
                for alt_id in alternative_ids:
                    if alt_id == camera_id:
                        continue
                    logger.info(f"Trying alternative camera ID: {alt_id}")
                    cap = cv2.VideoCapture(alt_id)
                    if cap.isOpened():
                        logger.info(f"Successfully opened camera with ID {alt_id}")
                        camera_id = alt_id
                        break
                    else:
                        cap.release()
            
            if not cap.isOpened():
                return {
                    "success": False,
                    "camera_id": camera_id,
                    "error": "Failed to open camera"
                }
        
        # Set resolution if specified
        if resolution:
            width, height = resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        logger.info(f"Camera opened with resolution {width}x{height}, {fps} FPS")
        
        # Test reading frames
        start_time = time.time()
        frame_count = 0
        test_frame = None
        
        try:
            while time.time() - start_time < duration:
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning("Failed to read frame")
                    continue
                
                frame_count += 1
                
                # Keep the last frame for saving
                test_frame = frame.copy()
                
                # Add text overlay
                cv2.putText(
                    frame, 
                    f"Camera ID: {camera_id} | {width}x{height} | FPS: {fps:.1f}", 
                    (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, 
                    (0, 255, 0), 
                    2
                )
                
                # Add frame counter
                cv2.putText(
                    frame, 
                    f"Frame: {frame_count} | Time: {time.time() - start_time:.1f}s", 
                    (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, 
                    (0, 255, 0), 
                    2
                )
                
                # Show frame
                cv2.imshow(f"Camera Test - ID {camera_id}", frame)
                
                # Check for exit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            logger.info("Test interrupted by user")
        except Exception as e:
            logger.error(f"Error during camera test: {e}")
        
        # Calculate actual FPS
        end_time = time.time()
        elapsed_time = end_time - start_time
        actual_fps = frame_count / elapsed_time if elapsed_time > 0 else 0
        
        # Save test frame if requested
        frame_path = None
        if save_frame and test_frame is not None:
            frame_path = f"camera_{camera_id}_test.jpg"
            cv2.imwrite(frame_path, test_frame)
            logger.info(f"Test frame saved to {frame_path}")
        
        # Close camera and windows
        cap.release()
        cv2.destroyAllWindows()
        
        # Compile results
        results = {
            "success": True,
            "camera_id": camera_id,
            "resolution": f"{width}x{height}",
            "nominal_fps": fps,
            "actual_fps": actual_fps,
            "frames_captured": frame_count,
            "test_duration": elapsed_time,
            "test_frame": frame_path,
            "platform": platform.system()
        }
        
        logger.info(f"Camera test completed: {actual_fps:.1f} FPS achieved")
        
        return results

class DeploymentTool:
    """Tool for deploying camera-related files to Windows"""
    
    @staticmethod
    def test_ssh_connection(ssh_key, username, port):
        """Test SSH connection to the Windows device"""
        logger.info("Testing SSH connection...")
        
        command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no -o ConnectTimeout=5 {username}@localhost "echo Connection successful"'
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("SSH connection successful!")
                return True
            else:
                logger.error(f"SSH connection failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error testing SSH connection: {e}")
            return False
    
    @staticmethod
    def deploy_file(ssh_key, username, port, local_file, remote_file):
        """Deploy a file to the Windows device"""
        logger.info(f"Deploying {local_file} -> {remote_file}")
        
        if not os.path.exists(local_file):
            logger.error(f"Local file not found: {local_file}")
            return False
        
        # Create remote directory if needed
        remote_dir = os.path.dirname(remote_file)
        if remote_dir:
            dir_command = f'ssh -i "{ssh_key}" -p {port} -o StrictHostKeyChecking=no {username}@localhost "mkdir -p {remote_dir}"'
            try:
                subprocess.run(dir_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as e:
                logger.warning(f"Error creating remote directory: {e}")
        
        # Copy file
        command = f'scp -i "{ssh_key}" -P {port} -o StrictHostKeyChecking=no "{local_file}" {username}@localhost:"{remote_file}"'
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"File deployed successfully: {os.path.basename(local_file)}")
                return True
            else:
                logger.error(f"Deployment failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error deploying file: {e}")
            return False
    
    @staticmethod
    def get_camera_files():
        """Get list of camera-related files to deploy"""
        return [
            "aws_virtual_camera_rfc.py",
            "aws_virtual_camera_test_windows.py",
            "snapdragon_realtime_demo_windows.py",
            "snapdragon_video_demo_windows.py"
        ]
    
    @staticmethod
    def deploy_camera_files(ssh_key, username, port, source_dir, target_dir):
        """Deploy all camera-related files"""
        files = DeploymentTool.get_camera_files()
        logger.info(f"Deploying {len(files)} camera-related files...")
        
        success_count = 0
        
        for file in files:
            local_file = os.path.join(source_dir, file)
            remote_file = f"{target_dir}/{file}"
            
            if DeploymentTool.deploy_file(ssh_key, username, port, local_file, remote_file):
                success_count += 1
        
        logger.info(f"Deployed {success_count}/{len(files)} files")
        return success_count == len(files)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="AWS Virtual Camera Integration Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List cameras command
    list_parser = subparsers.add_parser("list", help="List available cameras")
    list_parser.add_argument("--max", type=int, default=10, help="Maximum number of cameras to check")
    
    # Test camera command
    test_parser = subparsers.add_parser("test", help="Test a camera")
    test_parser.add_argument("--id", type=int, default=1, help="Camera ID to test (default: 1)")
    test_parser.add_argument("--duration", type=int, default=10, help="Test duration in seconds (default: 10)")
    test_parser.add_argument("--resolution", type=str, help="Resolution as WIDTHxHEIGHT (e.g., 640x480)")
    test_parser.add_argument("--save", action="store_true", help="Save a test frame")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy camera files to Windows")
    deploy_parser.add_argument("--ssh-key", required=True, help="SSH key file")
    deploy_parser.add_argument("--username", default="hcktest", help="SSH username (default: hcktest)")
    deploy_parser.add_argument("--port", type=int, default=2222, help="SSH port (default: 2222)")
    deploy_parser.add_argument("--source", default=os.getcwd(), help="Source directory (default: current directory)")
    deploy_parser.add_argument("--target", default="C:/dragon_x_fall_detection", help="Target directory on Windows")
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == "list":
        cameras = CameraTestTool.list_available_cameras(args.max)
        
        print("\nAvailable cameras:")
        if cameras:
            for camera in cameras:
                if camera.get('working', False):
                    print(f"  Camera {camera['id']}: {camera['width']}x{camera['height']} @ {camera['fps']}fps")
                else:
                    print(f"  Camera {camera['id']}: Not working - {camera.get('note', 'Unknown error')}")
        else:
            print("  No cameras found")
    
    elif args.command == "test":
        # Parse resolution if provided
        resolution = None
        if args.resolution:
            try:
                width, height = map(int, args.resolution.split("x"))
                resolution = (width, height)
            except ValueError:
                print(f"Invalid resolution format: {args.resolution}. Using default.")
        
        # Run camera test
        results = CameraTestTool.test_camera(
            camera_id=args.id,
            resolution=resolution,
            duration=args.duration,
            save_frame=args.save
        )
        
        if results["success"]:
            print("\nCamera Test Results:")
            print(f"  Camera ID: {results['camera_id']}")
            print(f"  Resolution: {results['resolution']}")
            print(f"  Nominal FPS: {results['nominal_fps']}")
            print(f"  Actual FPS: {results['actual_fps']:.1f}")
            print(f"  Frames captured: {results['frames_captured']}")
            print(f"  Test duration: {results['test_duration']:.1f} seconds")
            print(f"  Platform: {results['platform']}")
            
            if results.get("test_frame"):
                print(f"  Test frame saved to: {results['test_frame']}")
        else:
            print(f"\nCamera test failed: {results.get('error', 'Unknown error')}")
    
    elif args.command == "deploy":
        # Test SSH connection
        if not DeploymentTool.test_ssh_connection(args.ssh_key, args.username, args.port):
            print("Cannot proceed: SSH connection failed")
            return 1
        
        # Deploy camera files
        success = DeploymentTool.deploy_camera_files(
            args.ssh_key,
            args.username,
            args.port,
            args.source,
            args.target
        )
        
        if success:
            print("\nDeployment successful!")
            print("\nTo test the camera on Windows, run:")
            print(f"  python {args.target}/aws_virtual_camera_test_windows.py --list")
            print(f"  python {args.target}/aws_virtual_camera_test_windows.py --camera_id 1")
        else:
            print("\nDeployment failed. Check logs for details.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
