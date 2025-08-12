#!/usr/bin/env python3
"""
AWS Virtual Camera RFC Test for Windows (ASCII Version)
Tests AWS Virtual Camera on Snapdragon X Elite Windows platform
"""

import cv2
import numpy as np
import time
import logging
import os
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_available_cameras(max_cameras=5):
    """List all available camera devices
    
    Args:
        max_cameras (int): Maximum number of cameras to check
        
    Returns:
        list: List of available camera info
    """
    available_cameras = []
    
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            available_cameras.append({
                'id': i,
                'width': width,
                'height': height,
                'fps': fps
            })
            
            cap.release()
    
    return available_cameras

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
    logger.info(f"Testing camera ID {camera_id}...")
    
    # Initialize camera
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        logger.error(f"Failed to open camera ID {camera_id}")
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
        "test_frame": frame_path
    }
    
    logger.info(f"Camera test completed: {actual_fps:.1f} FPS achieved")
    
    return results

def main():
    """Main function: Camera test application"""
    parser = argparse.ArgumentParser(description="Test AWS Virtual Camera RFC on Windows")
    parser.add_argument("--camera_id", type=int, default=1, help="Camera ID to test (default: 1)")
    parser.add_argument("--duration", type=int, default=10, help="Test duration in seconds (default: 10)")
    parser.add_argument("--list", action="store_true", help="List available cameras")
    parser.add_argument("--save", action="store_true", help="Save a test frame")
    parser.add_argument("--width", type=int, help="Set camera width")
    parser.add_argument("--height", type=int, help="Set camera height")
    args = parser.parse_args()
    
    print("AWS Virtual Camera RFC Test for Windows")
    print("=" * 50)
    
    if args.list:
        print("\nScanning for available cameras...")
        cameras = list_available_cameras()
        
        if cameras:
            print(f"\nFound {len(cameras)} camera(s):")
            for cam in cameras:
                print(f"  Camera ID {cam['id']}: {cam['width']}x{cam['height']}, {cam['fps']} FPS")
        else:
            print("No cameras found!")
    else:
        # Set resolution if specified
        resolution = None
        if args.width and args.height:
            resolution = (args.width, args.height)
        
        # Test the specified camera
        results = test_camera(
            camera_id=args.camera_id,
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
            
            if results.get("test_frame"):
                print(f"  Test frame saved to: {results['test_frame']}")
        else:
            print(f"\nCamera test failed: {results.get('error', 'Unknown error')}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()
