# Task: Integrate BlazePose + Whisper + Fusion Trigger.
# Use webcam and microphone stream to run real-time detection.
# Display fall/hit alerts in OpenCV window overlay.
# This is the main entry point for real-time testing.

import cv2
import numpy as np
import sounddevice as sd
import threading
import time
from queue import Queue
from typing import Optional

from detectors.fall_detector import FallDetector
from detectors.whisper_infer import WhisperKeywordDetector
from detectors.fusion_trigger import FusionTrigger

class RealTimeFallDetectionSystem:
    def __init__(self):
        # Initialize components
        self.fall_detector = FallDetector()
        self.whisper_detector = WhisperKeywordDetector()
        self.fusion_trigger = FusionTrigger(cooldown_seconds=3.0)
        
        # Audio settings
        self.audio_sample_rate = 16000
        self.audio_buffer_duration = 3.0  # seconds
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
        self.last_angle = None
        
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio input."""
        if status:
            print(f"Audio callback status: {status}")
        
        # Add audio data to queue
        audio_data = indata[:, 0]  # Use first channel
        self.audio_queue.put(audio_data.copy())
    
    def process_audio(self):
        """Process audio data in separate thread."""
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
                print(f"Error in audio processing: {e}")
                time.sleep(0.1)
    
    def draw_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Draw detection status and alerts on frame."""
        height, width = frame.shape[:2]
        
        # Draw detection status
        status_y = 30
        cv2.putText(frame, f"Fall Detected: {self.fall_detected}", 
                   (10, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
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
    
    def run(self):
        """Main execution loop."""
        print("Starting Fall Detection System...")
        print("Initializing camera and microphone...")
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera")
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
        except Exception as e:
            print(f"Error starting audio stream: {e}")
            cap.release()
            return
        
        # Start audio processing thread
        self.running = True
        audio_thread = threading.Thread(target=self.process_audio, daemon=True)
        audio_thread.start()
        
        print("System ready! Press 'q' to quit.")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Detect fall from frame
                self.fall_detected, self.last_angle = self.fall_detector.detect_fall_from_frame(frame)
                
                # Check if alert should be triggered
                if self.fusion_trigger.should_trigger_alert(self.fall_detected, self.help_detected):
                    self.current_alert = self.fusion_trigger.alert_history[-1]
                    self.alert_start_time = time.time()
                    print(f"ALERT TRIGGERED: {self.current_alert.message}")
                
                # Draw pose landmarks
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.fall_detector.pose.process(rgb_frame)
                if results.pose_landmarks:
                    frame = self.fall_detector.draw_pose_landmarks(frame, results.pose_landmarks)
                
                # Draw overlay
                frame = self.draw_overlay(frame)
                
                # Display frame
                cv2.imshow('Fall Detection System', frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('c'):
                    self.fusion_trigger.clear_history()
                    print("Alert history cleared")
                elif key == ord('s'):
                    recent_alerts = self.fusion_trigger.get_recent_alerts(5)
                    print("\nRecent alerts:")
                    for alert in recent_alerts:
                        print(f"  {time.strftime('%H:%M:%S', time.localtime(alert.timestamp))}: {alert.message}")
                    print()
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        
        finally:
            # Cleanup
            self.running = False
            cap.release()
            audio_stream.stop()
            audio_stream.close()
            cv2.destroyAllWindows()
            print("System shutdown complete.")

def main():
    """Main entry point."""
    system = RealTimeFallDetectionSystem()
    system.run()

if __name__ == "__main__":
    main()
