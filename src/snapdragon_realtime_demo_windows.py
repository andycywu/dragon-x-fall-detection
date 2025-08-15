#!/usr/bin/env python3
"""
Snapdragon X Elite Real-time Fall Detection Demo (Windows Version)
Demonstrates real-time fall detection using webcam with hardware acceleration
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

class RealtimeFallDetector:
    """Real-time fall detector with Snapdragon X Elite acceleration"""
    
    def __init__(self, camera_index=1, enable_acceleration=True, resolution=None):
        """Initialize the real-time fall detector"""
        logger.info("Initializing Real-time Fall Detector")
        
        # Configure hardware acceleration
        self.enable_acceleration = enable_acceleration
        if enable_acceleration:
            self._setup_acceleration()
            logger.info("Hardware acceleration enabled")
        else:
            logger.info("Hardware acceleration disabled")
        
        # Camera settings
        self.camera_index = camera_index
        self.resolution = resolution
        
        # Performance tracking
        self.fps_history = []
        self.max_history = 30  # Keep last 30 frames for FPS calculation
        
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
            # Try to use the Windows-compatible version first
            try:
                from unified_ai_detector_windows import UnifiedAIDetector
            except ImportError:
                from unified_ai_detector_ascii import UnifiedAIDetector
                
            self.ai_detector = UnifiedAIDetector()
            self.platform = getattr(self.ai_detector, 'platform_info', {}).get('type', 'unknown')
            self.accelerators = [getattr(self.ai_detector, 'platform_info', {}).get('ai_accelerator', 'cpu')]
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
    
    def open_camera(self):
        """Open and configure the camera"""
        logger.info(f"Opening camera {self.camera_index}")
        
        try:
            # Try to use AWS Virtual Camera RFC
            try:
                from aws_virtual_camera_rfc import AWSVirtualCameraRFC
            except ImportError:
                logger.info("Trying alternate import path for AWS Virtual Camera RFC")
                # Try with full path for Windows
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                from aws_virtual_camera_rfc import AWSVirtualCameraRFC
                
            self.use_aws_rfc = True
            
            # Create AWS Virtual Camera RFC
            self.camera = AWSVirtualCameraRFC(camera_id=self.camera_index, resolution=self.resolution)
            if not self.camera.open():
                logger.error(f"Failed to open AWS Virtual Camera RFC with ID {self.camera_index}")
                return False
            
            # Get properties
            props = self.camera.get_properties()
            self.width = props['width']
            self.height = props['height']
            self.camera_fps = props['nominal_fps']
            
            logger.info(f"AWS Virtual Camera RFC opened with resolution {self.width}x{self.height}, {self.camera_fps} FPS")
            
        except Exception as e:
            # Fallback to standard OpenCV
            logger.info(f"AWS Virtual Camera RFC not available ({e}), falling back to standard OpenCV")
            self.use_aws_rfc = False
            
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_index}")
                return False
            
            # Set resolution if specified
            if self.resolution:
                width, height = self.resolution
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Get actual camera properties
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.camera_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Camera opened with resolution {self.width}x{self.height}, {self.camera_fps} FPS")
        
        return True
    
    def close_camera(self):
        """Close the camera"""
        if hasattr(self, 'use_aws_rfc') and self.use_aws_rfc:
            if hasattr(self, 'camera') and self.camera is not None:
                self.camera.close()
                logger.info("AWS Virtual Camera RFC closed")
        elif hasattr(self, 'cap') and self.cap is not None and self.cap.isOpened():
            self.cap.release()
            logger.info("Camera closed")
    
    def process_frame(self, frame):
        """Process a single video frame"""
        start_time = time.time()
        
        # Detect fall
        result = self.fall_detector.detect_fall_from_frame(frame)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Track FPS
        self.fps_history.append(1.0 / process_time if process_time > 0 else 0)
        if len(self.fps_history) > self.max_history:
            self.fps_history = self.fps_history[-self.max_history:]
        
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
        
        # Calculate average FPS
        if self.fps_history:
            avg_fps = sum(self.fps_history) / len(self.fps_history)
            cv2.putText(display_frame, f"FPS: {avg_fps:.1f}", (30, 120), font, 1, (255, 255, 0), 2)
        
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
        
        # Add time
        current_time = time.strftime("%H:%M:%S", time.localtime())
        cv2.putText(display_frame, current_time, (display_frame.shape[1] - 150, 40), font, 1, (255, 255, 255), 2)
        
        return display_frame
    
    def run(self, output_path=None, max_duration=None):
        """Run the real-time fall detection demo"""
        if not self.open_camera():
            return False
        
        # Initialize video writer if output path is specified
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, 30, (self.width, self.height))
            logger.info(f"Recording video to: {output_path}")
        
        # Variables for statistics
        frame_count = 0
        start_time = time.time()
        last_status_time = start_time
        last_status = None
        
        logger.info("Starting real-time fall detection")
        print("Real-time Fall Detection Demo")
        print("=" * 50)
        print("Press 'q' to quit")
        print("Press 's' to take a screenshot")
        print("Press 'r' to toggle recording")
        
        # Main loop
        recording = output_path is not None
        try:
            while True:
                # Check if max duration reached
                if max_duration and (time.time() - start_time) > max_duration:
                    print(f"Maximum duration of {max_duration} seconds reached")
                    break
                
                # Read frame
                if hasattr(self, 'use_aws_rfc') and self.use_aws_rfc:
                    ret, frame = self.camera.read_frame()
                else:
                    ret, frame = self.cap.read()
                    
                if not ret or frame is None:
                    print("Failed to read frame from camera")
                    # Try to recover by waiting a bit
                    time.sleep(0.1)
                    continue
                
                # Process frame
                result = self.process_frame(frame)
                frame_count += 1
                
                # Log status changes
                current_status = result['status']
                if current_status != last_status:
                    print(f"Status changed to: {current_status}")
                    if current_status == 'FALL_DETECTED':
                        print("ALERT: Fall detected!")
                    last_status = current_status
                    last_status_time = time.time()
                
                # Log confidence periodically
                if frame_count % 30 == 0 and result['confidence'] is not None:
                    print(f"Current confidence: {result['confidence']:.2f}")
                
                # Display frame
                cv2.imshow('Fall Detection', result['output_frame'])
                
                # Write frame if recording
                if writer and recording:
                    writer.write(result['output_frame'])
                
                # Check for key press
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Quit key pressed")
                    break
                elif key == ord('s'):
                    # Take screenshot
                    screenshot_path = f"screenshot_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
                    cv2.imwrite(screenshot_path, result['output_frame'])
                    print(f"Screenshot saved to {screenshot_path}")
                elif key == ord('r'):
                    # Toggle recording
                    if writer:
                        recording = not recording
                        print(f"Recording {'started' if recording else 'paused'}")
        
        except KeyboardInterrupt:
            print("Interrupted by user")
        
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.close_camera()
            if writer:
                writer.release()
            cv2.destroyAllWindows()
            
            # Print statistics
            total_time = time.time() - start_time
            print("\nSession Statistics:")
            print(f"Total frames processed: {frame_count}")
            print(f"Total runtime: {total_time:.2f} seconds")
            if frame_count > 0:
                print(f"Average FPS: {frame_count / total_time:.2f}")
            if writer:
                print(f"Output video saved to: {output_path}")
            
            return True

def main():
    parser = argparse.ArgumentParser(description="Real-time Fall Detection with Snapdragon X Elite Acceleration")
    parser.add_argument("--camera", type=int, default=1, help="Camera index (default: 1)")
    parser.add_argument("--output", help="Path to output video file (optional)")
    parser.add_argument("--duration", type=int, help="Maximum duration in seconds (optional)")
    parser.add_argument("--disable-acceleration", action="store_true", help="Disable hardware acceleration")
    parser.add_argument("--resolution", help="Camera resolution in format WIDTHxHEIGHT (e.g., 640x480)")
    
    args = parser.parse_args()
    
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
    
    # Create and run detector
    detector = RealtimeFallDetector(
        camera_index=args.camera,
        enable_acceleration=not args.disable_acceleration,
        resolution=resolution
    )
    
    detector.run(output_path=args.output, max_duration=args.duration)

if __name__ == "__main__":
    main()
