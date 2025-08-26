#!/usr/bin/env python3
"""
Snapdragon X Elite Performance Benchmark (Windows Version)
Tests fall detection performance with and without hardware acceleration
"""

import os
import sys
import cv2
import time
import numpy as np
import logging
import argparse
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceBenchmark:
    """Performance benchmark for fall detection with Snapdragon X Elite"""
    
    def __init__(self, test_images_dir=None, iterations=5):
        """Initialize the performance benchmark
        
        Args:
            test_images_dir (str): Directory containing test images
            iterations (int): Number of iterations for each test
        """
        logger.info("Initializing Performance Benchmark")
        
        # Configure test parameters
        self.test_images_dir = test_images_dir or "test_images"
        self.iterations = iterations
        
        # Prepare test images
        self.test_images = self._load_test_images()
        
        # Results storage
        self.results = {
            "platform_info": self._get_platform_info(),
            "test_parameters": {
                "iterations": iterations,
                "test_images_count": len(self.test_images)
            },
            "benchmarks": []
        }
    
    def _get_platform_info(self):
        """Get platform information"""
        platform_info = {
            "system": sys.platform,
            "python_version": sys.version,
            "opencv_version": cv2.__version__
        }
        
        # Try to get more detailed platform info
        try:
            import platform
            system = platform.system().lower()
            machine = platform.machine().lower()
            processor = platform.processor().lower()
            
            platform_info.update({
                "system_detailed": system,
                "machine": machine,
                "processor": processor
            })
            
            # Determine if running on Snapdragon
            if "snapdragon" in processor.lower() or "qualcomm" in processor.lower():
                platform_info["platform_type"] = "snapdragon_x_elite"
            elif system == "windows" and ("arm" in machine or "aarch64" in machine):
                platform_info["platform_type"] = "windows_arm"
            else:
                platform_info["platform_type"] = "generic"
                
        except Exception as e:
            logger.warning(f"Could not get detailed platform info: {e}")
        
        return platform_info
    
    def _load_test_images(self):
        """Load test images from directory"""
        test_images = []
        
        if not os.path.exists(self.test_images_dir):
            logger.warning(f"Test images directory not found: {self.test_images_dir}")
            
            # Create a synthetic test image
            logger.info("Creating synthetic test image")
            synthetic_image = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Draw a simple person silhouette
            cv2.rectangle(synthetic_image, (280, 100), (360, 180), (255, 255, 255), -1)  # head
            cv2.rectangle(synthetic_image, (250, 180), (390, 350), (255, 255, 255), -1)  # body
            cv2.rectangle(synthetic_image, (250, 350), (300, 450), (255, 255, 255), -1)  # left leg
            cv2.rectangle(synthetic_image, (340, 350), (390, 450), (255, 255, 255), -1)  # right leg
            cv2.rectangle(synthetic_image, (180, 200), (250, 250), (255, 255, 255), -1)  # left arm
            cv2.rectangle(synthetic_image, (390, 200), (460, 250), (255, 255, 255), -1)  # right arm
            
            test_images.append(("synthetic_test.jpg", synthetic_image))
            
            # Create test directory and save synthetic image
            os.makedirs(self.test_images_dir, exist_ok=True)
            cv2.imwrite(os.path.join(self.test_images_dir, "synthetic_test.jpg"), synthetic_image)
            
            return test_images
        
        # Load all images from the test directory
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        for filename in os.listdir(self.test_images_dir):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                filepath = os.path.join(self.test_images_dir, filename)
                try:
                    image = cv2.imread(filepath)
                    if image is not None:
                        test_images.append((filename, image))
                    else:
                        logger.warning(f"Could not load image: {filepath}")
                except Exception as e:
                    logger.warning(f"Error loading image {filepath}: {e}")
        
        if not test_images:
            logger.warning("No valid test images found")
            
            # Create a synthetic test image as fallback
            synthetic_image = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.rectangle(synthetic_image, (280, 100), (360, 180), (255, 255, 255), -1)  # head
            cv2.rectangle(synthetic_image, (250, 180), (390, 350), (255, 255, 255), -1)  # body
            
            test_images.append(("synthetic_test.jpg", synthetic_image))
            cv2.imwrite(os.path.join(self.test_images_dir, "synthetic_test.jpg"), synthetic_image)
        
        logger.info(f"Loaded {len(test_images)} test images")
        return test_images
    
    def run_benchmark(self, name, detector_factory, warm_up=2):
        """Run benchmark for a specific detector configuration
        
        Args:
            name (str): Name of the benchmark
            detector_factory (callable): Function that returns a detector instance
            warm_up (int): Number of warm-up iterations (not counted)
        """
        logger.info(f"Running benchmark: {name}")
        print(f"\nRunning benchmark: {name}")
        print("=" * 50)
        
        benchmark_results = {
            "name": name,
            "image_results": [],
            "summary": {}
        }
        
        # Create detector
        detector = detector_factory()
        
        # Warm-up
        if warm_up > 0:
            print(f"Warming up for {warm_up} iterations...")
            for _ in range(warm_up):
                for _, image in self.test_images:
                    detector.detect_fall_from_frame(image)
        
        # Run benchmark for each test image
        all_times = []
        
        for img_name, image in self.test_images:
            print(f"Testing image: {img_name}")
            image_times = []
            
            # Run multiple iterations
            for i in range(self.iterations):
                start_time = time.time()
                result = detector.detect_fall_from_frame(image)
                elapsed = time.time() - start_time
                
                image_times.append(elapsed)
                all_times.append(elapsed)
                
                # Show progress
                sys.stdout.write(f"\rIteration {i+1}/{self.iterations} - {elapsed*1000:.1f} ms")
                sys.stdout.flush()
            
            print()  # New line after progress
            
            # Calculate statistics for this image
            avg_time = sum(image_times) / len(image_times)
            std_dev = np.std(image_times)
            min_time = min(image_times)
            max_time = max(image_times)
            
            # Log results
            print(f"Results for {img_name}:")
            print(f"  Average: {avg_time*1000:.2f} ms")
            print(f"  Min: {min_time*1000:.2f} ms")
            print(f"  Max: {max_time*1000:.2f} ms")
            print(f"  Std Dev: {std_dev*1000:.2f} ms")
            
            # Store results
            benchmark_results["image_results"].append({
                "image_name": img_name,
                "average_time": avg_time,
                "min_time": min_time,
                "max_time": max_time,
                "std_dev": std_dev,
                "iterations": self.iterations
            })
        
        # Calculate overall statistics
        avg_time = sum(all_times) / len(all_times)
        std_dev = np.std(all_times)
        min_time = min(all_times)
        max_time = max(all_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        
        # Store summary
        benchmark_results["summary"] = {
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "std_dev": std_dev,
            "fps": fps,
            "total_iterations": self.iterations * len(self.test_images)
        }
        
        # Log summary
        print("\nOverall Results:")
        print(f"  Average: {avg_time*1000:.2f} ms")
        print(f"  Min: {min_time*1000:.2f} ms")
        print(f"  Max: {max_time*1000:.2f} ms")
        print(f"  Std Dev: {std_dev*1000:.2f} ms")
        print(f"  FPS: {fps:.2f}")
        
        # Add to results
        self.results["benchmarks"].append(benchmark_results)
        
        return benchmark_results
    
    def run_all_benchmarks(self):
        """Run all benchmarks"""
        from fall_detector import FallDetector
        
        # Create factories for different configurations
        def create_accelerated_detector():
            # Enable hardware acceleration
            os.environ['ENABLE_QAI_ACCELERATION'] = 'true'
            os.environ['QAI_HUB_ACCELERATOR'] = 'hexagon_npu'
            os.environ['QAI_OPTIMIZATION_LEVEL'] = 'performance'
            return FallDetector()
        
        def create_cpu_detector():
            # Disable hardware acceleration
            os.environ['ENABLE_QAI_ACCELERATION'] = 'false'
            os.environ.pop('QAI_HUB_ACCELERATOR', None)
            os.environ.pop('QAI_OPTIMIZATION_LEVEL', None)
            return FallDetector()
        
        # Run benchmarks
        print("\nStarting Performance Benchmark")
        print("=" * 50)
        print(f"Platform: {self.results['platform_info'].get('platform_type', 'unknown')}")
        print(f"Test Images: {len(self.test_images)}")
        print(f"Iterations per image: {self.iterations}")
        print()
        
        # Run CPU benchmark first
        cpu_results = self.run_benchmark("CPU (No Acceleration)", create_cpu_detector)
        
        # Run accelerated benchmark
        accel_results = self.run_benchmark("Snapdragon X Elite (NPU Acceleration)", create_accelerated_detector)
        
        # Calculate improvement
        cpu_time = cpu_results["summary"]["average_time"]
        accel_time = accel_results["summary"]["average_time"]
        
        if cpu_time > 0:
            improvement = (cpu_time - accel_time) / cpu_time * 100
            self.results["improvement"] = {
                "percentage": improvement,
                "cpu_fps": cpu_results["summary"]["fps"],
                "accelerated_fps": accel_results["summary"]["fps"],
                "fps_increase": accel_results["summary"]["fps"] - cpu_results["summary"]["fps"]
            }
            
            print("\nPerformance Improvement:")
            print(f"  CPU: {cpu_results['summary']['fps']:.2f} FPS")
            print(f"  Accelerated: {accel_results['summary']['fps']:.2f} FPS")
            print(f"  Improvement: {improvement:.2f}%")
        
        # Save results
        self.save_results()
        
        return self.results
    
    def save_results(self, filename=None):
        """Save benchmark results to file"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nBenchmark results saved to: {filename}")
        
        return filename

def main():
    parser = argparse.ArgumentParser(description="Snapdragon X Elite Performance Benchmark")
    parser.add_argument("--images", help="Directory containing test images (default: test_images)")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations (default: 5)")
    parser.add_argument("--output", help="Output filename for results (default: auto-generated)")
    
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark(
        test_images_dir=args.images,
        iterations=args.iterations
    )
    
    results = benchmark.run_all_benchmarks()
    
    if args.output:
        benchmark.save_results(args.output)
    
    return results

if __name__ == "__main__":
    main()
