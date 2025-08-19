#!/usr/bin/env python3
"""
Video Processing Demo with Snapdragon X Elite Acceleration
Demonstrates real-time fall detection on video using hardware acceleration
"""

import os
import sys
import cv2
import time
import numpy as np
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoFallDetector:
    """Video fall detector with Snapdragon X Elite acceleration"""
    
    def __init__(self, enable_acceleration=True):
        """Initialize the video fall detector"""
        logger.info("Initializing Video Fall Detector")
        
        # Configure hardware acceleration
        self.enable_acceleration = enable_acceleration
        if enable_acceleration:
            self._setup_acceleration()
            logger.info("Hardware acceleration enabled")
        else:
            logger.info("Hardware acceleration disabled")
        
        # Load fall detector module
        try:
            from fall_detector import FallDetector
            self.fall_detector = FallDetector()
            logger.info("Fall detector initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing fall detector: {e}")
            raise
        
        # Load unified AI detector to check platform and accelerators
        try:
            from unified_ai_detector_ascii import UnifiedAIDetector
            self.ai_detector = UnifiedAIDetector()
            self.platform = self.ai_detector.platform
            self.accelerators = self.ai_detector.accelerators
            logger.info(f"Platform: {self.platform}")
            logger.info(f"Available accelerators: {self.accelerators}")
        except Exception as e:
            logger.warning(f"Could not load AI detector: {e}")
            self.platform = "unknown"
            self.accelerators = []
    
    def _setup_acceleration(self):
        """Set up hardware acceleration"""
        os.environ['ENABLE_QAI_ACCELERATION'] = 'true'
        os.environ['QAI_HUB_ACCELERATOR'] = 'hexagon_npu'
        os.environ['QAI_OPTIMIZATION_LEVEL'] = 'performance'
    
    def process_frame(self, frame):
        """Process a single video frame"""
        start_time = time.time()
        
        # Detect fall
        result = self.fall_detector.detect_fall_from_frame(frame)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Process result
        if result is None:
            return {
                'is_falling': False,
                'confidence': None,
                'process_time': process_time,
                'status': 'NO_POSE_DETECTED',
                'output_frame': self.visualize_result(frame, None, process_time)
            }
        
        is_falling, confidence = result
        
        # Create visualization
        output_frame = self.visualize_result(frame, result, process_time)
        
        return {
            'is_falling': is_falling,
            'confidence': confidence,
            'process_time': process_time,
            'status': 'FALL_DETECTED' if is_falling else 'NO_FALL',
            'output_frame': output_frame
        }
    
    def visualize_result(self, frame, result, process_time):
        """Visualize the detection result on the frame"""
        # Make a copy for visualization
        display_frame = frame.copy()
        
        # Get result values
        if result is None:
            is_falling = False
            confidence = None
            status = 'NO_POSE_DETECTED'
        else:
            is_falling, confidence = result
            status = 'FALL_DETECTED' if is_falling else 'NO_FALL'
        
        # Determine color based on status
        if status == 'FALL_DETECTED':
            color = (0, 0, 255)  # Red
            text = "FALL DETECTED!"
        elif status == 'NO_FALL':
            color = (0, 255, 0)  # Green
            text = "No fall detected"
        else:  # NO_POSE_DETECTED
            color = (0, 165, 255)  # Orange
            text = "No pose detected"
        
        # Add text with detection results
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(display_frame, text, (30, 40), font, 1, color, 2)
        
        if confidence is not None:
            cv2.putText(display_frame, f"Confidence: {confidence:.2f}", (30, 80), font, 1, color, 2)
        
        # Add processing time and FPS
        fps = 1.0 / process_time if process_time > 0 else 0
        cv2.putText(display_frame, f"FPS: {fps:.1f}", (30, 120), font, 1, (255, 255, 0), 2)
        
        # Add platform info
        cv2.putText(display_frame, f"Platform: {self.platform}", (30, 160), font, 1, (255, 255, 255), 2)
        
        # Add acceleration info
        acc_text = "NPU Acceleration: "
        if self.enable_acceleration and 'hexagon_npu' in self.accelerators:
            acc_text += "Enabled"
            acc_color = (0, 255, 0)
        else:
            acc_text += "Disabled"
            acc_color = (0, 0, 255)
        cv2.putText(display_frame, acc_text, (30, 200), font, 1, acc_color, 2)
        
        return display_frame

def process_video(video_path, output_path=None, enable_acceleration=True):
    """Process a video file with fall detection"""
    print(f"Processing video: {video_path}")
    print(f"Hardware acceleration: {'Enabled' if enable_acceleration else 'Disabled'}")
    
    # Initialize video fall detector
    detector = VideoFallDetector(enable_acceleration=enable_acceleration)
    
    # Open video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video properties: {width}x{height}, {fps} FPS, {frame_count} frames")
    
    # Initialize video writer if output path is specified
    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        print(f"Writing output to: {output_path}")
    
    # Process video frames
    frame_idx = 0
    processing_times = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_idx += 1
        print(f"Processing frame {frame_idx}/{frame_count}...")
        
        # Process frame
        result = detector.process_frame(frame)
        processing_times.append(result['process_time'])
        
        # Display status
        status = result['status']
        conf = result['confidence']
        if conf is not None:
            print(f"  Result: {status}, Confidence: {conf:.2f}, Time: {result['process_time']:.3f}s")
        else:
            print(f"  Result: {status}, Time: {result['process_time']:.3f}s")
        
        # Write output frame
        if writer:
            writer.write(result['output_frame'])
    
    # Release resources
    cap.release()
    if writer:
        writer.release()
    
    # Print summary
    if processing_times:
        avg_time = sum(processing_times) / len(processing_times)
        avg_fps = 1.0 / avg_time
        print("\nVideo Processing Summary:")
        print(f"Processed {frame_idx} frames")
        print(f"Average processing time: {avg_time:.3f} seconds per frame")
        print(f"Average FPS: {avg_fps:.1f}")
        print(f"Hardware acceleration: {'Enabled' if enable_acceleration else 'Disabled'}")
        if output_path:
            print(f"Output saved to: {output_path}")
    
    return {
        'frames_processed': frame_idx,
        'avg_time': avg_time if processing_times else 0,
        'avg_fps': avg_fps if processing_times else 0
    }

