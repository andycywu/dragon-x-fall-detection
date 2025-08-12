import os
import sys
import cv2
import time
import numpy as np

def print_banner():
    print('==== Final Fall Detection Demo ====')
    print('Dragon X Fall Detection System')
    print('==================================')

def main():
    print_banner()
    print('Loading Fall Detector...')
    # Load the fall detector
    try:
        from fall_detector import FallDetector
        detector = FallDetector()
        print('Fall detector initialized successfully')
    except Exception as e:
        print('Error initializing Fall detector:', e)
        return

    # Process test images
    print('\nTesting with images...')
    test_dir = 'test_images'
    if os.path.exists(test_dir):
        img_files = [f for f in os.listdir(test_dir) if f.endswith('.jpg') or f.endswith('.png')]
        print(f'Found {len(img_files)} images')

        results_summary = []
        successful_count = 0

        for i, img_file in enumerate(img_files):
            image_path = os.path.join(test_dir, img_file)
            print(f'\nProcessing image {i+1}/{len(img_files)}: {image_path}')

            # Load image
            image = cv2.imread(image_path)
            if image is None:
                print('Failed to load image')
                continue

            # Make a copy for visualization
            display_image = image.copy()

            try:
                # Detect fall
                start_time = time.time()
                result = detector.detect_fall_from_frame(image)
                process_time = time.time() - start_time

                # Handle None result (no pose detected)
                if result is None:
                    print('No pose detected in image')
                    status = 'NO POSE DETECTED'
                    is_falling = False
                    confidence = 0.0
                    color = (0, 0, 255)
                else:
                    is_falling, confidence = result
                    status = 'FALL DETECTED!' if is_falling else 'No fall detected'
                    color = (0, 0, 255) if is_falling else (0, 255, 0)
                    successful_count += 1

                # Add text with detection results
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(display_image, status, (50, 50), font, 1, color, 2)
                if result is not None:
                    cv2.putText(display_image, f'Confidence: {confidence:.2f}', (50, 100), font, 1, color, 2)
                cv2.putText(display_image, f'Process time: {process_time:.3f}s', (50, 150), font, 1, (255, 255, 0), 2)

                # Save result image
                output_filename = f'result_{i+1}_{os.path.basename(image_path)}'
                cv2.imwrite(output_filename, display_image)

                # Print and store results
                if result is not None:
                    print(f'Result: {status}, Confidence: {confidence:.2f}')
                    results_summary.append({'file': img_file, 'status': status, 'confidence': confidence, 'time': process_time})
                else:
                    print(f'Result: {status}')
                    results_summary.append({'file': img_file, 'status': status, 'confidence': None, 'time': process_time})

                print(f'Processed in {process_time:.3f} seconds')
                print(f'Result saved to: {output_filename}')
            except Exception as e:
                print('Error during fall detection:', e)
                import traceback
                traceback.print_exc()

        # Print summary
        print('\n===== RESULTS SUMMARY =====')
        print(f'Total images: {len(img_files)}')
        print(f'Successfully processed: {successful_count}')
        print(f'Failed to process: {len(img_files) - successful_count}')

        if successful_count > 0:
            # Sort by confidence
            valid_results = [r for r in results_summary if r['confidence'] is not None]
            if valid_results:
                sorted_results = sorted(valid_results, key=lambda x: x['confidence'])
                print('\nTop 5 lowest confidence (potential falls):')
                for r in sorted_results[:5]:
                    print(f"{r['file']}: {r['status']} (Confidence: {r['confidence']:.2f}, Time: {r['time']:.3f}s)")
    else:
        print(f'Test directory {test_dir} not found')

    print('\nDemo completed!')

if __name__ == '__main__':
    main()
