#!/usr/bin/env python3
"""
AWS Virtual Camera RFC Test Script
Tests the AWS Virtual Camera RFC implementation
"""

import sys
import os
import time
import cv2
from aws_virtual_camera_rfc import AWSVirtualCameraRFC, list_available_cameras

def test_list_cameras():
    """Test listing available cameras"""
    print("\nListing available AWS Virtual Camera RFC devices...")
    cameras = list_available_cameras()
    
    if not cameras:
        print("No AWS Virtual Camera RFC devices found")
        return
    
    print(f"Found {len(cameras)} AWS Virtual Camera RFC devices:")
    for cam in cameras:
        print(f"Camera ID {cam['id']}: {cam['width']}x{cam['height']}, {cam['fps']} FPS")
    
    return cameras

def test_camera(camera_id=0, duration=5, save_frame=True):
    """Test camera functionality"""
    print(f"\nTesting AWS Virtual Camera RFC with ID {camera_id}...")
    
    # Initialize camera
    camera = AWSVirtualCameraRFC(camera_id=camera_id)
    if not camera.open():
        print(f"Failed to open AWS Virtual Camera RFC with ID {camera_id}")
        return False
    
    # Get properties
    props = camera.get_properties()
    print(f"Camera properties:")
    for key, value in props.items():
        print(f"  {key}: {value}")
    
    # Read frames for specified duration
    start_time = time.time()
    frame_count = 0
    
    print(f"Reading frames for {duration} seconds...")
    
    while (time.time() - start_time) < duration:
        ret, frame = camera.read_frame()
        
        if not ret:
            print("Failed to read frame")
            break
        
        frame_count += 1
        
        # Save first frame if requested
        if save_frame and frame_count == 1:
            filename = f"aws_camera_{camera_id}_test.jpg"
            cv2.imwrite(filename, frame)
            print(f"Saved test frame to {filename}")
    
    # Close camera
    camera.close()
    
    # Calculate statistics
    elapsed_time = time.time() - start_time
    fps = frame_count / elapsed_time if elapsed_time > 0 else 0
    
    print(f"Test results:")
    print(f"  Frames captured: {frame_count}")
    print(f"  Elapsed time: {elapsed_time:.2f} seconds")
    print(f"  Average FPS: {fps:.2f}")
    
    return True

def run_camera_demo(camera_id=0, duration=10):
    """Run a visual demo of the camera"""
    print(f"\nRunning AWS Virtual Camera RFC demo with ID {camera_id}...")
    
    # Initialize camera
    camera = AWSVirtualCameraRFC(camera_id=camera_id)
    if not camera.open():
        print(f"Failed to open AWS Virtual Camera RFC with ID {camera_id}")
        return False
    
    # Get properties
    props = camera.get_properties()
    width = props['width']
    height = props['height']
    
    print(f"Camera properties: {width}x{height}")
    
    # Start capture
    start_time = time.time()
    frame_count = 0
    
    print(f"Running demo for {duration} seconds...")
    print("Press any key to exit early")
    
    while (time.time() - start_time) < duration:
        ret, frame = camera.read_frame()
        
        if not ret:
            print("Failed to read frame")
            break
        
        frame_count += 1
        
        # Add overlay information
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        
        cv2.putText(frame, f"AWS Virtual Camera RFC ID: {camera_id}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {frame_count}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Time: {elapsed:.1f}s", (10, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display frame
        cv2.imshow("AWS Virtual Camera RFC Demo", frame)
        
        # Check for key press to exit
        if cv2.waitKey(1) & 0xFF != 255:
            print("Key pressed, exiting...")
            break
    
    # Clean up
    camera.close()
    cv2.destroyAllWindows()
    
    # Calculate final statistics
    elapsed_time = time.time() - start_time
    fps = frame_count / elapsed_time if elapsed_time > 0 else 0
    
    print(f"Demo results:")
    print(f"  Frames displayed: {frame_count}")
    print(f"  Elapsed time: {elapsed_time:.2f} seconds")
    print(f"  Average FPS: {fps:.2f}")
    
    return True

def main():
    """Main function"""
    print("AWS Virtual Camera RFC Test")
    print("=" * 50)
    
    # List available cameras
    cameras = test_list_cameras()
    
    if not cameras:
        print("No cameras found, exiting")
        return
    
    # Default to camera ID 1
    camera_id = 1
    if len(cameras) > 1:
        while True:
            try:
                selection = input(f"Select camera ID to test (default=1): ")
                if not selection:
                    break
                
                camera_id = int(selection)
                if 0 <= camera_id < len(cameras):
                    break
                else:
                    print(f"Invalid selection, please enter a number between 0 and {len(cameras)-1}")
            except ValueError:
                print("Please enter a valid number")
    
    # Test selected camera
    test_camera(camera_id)
    
    # Ask if user wants to run demo
    while True:
        response = input("Run visual demo? (y/n, default=y): ").lower()
        if not response or response == 'y':
            run_camera_demo(camera_id)
            break
        elif response == 'n':
            break
        else:
            print("Please enter 'y' or 'n'")
    
    print("\nAWS Virtual Camera RFC test completed")

if __name__ == "__main__":
    main()