def process_webcam(output_path=None, enable_acceleration=True, camera_id=0, resolution=None):
    """Process webcam feed with fall detection"""
    print("Opening AWS Virtual Camera RFC...")
    print(f"Hardware acceleration: {'Enabled' if enable_acceleration else 'Disabled'}")
    
    # Initialize video fall detector
    detector = VideoFallDetector(enable_acceleration=enable_acceleration)
    
    # Import AWS Virtual Camera RFC
    try:
        from aws_virtual_camera_rfc import AWSVirtualCameraRFC
        # Open AWS Virtual Camera RFC
        camera = AWSVirtualCameraRFC(camera_id=camera_id, resolution=resolution)
        if not camera.open():
            print(f"Error: Could not open AWS Virtual Camera RFC with ID {camera_id}")
            return
        
        # Get camera properties
        props = camera.get_properties()
        width = props['width']
        height = props['height']
        fps = props['nominal_fps'] if props['nominal_fps'] > 0 else 30  # Default to 30 FPS if not specified
        
        print(f"AWS Virtual Camera RFC properties: {width}x{height}, {fps} FPS")
    except ImportError:
        print("AWS Virtual Camera RFC module not found, falling back to standard webcam")
        # Fallback to standard webcam
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"Error: Could not open webcam with ID {camera_id}")
            return
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = 30  # Assume 30 FPS for webcam
        
        print(f"Webcam properties: {width}x{height}")
    
    # Initialize video writer if output path is specified
    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        print(f"Writing output to: {output_path}")
    
    # Process webcam frames
    frame_idx = 0
    processing_times = []
    
    print("Press 'q' to quit")
    
    using_aws_rfc = 'camera' in locals()
    
    while True:
        # Read frame from appropriate source
        if using_aws_rfc:
            ret, frame = camera.read_frame()
        else:
            ret, frame = cap.read()
            
        if not ret:
            break
        
        frame_idx += 1
        
        # Process frame
        result = detector.process_frame(frame)
        processing_times.append(result['process_time'])
        
        # Display status in console
        if frame_idx % 10 == 0:  # Only print every 10 frames
            status = result['status']
            conf = result['confidence']
            if conf is not None:
                print(f"Frame {frame_idx}: {status}, Confidence: {conf:.2f}, FPS: {1.0/result['process_time']:.1f}")
            else:
                print(f"Frame {frame_idx}: {status}, FPS: {1.0/result['process_time']:.1f}")
        
        # Display frame
        cv2.imshow('Fall Detection', result['output_frame'])
        
        # Write output frame
        if writer:
            writer.write(result['output_frame'])
        
        # Check for key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources
    if using_aws_rfc:
        camera.close()
    else:
        cap.release()
        
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    
    # Print summary
    if processing_times:
        avg_time = sum(processing_times) / len(processing_times)
        avg_fps = 1.0 / avg_time
        print("\nWebcam Processing Summary:")
        print(f"Processed {frame_idx} frames")
        print(f"Average processing time: {avg_time:.3f} seconds per frame")
        print(f"Average FPS: {avg_fps:.1f}")
        print(f"Hardware acceleration: {'Enabled' if enable_acceleration else 'Disabled'}")
        if output_path:
            print(f"Output saved to: {output_path}")
    
    return {
        'frames_processed': frame_idx,
        'avg_time': avg_time if processing_times else 0,
        'avg_fps': avg_fps if processing_times else 0
    }

def main():
    parser = argparse.ArgumentParser(description="Video Fall Detection with Snapdragon X Elite Acceleration")
    parser.add_argument("--input", help="Path to input video file (omit for webcam)")
    parser.add_argument("--output", help="Path to output video file")
    parser.add_argument("--disable-acceleration", action="store_true", help="Disable hardware acceleration")
    parser.add_argument("--camera", type=int, default=1, help="Camera ID for AWS Virtual Camera RFC (default: 1)")
    parser.add_argument("--resolution", help="Camera resolution in format WIDTHxHEIGHT (e.g., 640x480)")
    
    args = parser.parse_args()
    
    # Enable acceleration by default
    enable_acceleration = not args.disable_acceleration
    
    # Parse resolution if provided
    resolution = None
    if args.resolution:
        try:
            width, height = map(int, args.resolution.split('x'))
            resolution = (width, height)
            print(f"Using custom resolution: {width}x{height}")
        except:
            print(f"Invalid resolution format: {args.resolution}")
            print("Using default camera resolution")
    
    if args.input:
        # Process video file
        process_video(args.input, args.output, enable_acceleration)
    else:
        # Process webcam feed
        process_webcam(args.output, enable_acceleration, args.camera, resolution)

if __name__ == "__main__":
    main()
