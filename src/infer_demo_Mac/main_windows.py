#!/usr/bin/env python3
"""
Main Entry Point for Dragon X Fall Detection System - Windows Version
For Qualcomm Device Cloud Compatibility
"""

import cv2
import numpy as np
import threading
import time
from queue import Queue
from typing import Optional
import os
import platform
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import components with fallback mechanisms
try:
    from fall_detector import FallDetector
    FALL_DETECTOR_AVAILABLE = True
except ImportError:
    logger.warning("Standard FallDetector not available, using OpenCV fallback")
    FALL_DETECTOR_AVAILABLE = False
    from fall_detector_opencv import OpenCVFallDetector as FallDetector

try:
    import sounddevice as sd
    from whisper_infer import WhisperKeywordDetector
    WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("Whisper or sounddevice not available, audio detection disabled")
    WHISPER_AVAILABLE = False

from fusion_trigger import FusionTrigger

class RealTimeFallDetectionSystem:
    def __init__(self):
        # Initialize components
        self.fall_detector = FallDetector()
        self.fusion_trigger = FusionTrigger(cooldown_seconds=3.0)
        
        # Initialize audio components if available
        self.whisper_detector = None
        if WHISPER_AVAILABLE:
            try:
                self.whisper_detector = WhisperKeywordDetector()
                
                # Audio settings
                self.audio_sample_rate = 16000
                self.audio_buffer_duration = 3.0  # seconds
                self.audio_buffer_size = int(self.audio_sample_rate * self.audio_buffer_duration)
                self.audio_queue = Queue()
                
                logger.info("Audio detection enabled")
            except Exception as e:
                logger.error(f"Error initializing WhisperKeywordDetector: {e}")
                WHISPER_AVAILABLE = False
        
        # State variables
        self.running = False
        self.current_alert = None
        self.alert_start_time = 0
        self.alert_duration = 3.0  # seconds to show alert
        
        # Detection results
        self.fall_detected = False
        self.help_detected = False
        self.last_angle = None
        
        # Platform detection
        self.is_windows = platform.system() == "Windows"
        self.default_camera_id = 1 if self.is_windows else 0
        
        logger.info(f"Platform: {platform.system()}")
        logger.info(f"Default camera ID: {self.default_camera_id}")
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio input."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Add audio data to queue
        audio_data = indata[:, 0]  # Use first channel
        self.audio_queue.put(audio_data.copy())
    
    def process_audio(self):
        """Process audio data in separate thread."""
        if not WHISPER_AVAILABLE or not self.whisper_detector:
            return
            
        audio_buffer = np.array([])
        
        while self.running:
            try:
                # Get audio data from queue
                if not self.audio_queue.empty():
                    new_audio = self.audio_queue.get_nowait()
                    audio_buffer = np.concatenate([audio_buffer, new_audio])
                    
                    # Keep buffer at fixed size
                    if len(audio_buffer) > self.audio_buffer_size:
                        audio_buffer = audio_buffer[-self.audio_buffer_size:]
                    
                    # Process if we have enough audio
                    if len(audio_buffer) >= self.audio_buffer_size:
                        self.help_detected = self.whisper_detector.detect_help_keyword(
                            audio_buffer, self.audio_sample_rate
                        )
                        
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                logger.error(f"Error in audio processing: {e}")
                time.sleep(0.1)
    
    def draw_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Draw detection status and alerts on frame."""
        height, width = frame.shape[:2]
        
        # Draw detection status
        status_y = 30
        cv2.putText(frame, f"Fall Detected: {self.fall_detected}", 
                   (10, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if WHISPER_AVAILABLE:
            status_y += 30
            cv2.putText(frame, f"Help Detected: {self.help_detected}", 
                       (10, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if self.last_angle is not None:
            status_y += 30
            cv2.putText(frame, f"Torso Angle: {self.last_angle:.1f}°", 
                       (10, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw alert if active
        if self.current_alert and (time.time() - self.alert_start_time) < self.alert_duration:
            # Draw alert background
            alert_height = 100
            cv2.rectangle(frame, (0, height - alert_height), (width, height), (0, 0, 255), -1)
            
            # Draw alert text
            alert_text = self.current_alert.message
            text_size = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            text_x = (width - text_size[0]) // 2
            text_y = height - alert_height // 2 + text_size[1] // 2
            
            cv2.putText(frame, alert_text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            
            # Draw confidence
            conf_text = f"Confidence: {self.current_alert.confidence:.1%}"
            cv2.putText(frame, conf_text, (10, height - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Draw system status
        status_text = "System Status:"
        cv2.putText(frame, status_text, (width - 200, height - 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        fall_status = "Fall Detection: Active" if FALL_DETECTOR_AVAILABLE else "Fall Detection: OpenCV Fallback"
        cv2.putText(frame, fall_status, (width - 200, height - 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        audio_status = "Audio Detection: Active" if WHISPER_AVAILABLE else "Audio Detection: Disabled"
        cv2.putText(frame, audio_status, (width - 200, height - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        platform_text = f"Platform: {platform.system()}"
        cv2.putText(frame, platform_text, (width - 200, height - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw instructions
        instructions = [
            "Press 'q' to quit",
            "Press 'c' to clear alert history",
            "Press 's' to show recent alerts"
        ]
        
        for i, instruction in enumerate(instructions):
            cv2.putText(frame, instruction, (width - 300, 30 + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def run(self, camera_id=None, resolution=(640, 480), display=True):
        """Main execution loop."""
        logger.info("Starting Fall Detection System...")
        logger.info("Initializing camera...")
        
        # Use provided camera ID or default
        if camera_id is None:
            camera_id = self.default_camera_id
            
        # Initialize camera
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            logger.error(f"Could not open camera with ID {camera_id}")
            logger.info("Trying default camera...")
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("Error: Could not open any camera")
                return
        
        logger.info(f"Camera opened with ID: {camera_id}")
        
        # Set camera properties
        width, height = resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Start audio stream if available
        audio_stream = None
        if WHISPER_AVAILABLE and self.whisper_detector:
            try:
                logger.info("Starting audio stream...")
                audio_stream = sd.InputStream(
                    samplerate=self.audio_sample_rate,
                    channels=1,
                    callback=self.audio_callback,
                    blocksize=1024
                )
                audio_stream.start()
                logger.info("Audio stream started")
            except Exception as e:
                logger.error(f"Error starting audio stream: {e}")
                WHISPER_AVAILABLE = False
        
        # Start audio processing thread if needed
        self.running = True
        audio_thread = None
        if WHISPER_AVAILABLE and self.whisper_detector:
            logger.info("Starting audio processing thread...")
            audio_thread = threading.Thread(target=self.process_audio, daemon=True)
            audio_thread.start()
        
        logger.info("System ready! Press 'q' to quit.")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.error("Could not read frame")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Detect fall from frame
                self.fall_detected, self.last_angle = self.fall_detector.detect_fall_from_frame(frame)
                
                # Check if alert should be triggered
                if self.fusion_trigger.should_trigger_alert(self.fall_detected, self.help_detected):
                    self.current_alert = self.fusion_trigger.alert_history[-1]
                    self.alert_start_time = time.time()
                    logger.info(f"ALERT TRIGGERED: {self.current_alert.message}")
                
                # Draw pose landmarks if available
                if hasattr(self.fall_detector, 'pose') and hasattr(self.fall_detector, 'draw_pose_landmarks'):
                    try:
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = self.fall_detector.pose.process(rgb_frame)
                        if results.pose_landmarks:
                            frame = self.fall_detector.draw_pose_landmarks(frame, results.pose_landmarks)
                    except Exception as e:
                        logger.warning(f"Error drawing pose landmarks: {e}")
                
                # Draw overlay
                frame = self.draw_overlay(frame)
                
                # Display frame if enabled
                if display:
                    cv2.imshow('Fall Detection System', frame)
                    
                    # Handle key presses
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('c'):
                        self.fusion_trigger.clear_history()
                        logger.info("Alert history cleared")
                    elif key == ord('s'):
                        recent_alerts = self.fusion_trigger.get_recent_alerts(5)
                        logger.info("\nRecent alerts:")
                        for alert in recent_alerts:
                            logger.info(f"  {time.strftime('%H:%M:%S', time.localtime(alert.timestamp))}: {alert.message}")
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        
        finally:
            # Cleanup
            self.running = False
            cap.release()
            if audio_stream:
                audio_stream.stop()
                audio_stream.close()
            if display:
                cv2.destroyAllWindows()
            logger.info("System shutdown complete.")

def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description="Dragon X Fall Detection System")
    
    parser.add_argument("--camera_id", type=int, help="Camera ID to use")
    parser.add_argument("--resolution", default="640x480", help="Camera resolution (WxH)")
    parser.add_argument("--no-display", dest="display", action="store_false", help="Run without visual display")
    parser.add_argument("--hardware_acceleration", action="store_true", help="Use hardware acceleration if available")
    
    parser.set_defaults(display=True)
    args = parser.parse_args()
    
    # Parse resolution
    if args.resolution:
        try:
            width, height = map(int, args.resolution.split("x"))
            args.resolution = (width, height)
        except ValueError:
            logger.warning(f"Invalid resolution format: {args.resolution}, using default 640x480")
            args.resolution = (640, 480)
    
    return args

def main():
    """Main entry point."""
    args = parse_args()
    
    # Display system information
    logger.info("=" * 50)
    logger.info("Dragon X Fall Detection System - Windows Version")
    logger.info("=" * 50)
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"Fall detection: {'Standard' if FALL_DETECTOR_AVAILABLE else 'OpenCV Fallback'}")
    logger.info(f"Audio detection: {'Enabled' if WHISPER_AVAILABLE else 'Disabled'}")
    logger.info("=" * 50)
    
    # Create and run system
    system = RealTimeFallDetectionSystem()
    system.run(
        camera_id=args.camera_id, 
        resolution=args.resolution,
        display=args.display
    )

if __name__ == "__main__":
    main()
