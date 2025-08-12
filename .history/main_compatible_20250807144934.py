# Compatible Fall Detection System - Main Application
# Works without MediaPipe using OpenCV-based detection

import cv2
import numpy as np
import sounddevice as sd
import threading
import time
from queue import Queue
from typing import Optional

# Import our compatible detector
from fall_detector_opencv import FallDetector

class SimpleFallDetectionSystem:
    def __init__(self):
        # Initialize components
        self.fall_detector = FallDetector()
        
        # Audio settings (simplified without Whisper)
        self.audio_sample_rate = 16000
        self.audio_buffer_duration = 2.0  # seconds
        self.audio_buffer_size = int(self.audio_sample_rate * self.audio_buffer_duration)
        self.audio_queue = Queue()
        
        # State variables
        self.running = False
        self.current_alert = None
        self.alert_start_time = 0
        self.alert_duration = 3.0  # seconds to show alert
        
        # Detection results
        self.fall_detected = False
        self.help_detected = False
        self.last_confidence = None
        self.alert_cooldown = 3.0
        self.last_alert_time = 0
        
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio input - simplified version."""
        if status:
            print(f"Audio callback status: {status}")
        
        # Simple volume-based detection
        audio_data = indata[:, 0]  # Use first channel
        volume = np.sqrt(np.mean(audio_data**2))
        
        # Detect loud sounds as potential help calls
        self.help_detected = volume > 0.1  # Adjust threshold as needed
    
    def draw_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Draw detection status and alerts on frame."""
        height, width = frame.shape[:2]
        
        # Draw detection status
        status_y = 30
        color = (0, 0, 255) if self.fall_detected else (0, 255, 0)
        cv2.putText(frame, f"Fall Detected: {self.fall_detected}", 
                   (10, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        status_y += 30
        color = (0, 0, 255) if self.help_detected else (0, 255, 0)
        cv2.putText(frame, f"Loud Sound: {self.help_detected}", 
                   (10, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        if self.last_confidence is not None:
            status_y += 30
            cv2.putText(frame, f"Confidence: {self.last_confidence:.1f}", 
                       (10, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw alert if active
        current_time = time.time()
        if self.current_alert and (current_time - self.alert_start_time) < self.alert_duration:
            # Draw alert background
            alert_height = 100
            cv2.rectangle(frame, (0, height - alert_height), (width, height), (0, 0, 255), -1)
            
            # Draw alert text
            alert_text = "FALL DETECTED!" if self.fall_detected else "LOUD SOUND DETECTED!"
            text_size = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            text_x = (width - text_size[0]) // 2
            text_y = height - alert_height // 2 + text_size[1] // 2
            
            cv2.putText(frame, alert_text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        
        # Draw instructions
        instructions = [
            "Press 'q' to quit",
            "Press 'r' to reset detection",
            "OpenCV-based detection (no MediaPipe)"
        ]
        
        for i, instruction in enumerate(instructions):
            cv2.putText(frame, instruction, (width - 350, 30 + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def should_trigger_alert(self, fall_detected: bool, help_detected: bool) -> bool:
        """Simple alert trigger logic with cooldown."""
        current_time = time.time()
        
        if (fall_detected or help_detected) and (current_time - self.last_alert_time) >= self.alert_cooldown:
            self.last_alert_time = current_time
            return True
        return False
    
    def run(self):
        """Main execution loop."""
        print("Starting Compatible Fall Detection System...")
        print("Using OpenCV-based motion detection (MediaPipe not required)")
        print("Initializing camera and microphone...")
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera")
            print("Trying alternative camera indices...")
            for i in range(1, 5):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    print(f"Camera found at index {i}")
                    break
            else:
                print("No camera found. Exiting...")
                return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Start audio stream
        try:
            audio_stream = sd.InputStream(
                samplerate=self.audio_sample_rate,
                channels=1,
                callback=self.audio_callback,
                blocksize=1024
            )
            audio_stream.start()
            print("Audio stream started successfully")
        except Exception as e:
            print(f"Warning: Could not start audio stream: {e}")
            print("Continuing with video-only detection...")
            audio_stream = None
        
        self.running = True
        print("System ready! Press 'q' to quit.")
        
        try:
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Detect fall from frame (every few frames to improve performance)
                if frame_count % 3 == 0:  # Process every 3rd frame
                    self.fall_detected, self.last_confidence = self.fall_detector.detect_fall_from_frame(frame)
                
                frame_count += 1
                
                # Check if alert should be triggered
                if self.should_trigger_alert(self.fall_detected, self.help_detected):
                    self.current_alert = True
                    self.alert_start_time = time.time()
                    print(f"ALERT TRIGGERED! Fall: {self.fall_detected}, Sound: {self.help_detected}")
                
                # Draw motion analysis
                frame = self.fall_detector.draw_pose_landmarks(frame)
                
                # Draw overlay
                frame = self.draw_overlay(frame)
                
                # Display frame
                cv2.imshow('Compatible Fall Detection System', frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    print("Resetting detection...")
                    self.fall_detector = FallDetector()  # Reset detector
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        
        finally:
            # Cleanup
            self.running = False
            cap.release()
            if audio_stream:
                audio_stream.stop()
                audio_stream.close()
            cv2.destroyAllWindows()
            print("System shutdown complete.")

def main():
    """Main entry point."""
    print("=" * 60)
    print("🚀 Compatible Fall Detection System")
    print("=" * 60)
    print("This version works without MediaPipe!")
    print("Using OpenCV-based motion detection instead.")
    print("=" * 60)
    
    system = SimpleFallDetectionSystem()
    system.run()

if __name__ == "__main__":
    main()
