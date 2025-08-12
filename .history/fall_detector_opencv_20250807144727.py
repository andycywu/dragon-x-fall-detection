import cv2
import numpy as np
from typing import Tuple, Optional

class OpenCVFallDetector:
    """
    Fall detector using OpenCV's DNN pose estimation instead of MediaPipe.
    This works with any Python version and doesn't require MediaPipe.
    """
    def __init__(self):
        # We'll use a simple motion-based approach with OpenCV
        self.prev_frame = None
        self.motion_threshold = 5000  # Adjust based on testing
        
    def detect_fall_from_frame(self, frame: np.ndarray) -> Tuple[bool, Optional[float]]:
        """
        Detect fall using motion analysis and body position estimation.
        Returns: (fall_detected, confidence_score)
        """
        if frame is None:
            return False, None
            
        # Convert to grayscale for processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Initialize previous frame
        if self.prev_frame is None:
            self.prev_frame = gray
            return False, 0.0
        
        # Calculate frame difference
        frame_diff = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyze motion and body position
        total_motion = sum(cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 500)
        
        # Detect potential falls based on:
        # 1. Large motion areas (sudden movement)
        # 2. Horizontal orientation detection
        fall_detected = False
        confidence = 0.0
        
        if total_motion > self.motion_threshold:
            # Analyze largest contour for body orientation
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 1000:
                    # Fit ellipse to estimate body orientation
                    if len(largest_contour) >= 5:
                        ellipse = cv2.fitEllipse(largest_contour)
                        angle = ellipse[2]  # Rotation angle
                        
                        # Check if body is horizontal (fall position)
                        # Angle close to 0 or 180 indicates horizontal position
                        horizontal_angle = min(abs(angle), abs(angle - 180))
                        if horizontal_angle < 30:  # Body is horizontal
                            fall_detected = True
                            confidence = min(100.0, total_motion / 100)
        
        # Update previous frame
        self.prev_frame = gray.copy()
        
        return fall_detected, confidence
    
    def draw_motion_analysis(self, frame: np.ndarray) -> np.ndarray:
        """Draw motion analysis visualization on frame."""
        if self.prev_frame is None:
            return frame
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        frame_diff = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw motion contours
        for contour in contours:
            if cv2.contourArea(contour) > 500:
                cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
                
                # Draw bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                
                # Analyze aspect ratio for fall detection
                aspect_ratio = w / h if h > 0 else 0
                if aspect_ratio > 1.5:  # Wide rectangle suggests horizontal position
                    cv2.putText(frame, "POTENTIAL FALL", (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame

# Create a compatible fall detector class that matches the original interface
class FallDetector:
    """
    Fallback fall detector that works without MediaPipe.
    Uses OpenCV-based motion analysis instead of pose detection.
    """
    def __init__(self):
        self.opencv_detector = OpenCVFallDetector()
        print("⚠️  Using OpenCV fallback detector (MediaPipe not available)")
        
    def detect_fall_from_frame(self, frame: np.ndarray) -> Tuple[bool, Optional[float]]:
        """Detect fall from frame using OpenCV motion analysis."""
        return self.opencv_detector.detect_fall_from_frame(frame)
    
    def draw_pose_landmarks(self, frame: np.ndarray, landmarks=None) -> np.ndarray:
        """Draw motion analysis instead of pose landmarks."""
        return self.opencv_detector.draw_motion_analysis(frame)

def detect_fall_from_frame(frame: np.ndarray) -> Tuple[bool, Optional[float]]:
    """
    Legacy function for backward compatibility.
    """
    global _fall_detector
    if '_fall_detector' not in globals():
        _fall_detector = FallDetector()
    return _fall_detector.detect_fall_from_frame(frame)
