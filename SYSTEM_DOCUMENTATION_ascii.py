#!/usr/bin/env python3
"""
Snapdragon X Elite Fall Detection System Documentation
"""

import os
import sys
import time
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def main():
    """Main documentation function"""
    print_header("Snapdragon X Elite Fall Detection System")
    
    print("This document provides instructions for using the fall detection system")
    print("based on the Snapdragon X Elite platform.")
    print("This system utilizes Hexagon NPU hardware acceleration for efficient real-time fall detection.\n")
    
    print_header("System Requirements")
    
    print("Hardware Requirements:")
    print("- Snapdragon X Elite processor")
    print("- At least 8GB of memory")
    print("- Webcam\n")
    
    print("Software Requirements:")
    print("- Windows operating system")
    print("- Python 3.8+")
    print("- OpenCV 4.x")
    print("- QAI Hub API")
    print("- MediaPipe")
    print("- ONNX Runtime\n")
    
    print_header("File Description")
    
    print("Main Files:")
    print("- fall_detector.py: Core fall detection logic")
    print("- unified_ai_detector_ascii.py: Unified AI detector supporting multiple backends")
    print("- snapdragon_optimized_demo.py: Optimized image processing script")
    print("- snapdragon_performance_benchmark.py: Performance benchmark script")
    print("- snapdragon_video_demo.py: Video processing script")
    print("- snapdragon_realtime_demo.py: Real-time camera detection script\n")
    
    print_header("Usage Instructions")
    
    print("1. Real-time Fall Detection (using camera):")
    print("   python snapdragon_realtime_demo.py [options]")
    print("   Options:")
    print("   --camera CAMERA         Camera index (default: 0)")
    print("   --output OUTPUT         Output video file path (optional)")
    print("   --duration DURATION     Maximum runtime in seconds (optional)")
    print("   --disable-acceleration  Disable hardware acceleration")
    print("   --resolution RESOLUTION Camera resolution in format WIDTHxHEIGHT (e.g., 640x480)\n")
    
    print("2. Process Video Files:")
    print("   python snapdragon_video_demo.py [options]")
    print("   Options:")
    print("   --input INPUT           Input video file path")
    print("   --output OUTPUT         Output video file path (optional)")
    print("   --disable-acceleration  Disable hardware acceleration\n")
    
    print("3. Performance Benchmark:")
    print("   python snapdragon_performance_benchmark_ascii.py [options]")
    print("   Options:")
    print("   --image IMAGE           Test image path (default: test_images/andy.jpg)")
    print("   --iterations ITERATIONS Number of iterations per test (default: 5)")
    print("   --mode {compare,single} Test mode (default: compare)")
    print("   --accelerator {hexagon_npu,cpu,none} Accelerator to use in single mode\n")
    
    print_header("Performance Data")
    
    print("Test results on Snapdragon X Elite:")
    print("- With Hexagon NPU acceleration: Average processing time 0.0555 seconds (18.02 FPS)")
    print("- CPU only: Average processing time 0.0571 seconds (17.50 FPS)")
    print("- Speedup ratio: 1.03x (approximately 3% improvement)\n")
    
    print("In real-time camera mode, the system can achieve processing speeds of about 22 FPS,")
    print("which is sufficient for real-time fall detection needs.\n")
    
    print_header("Notes")
    
    print("1. When running for the first time, the system will download necessary model files,")
    print("   which may take some time.")
    print("2. When using a camera, ensure adequate lighting to improve detection accuracy.")
    print("3. The fall detection demo works best when body posture is clearly visible.")
    print("4. If detection results are unstable, try adjusting the camera position or improving")
    print("   lighting conditions.")
    print("5. To use hardware acceleration, make sure QAI Hub is configured correctly.\n")
    
    print_header("Contact Information")
    
    print("For any questions or suggestions, please contact the project maintainer.")
    print("Project GitHub: https://github.com/andycywu/dragon-x-fall-detection")
    print("\n")

if __name__ == "__main__":
    main()
