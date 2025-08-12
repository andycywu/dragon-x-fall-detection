#!/usr/bin/env python3
"""
Snapdragon X Elite Video Fall Detection Demo (Windows Version)
Demonstrates fall detection on video file or webcam with hardware acceleration
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
    
    def __init__(self, video_source=None, camera_index=1, enable_acceleration=True, resolution=None):
        """Initialize the video fall detector
        
        Args:
            video_source (str): Path to video file, or None to use camera
            camera_index (int): Camera index to use when video_source is None
            enable_acceleration (bool): Whether to enable hardware acceleration
            resolution (tuple): Optional resolution as (width, height)
        """
        logger.info("Initializing Video Fall Detector")
        
        # Video source settings
        self.video_source = video_source
        self.camera_index = camera_index
        self.resolution = resolution
        
        # Configure hardware acceleration
        self.enable_acceleration = enable_acceleration
        if enable_acceleration:
            self._setup_acceleration()
            logger.info("Hardware acceleration enabled")
        else:
            logger.info("Hardware acceleration disabled")
        
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
    
    def open_video_source(self):
        """Open and configure the video source (file or camera)"""
        if self.video_source:
            # Open video file
            logger.info(f"Opening video file: {self.video_source}")
            self.cap = cv2.VideoCapture(self.video_source)
            self.using_camera = False
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open video file: {self.video_source}")
                return False
                
            # Get video properties
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            logger.info(f"Video properties: {self.width}x{self.height}, {self.fps} FPS, {self.total_frames} frames")
            
            return True
        else:
            # Open camera
            logger.info(f"Opening camera {self.camera_index}")
            self.using_camera = True
            
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
                self.fps = props['nominal_fps']
                
                logger.info(f"AWS Virtual Camera RFC opened with resolution {self.width}x{self.height}, {self.fps} FPS")
                
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
                self.fps = self.cap.get(cv2.CAP_PROP_FPS)
                
                logger.info(f"Camera opened with resolution {self.width}x{self.height}, {self.fps} FPS")
            
            return True
    
    def close_video_source(self):
        """Close the video source"""
        if self.using_camera:
            if hasattr(self, 'use_aws_rfc') and self.use_aws_rfc:
                if hasattr(self, 'camera') and self.camera is not None:
                    self.camera.close()
                    logger.info("AWS Virtual Camera RFC closed")
            elif hasattr(self, 'cap') and self.cap is not None and self.cap.isOpened():
                self.cap.release()
                logger.info("Camera closed")
        else:
            if hasattr(self, 'cap') and self.cap is not None and self.cap.isOpened():
                self.cap.release()
                logger.info("Video file closed")
    
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
        
        # Add time info
        current_time = time.strftime("%H:%M:%S", time.localtime())
        cv2.putText(display_frame, current_time, (display_frame.shape[1] - 150, 40), font, 1, (255, 255, 255), 2)
        
        # Add frame info if using video file
        if not self.using_camera and hasattr(self, 'total_frames'):
            curr_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            progress = curr_frame / self.total_frames if self.total_frames > 0 else 0
            cv2.putText(display_frame, f"Frame: {curr_frame}/{self.total_frames} ({progress:.1%})",
                      (30, 240), font, 1, (255, 255, 255), 2)
        
        return display_frame
    
    def run(self, output_path=None, max_duration=None, playback_speed=1.0):
        """Run the video fall detection demo
        
        Args:
            output_path (str): Path to output video file, or None to not record
            max_duration (float): Maximum duration in seconds, or None for no limit
            playback_speed (float): Playback speed multiplier (1.0 = normal speed)
        """
        if not self.open_video_source():
            return False
        
        # Initialize video writer if output path is specified
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))
            logger.info(f"Recording video to: {output_path}")
        
        # Variables for statistics
        frame_count = 0
        fall_count = 0
        start_time = time.time()
        last_status = None
        last_frame_time = time.time()
        
        logger.info("Starting video fall detection")
        print("Video Fall Detection Demo")
        print("=" * 50)
        print("Press 'q' to quit")
        print("Press 's' to take a screenshot")
        print("Press 'p' to pause/play")
        print("Press '+' to increase playback speed")
        print("Press '-' to decrease playback speed")
        
        # Main loop
        paused = False
        try:
            while True:
                # Check if max duration reached
                if max_duration and (time.time() - start_time) > max_duration:
                    print(f"Maximum duration of {max_duration} seconds reached")
                    break
                
                # If paused, just check for key press
                if paused:
                    key = cv2.waitKey(100) & 0xFF
                    if key == ord('p'):
                        paused = False
                        print("Playback resumed")
                    elif key == ord('q'):
                        print("Quit key pressed")
                        break
                    continue
                
                # Control frame rate for video files
                if not self.using_camera:
                    target_time = last_frame_time + (1.0 / (self.fps * playback_speed))
                    wait_time = max(0, target_time - time.time())
                    time.sleep(wait_time)
                
                # Read frame
                if self.using_camera:
                    if hasattr(self, 'use_aws_rfc') and self.use_aws_rfc:
                        ret, frame = self.camera.read_frame()
                    else:
                        ret, frame = self.cap.read()
                else:
                    ret, frame = self.cap.read()
                    
                if not ret or frame is None:
                    if self.using_camera:
                        print("Failed to read frame from camera")
                        time.sleep(0.1)  # Wait a bit and try again
                        continue
                    else:
                        print("End of video reached")
                        break
                
                last_frame_time = time.time()
                
                # Process frame
                result = self.process_frame(frame)
                frame_count += 1
                
                # Log status changes
                current_status = result['status']
                if current_status != last_status:
                    print(f"Status changed to: {current_status}")
                    if current_status == 'FALL_DETECTED':
                        fall_count += 1
                        print(f"ALERT: Fall detected! (#{fall_count})")
                    last_status = current_status
                
                # Display frame
                cv2.imshow('Fall Detection', result['output_frame'])
                
                # Write frame if recording
                if writer:
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
                elif key == ord('p'):
                    # Pause/play
                    paused = True
                    print("Playback paused (press 'p' to resume)")
                elif key == ord('+'):
                    # Increase speed
                    playback_speed = min(playback_speed * 1.5, 10.0)
                    print(f"Playback speed: {playback_speed:.1f}x")
                elif key == ord('-'):
                    # Decrease speed
                    playback_speed = max(playback_speed / 1.5, 0.1)
                    print(f"Playback speed: {playback_speed:.1f}x")
        
        except KeyboardInterrupt:
            print("Interrupted by user")
        
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.close_video_source()
            if writer:
                writer.release()
            cv2.destroyAllWindows()
            
            # Print statistics
            total_time = time.time() - start_time
            print("\nSession Statistics:")
            print(f"Total frames processed: {frame_count}")
            print(f"Total falls detected: {fall_count}")
            print(f"Total runtime: {total_time:.2f} seconds")
            if frame_count > 0:
                print(f"Average FPS: {frame_count / total_time:.2f}")
            if writer:
                print(f"Output video saved to: {output_path}")
            
            return True

def main():
    parser = argparse.ArgumentParser(description="Video Fall Detection with Snapdragon X Elite Acceleration")
    parser.add_argument("--video", help="Path to input video file (optional)")
    parser.add_argument("--camera", type=int, default=1, help="Camera index (default: 1)")
    parser.add_argument("--output", help="Path to output video file (optional)")
    parser.add_argument("--duration", type=int, help="Maximum duration in seconds (optional)")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed for video files (default: 1.0)")
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
    detector = VideoFallDetector(
        video_source=args.video,
        camera_index=args.camera,
        enable_acceleration=not args.disable_acceleration,
        resolution=resolution
    )
    
    detector.run(output_path=args.output, max_duration=args.duration, playback_speed=args.speed)

if __name__ == "__main__":
    main()
