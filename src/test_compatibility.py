#!/usr/bin/env python3
"""
Test script for the compatible fall detection system.
This tests all components without requiring camera access.
"""

import cv2
import numpy as np
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_opencv_installation():
    """Test if OpenCV is working correctly."""
    print("1. Testing OpenCV installation...")
    try:
        import cv2
        print(f"   ✅ OpenCV version: {cv2.__version__}")
        
        # Test image creation and processing
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        test_image[:, :] = [100, 100, 100]  # Gray image
        
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        print(f"   ✅ Image processing works: {gray.shape}")
        
        return True
    except Exception as e:
        print(f"   ❌ OpenCV test failed: {e}")
        return False

def test_fall_detector():
    """Test the fall detector component."""
    print("2. Testing Fall Detector...")
    try:
        from fall_detector_opencv import FallDetector
        
        detector = FallDetector()
        print("   ✅ Fall detector initialized")
        
        # Create test images
        test_images = [
            np.zeros((480, 640, 3), dtype=np.uint8),  # Black image
            np.ones((480, 640, 3), dtype=np.uint8) * 255,  # White image
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)  # Random image
        ]
        
        for i, img in enumerate(test_images):
            fall_detected, confidence = detector.detect_fall_from_frame(img)
            print(f"   ✅ Test image {i+1}: Fall={fall_detected}, Confidence={confidence}")
        
        return True
    except Exception as e:
        print(f"   ❌ Fall detector test failed: {e}")
        return False

def test_audio_components():
    """Test audio components."""
    print("3. Testing Audio Components...")
    try:
        import sounddevice as sd
        import numpy as np
        
        # List audio devices
        devices = sd.query_devices()
        print(f"   ✅ Found {len(devices)} audio devices")
        
        # Test audio array creation
        sample_rate = 16000
        duration = 1.0
        test_audio = np.random.normal(0, 0.1, int(sample_rate * duration))
        print(f"   ✅ Audio array created: {test_audio.shape}")
        
        return True
    except Exception as e:
        print(f"   ❌ Audio test failed: {e}")
        return False

def test_streamlit_components():
    """Test Streamlit installation."""
    print("4. Testing Streamlit Components...")
    try:
        import streamlit as st
        import plotly.graph_objects as go
        import pandas as pd
        
        print("   ✅ Streamlit imported successfully")
        print("   ✅ Plotly imported successfully")
        print("   ✅ Pandas imported successfully")
        
        # Test data structures
        test_data = pd.DataFrame({
            'time': [1, 2, 3, 4, 5],
            'value': [10, 20, 15, 25, 30]
        })
        print(f"   ✅ Test dataframe created: {test_data.shape}")
        
        return True
    except Exception as e:
        print(f"   ❌ Streamlit components test failed: {e}")
        return False

def test_camera_access():
    """Test camera access (optional)."""
    print("5. Testing Camera Access...")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("   ✅ Primary camera accessible")
            ret, frame = cap.read()
            if ret:
                print(f"   ✅ Frame captured successfully: {frame.shape}")
            else:
                print("   ⚠️  Could not capture frame")
            cap.release()
        else:
            print("   ⚠️  Primary camera not accessible (this is OK for testing)")
            
        return True
    except Exception as e:
        print(f"   ⚠️  Camera test failed: {e} (this is OK for testing)")
        return True  # Don't fail the test for camera issues

def test_integration():
    """Test system integration."""
    print("6. Testing System Integration...")
    try:
        # Import main compatible system
        from main_compatible import SimpleFallDetectionSystem
        
        # Create system instance (don't run it)
        system = SimpleFallDetectionSystem()
        print("   ✅ Compatible system created successfully")
        
        # Test detection logic
        result = system.should_trigger_alert(True, False)
        print(f"   ✅ Alert logic test: {result}")
        
        return True
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running Compatibility Tests")
    print("=" * 50)
    
    tests = [
        test_opencv_installation,
        test_fall_detector,
        test_audio_components,
        test_streamlit_components,
        test_camera_access,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
        print()
    
    print("=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your system is ready to use.")
        print("\nNext steps:")
        print("1. Run the main application:")
        print("   /Users/andycyw/mvp_fall_detection_starter/.venv/bin/python main_compatible.py")
        print("\n2. Or run the Streamlit dashboard:")
        print("   /Users/andycyw/mvp_fall_detection_starter/.venv/bin/python -m streamlit run ui_dashboard.py")
    else:
        print("⚠️  Some tests failed, but the core system should still work.")
        print("Check the error messages above for details.")
    
    print("\n📝 Note: Camera permissions may be required for full functionality.")

if __name__ == "__main__":
    main()
