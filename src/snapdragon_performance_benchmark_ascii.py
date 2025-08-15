#!/usr/bin/env python3
"""
Snapdragon X Elite Performance Benchmark
Compares performance of different acceleration methods
"""

import os
import sys
import cv2
import time
import numpy as np
import logging
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def benchmark_fall_detection(image_path, accelerator=None, iterations=5):
    """Run performance benchmarks"""
    print(f"Testing image: {image_path}")
    print(f"Accelerator: {accelerator if accelerator else 'default'}")
    print(f"Iterations: {iterations}")
    
    # Load test image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to load image: {image_path}")
        return
    
    print(f"Image dimensions: {image.shape}")
    
    # Set environment variables to control acceleration
    if accelerator:
        if accelerator == "hexagon_npu":
            os.environ['ENABLE_QAI_ACCELERATION'] = 'true'
            os.environ['QAI_HUB_ACCELERATOR'] = 'hexagon_npu'
            os.environ['QAI_OPTIMIZATION_LEVEL'] = 'performance'
        elif accelerator == "cpu":
            if 'ENABLE_QAI_ACCELERATION' in os.environ:
                del os.environ['ENABLE_QAI_ACCELERATION']
            if 'QAI_HUB_ACCELERATOR' in os.environ:
                del os.environ['QAI_HUB_ACCELERATOR']
    
    try:
        # Load UnifiedAIDetector (detects platform and available accelerators)
        print("Initializing AI detector...")
        from unified_ai_detector_ascii import UnifiedAIDetector
        detector = UnifiedAIDetector()
        print(f"Detected platform: {detector.platform}")
        print(f"Available accelerators: {detector.accelerators}")
        
        # Load fall detector
        print("Initializing fall detector...")
        from fall_detector import FallDetector
        fall_detector = FallDetector()
        
        # Run benchmark
        print("\nStarting performance test...")
        times = []
        
        for i in range(iterations):
            print(f"Iteration {i+1}/{iterations}...")
            
            # Measure processing time
            start_time = time.time()
            result = fall_detector.detect_fall_from_frame(image)
            end_time = time.time()
            
            process_time = end_time - start_time
            times.append(process_time)
            
            if result is None:
                print(f"  No pose detected, processing time: {process_time:.4f} seconds")
            else:
                is_falling, confidence = result
                status = "FALL" if is_falling else "NORMAL"
                print(f"  Result: {status}, Confidence: {confidence:.2f}, Processing time: {process_time:.4f} seconds")
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print("\nTest Results Summary:")
        print(f"Platform: {detector.platform}")
        print(f"Accelerator: {accelerator if accelerator else 'default'}")
        print(f"Average processing time: {avg_time:.4f} seconds")
        print(f"Minimum processing time: {min_time:.4f} seconds")
        print(f"Maximum processing time: {max_time:.4f} seconds")
        print(f"Frames per second (FPS): {1/avg_time:.2f}")
        
        return {
            "platform": detector.platform,
            "accelerator": accelerator,
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "fps": 1/avg_time
        }
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_accelerators(image_path, iterations=5):
    """Compare performance of different accelerators"""
    print("=" * 70)
    print("Snapdragon X Elite Accelerator Performance Comparison")
    print("=" * 70)
    
    results = {}
    
    # Test CPU (no acceleration)
    print("\n=== Testing CPU (no acceleration) ===")
    results["cpu"] = benchmark_fall_detection(image_path, "cpu", iterations)
    
    # Test Hexagon NPU
    print("\n=== Testing Hexagon NPU acceleration ===")
    results["hexagon_npu"] = benchmark_fall_detection(image_path, "hexagon_npu", iterations)
    
    # Compare results
    print("\n" + "=" * 70)
    print("Performance Comparison Results")
    print("=" * 70)
    
    if "cpu" in results and "hexagon_npu" in results:
        cpu_time = results["cpu"]["average_time"]
        npu_time = results["hexagon_npu"]["average_time"]
        speedup = cpu_time / npu_time
        
        print(f"CPU average processing time: {cpu_time:.4f} seconds ({1/cpu_time:.2f} FPS)")
        print(f"Hexagon NPU average processing time: {npu_time:.4f} seconds ({1/npu_time:.2f} FPS)")
        print(f"Speedup factor: {speedup:.2f}x")
        
        if speedup > 1:
            print(f"Hexagon NPU acceleration improved performance by {(speedup-1)*100:.1f}%")
        else:
            print(f"Hexagon NPU did not provide acceleration, performance decreased by {(1-speedup)*100:.1f}%")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Snapdragon X Elite Performance Benchmark")
    parser.add_argument("--image", default="test_images/andy.jpg", help="Path to test image")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations per test")
    parser.add_argument("--mode", choices=["compare", "single"], default="compare", 
                        help="Test mode: compare (different accelerators) or single (one accelerator)")
    parser.add_argument("--accelerator", choices=["hexagon_npu", "cpu", "none"], default=None,
                        help="Accelerator to use in single mode")
    
    args = parser.parse_args()
    
    if args.mode == "compare":
        compare_accelerators(args.image, args.iterations)
    else:
        benchmark_fall_detection(args.image, args.accelerator, args.iterations)

if __name__ == "__main__":
    main()
