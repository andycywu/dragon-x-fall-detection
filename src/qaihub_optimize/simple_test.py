#!/usr/bin/env python3
"""
Simple test script to verify the basic structure works.
This version uses placeholder implementations to test the integration.
"""

import cv2
import numpy as np
import time
from typing import Tuple, Optional

# Simple placeholder implementations for testing

class SimpleFallDetector:
    """Simplified fall detector for testing without MediaPipe"""
    
    def detect_fall_from_frame(self, frame: np.ndarray) -> Tuple[bool, Optional[float]]:
        """
        Simplified fall detection - detects based on image brightness
        (placeholder logic for testing)
        """
        # Convert to grayscale and calculate average brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        
        # Simple heuristic: very dark or very bright images might indicate a fall
        fall_detected = avg_brightness < 50 or avg_brightness > 200
        angle = 90.0 - (avg_brightness - 128) * 0.5  # Mock angle calculation
        
        return fall_detected, angle

class SimpleWhisperDetector:
    """Simplified whisper detector for testing"""
    
    def detect_help_keyword(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> bool:
        """
        Simplified keyword detection - detects based on audio amplitude
        (placeholder logic for testing)
        """
        if len(audio_chunk) == 0:
            return False
            
        # Simple heuristic: detect loud sounds as potential help calls
        max_amplitude = np.max(np.abs(audio_chunk))
        return max_amplitude > 0.5

def test_basic_functionality():
    """Test basic functionality with simple implementations"""
    
    print("🧪 Testing Fall Detection System (Simplified)")
    print("=" * 50)
    
    # Test fall detector
    print("1. Testing Fall Detector...")
    fall_detector = SimpleFallDetector()
    
    # Create test image
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    test_image[:, :] = [100, 100, 100]  # Gray image
    
    fall_detected, angle = fall_detector.detect_fall_from_frame(test_image)
    print(f"   ✅ Fall detected: {fall_detected}, Angle: {angle:.1f}°")
    
    # Test whisper detector
    print("2. Testing Audio Detector...")
    whisper_detector = SimpleWhisperDetector()
    
    # Create test audio
    test_audio = np.random.normal(0, 0.1, 16000)  # 1 second of quiet audio
    loud_audio = np.random.normal(0, 0.8, 16000)  # 1 second of loud audio
    
    quiet_result = whisper_detector.detect_help_keyword(test_audio)
    loud_result = whisper_detector.detect_help_keyword(loud_audio)
    print(f"   ✅ Quiet audio result: {quiet_result}")
    print(f"   ✅ Loud audio result: {loud_result}")
    
    # Test fusion trigger
    print("3. Testing Fusion Trigger...")
    from fusion_trigger import FusionTrigger
    
    fusion = FusionTrigger(cooldown_seconds=1.0)
    
    # Test various combinations
    tests = [
        (True, False, "Fall only"),
        (False, True, "Audio only"),
        (True, True, "Both detected"),
        (False, False, "Nothing detected")
    ]
    
    for fall, audio, description in tests:
        result = fusion.should_trigger_alert(fall, audio)
        print(f"   ✅ {description}: Alert = {result}")
        time.sleep(1.1)  # Wait for cooldown
    
    print("\n4. Testing Camera Access...")
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("   ✅ Camera accessible")
        ret, frame = cap.read()
        if ret:
            print(f"   ✅ Frame captured: {frame.shape}")
            
            # Test fall detection on real frame
            fall_detected, angle = fall_detector.detect_fall_from_frame(frame)
            print(f"   ✅ Real frame analysis: Fall={fall_detected}, Angle={angle:.1f}°")
        cap.release()
    else:
        print("   ⚠️  Camera not accessible")
    
    print("\n🎉 Basic functionality test complete!")
    print("\nNext steps:")
    print("1. Install MediaPipe for full pose detection")
    print("2. Install Whisper for full audio detection")
    print("3. Run 'python main.py' for full real-time detection")
    print("4. Run 'streamlit run ui_dashboard.py' for web interface")

if __name__ == "__main__":
    test_basic_functionality()
