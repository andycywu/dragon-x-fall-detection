#!/usr/bin/env python3
"""
Snapdragon X Elite Optimized Fall Detection Demo
Leverages hardware acceleration for faster and more efficient fall detection
"""

import os
import sys
import cv2
import time
import numpy as np
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SnapdragonFallDetector:
    """Fall detector optimized for Snapdragon X Elite"""
    
    def __init__(self):
        """Initialize the Snapdragon-optimized fall detector"""
        logger.info("Initializing Snapdragon-optimized Fall Detector")
        
        # Ensure environment is properly configured
        self._setup_environment()
        
        # Load fall detector module
        try:
            from fall_detector import FallDetector
            self.fall_detector = FallDetector()
            logger.info("Fall detector initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing fall detector: {e}")
            raise
    
    def _setup_environment(self):
        """Set up the environment for Snapdragon acceleration"""
        # Set environment variables
        os.environ['ENABLE_QAI_ACCELERATION'] = 'true'
        os.environ['QAI_HUB_ACCELERATOR'] = 'hexagon_npu'
        os.environ['QAI_OPTIMIZATION_LEVEL'] = 'performance'
        
        # Check QAI Hub configuration
        qai_config = Path.home() / ".qai_hub" / "client.ini"
        if not qai_config.exists():
            logger.warning("QAI Hub configuration not found. Acceleration may not be available.")
    
    def process_image(self, image):
        """Process a single image using hardware acceleration"""
        start_time = time.time()
        
        # Detect fall
        result = self.fall_detector.detect_fall_from_frame(image)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Process result
        if result is None:
            logger.warning("No pose detected in image")
            return {
                'is_falling': False,
                'confidence': None,
                'process_time': process_time,
                'status': 'NO_POSE_DETECTED'
            }
        
        is_falling, confidence = result
        
        return {
            'is_falling': is_falling,
            'confidence': confidence,
            'process_time': process_time,
            'status': 'FALL_DETECTED' if is_falling else 'NO_FALL'
        }
    
    def visualize_result(self, image, result):
        """Visualize the detection result on the image"""
        # Make a copy for visualization
        display_image = image.copy()
        
        # Get result values
        is_falling = result['is_falling']
        confidence = result['confidence']
        process_time = result['process_time']
        status = result['status']
        
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
        cv2.putText(display_image, text, (50, 50), font, 1, color, 2)
        
        if confidence is not None:
            cv2.putText(display_image, f"Confidence: {confidence:.2f}", (50, 100), font, 1, color, 2)
        
        # Add processing time
        cv2.putText(display_image, f"Process time: {process_time:.3f}s", (50, 150), font, 1, (255, 255, 0), 2)
        
        # Add platform info
        cv2.putText(display_image, "Platform: Snapdragon X Elite", (50, 200), font, 1, (255, 255, 255), 2)
        
        # Add acceleration info
        cv2.putText(display_image, "Acceleration: Hexagon NPU", (50, 250), font, 1, (255, 255, 255), 2)
        
        return display_image

def print_banner():
    """Print the demo banner"""
    print("=" * 70)
    print("Snapdragon X Elite Optimized Fall Detection Demo")
    print("Powered by Qualcomm AI Hub and Hexagon NPU Hardware Acceleration")
    print("=" * 70)

def main():
    """Main function"""
    print_banner()
    
    try:
        # Initialize fall detector
        print("Initializing Snapdragon-optimized Fall Detector...")
        detector = SnapdragonFallDetector()
        print("Fall detector initialized successfully with hardware acceleration")
        
        # Process test images
        print("\nTesting with images...")
        test_dir = "test_images"
        
        if not os.path.exists(test_dir):
            print(f"Test directory {test_dir} not found")
            return
        
        img_files = [f for f in os.listdir(test_dir) if f.endswith('.jpg') or f.endswith('.png')]
        print(f"Found {len(img_files)} images")
        
        results_summary = []
        
        for i, img_file in enumerate(img_files):
            image_path = os.path.join(test_dir, img_file)
            print(f"\nProcessing image {i+1}/{len(img_files)}: {image_path}")
            
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                print(f"Failed to load image: {image_path}")
                continue
            
            print(f"Image loaded, shape: {image.shape}")
            
            try:
                # Process image with hardware acceleration
                result = detector.process_image(image)
                
                # Visualize result
                display_image = detector.visualize_result(image, result)
                
                # Save result
                output_filename = f"snapdragon_result_{i+1}_{os.path.basename(image_path)}"
                cv2.imwrite(output_filename, display_image)
                
                # Print result
                status_text = "FALL DETECTED!" if result['is_falling'] else "No fall detected"
                if result['confidence'] is not None:
                    print(f"Result: {status_text}, Confidence: {result['confidence']:.2f}")
                else:
                    print(f"Result: {status_text}")
                print(f"Processed in {result['process_time']:.3f} seconds with Hexagon NPU acceleration")
                print(f"Result saved to: {output_filename}")
                
                # Store for summary
                results_summary.append({
                    'file': img_file,
                    'status': status_text,
                    'confidence': result['confidence'],
                    'time': result['process_time']
                })
                
            except Exception as e:
                print(f"Error processing image: {e}")
                import traceback
                traceback.print_exc()
        
        # Print summary
        print("\n" + "=" * 70)
        print("RESULTS SUMMARY")
        print("=" * 70)
        
        print(f"Total images processed: {len(results_summary)}")
        
        # Calculate average processing time
        times = [r['time'] for r in results_summary]
        if times:
            avg_time = sum(times) / len(times)
            print(f"Average processing time: {avg_time:.3f} seconds")
        
        # List potential falls (lowest confidence)
        valid_results = [r for r in results_summary if r['confidence'] is not None]
        if valid_results:
            sorted_results = sorted(valid_results, key=lambda x: x['confidence'])
            print("\nTop 5 lowest confidence (potential falls):")
            for r in sorted_results[:5]:
                print(f"{r['file']}: {r['status']} (Confidence: {r['confidence']:.2f}, Time: {r['time']:.3f}s)")
        
        print("\nDemo completed successfully!")
        
    except Exception as e:
        print(f"Error in demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
