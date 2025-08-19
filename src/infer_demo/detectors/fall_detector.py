import cv2
import mediapipe as mp
import numpy as np
from typing import Tuple, Optional

class FallDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
    def calculate_angle(self, point1: np.ndarray, point2: np.ndarray, point3: np.ndarray) -> float:
        """Calculate angle between three points."""
        vector1 = point1 - point2
        vector2 = point3 - point2
        
        cosine_angle = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        angle = np.arccos(cosine_angle)
        return np.degrees(angle)
    
    def detect_fall_from_frame(self, frame: np.ndarray) -> Tuple[bool, Optional[float]]:
        """
        Detect fall from a single frame using pose analysis.
        Returns: (fall_detected, angle)
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        if not results.pose_landmarks:
            return False, None
            
        landmarks = results.pose_landmarks.landmark
        
        # Get key points: left/right shoulder, hip, knee
        left_shoulder = np.array([landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER].x,
                                 landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y])
        left_hip = np.array([landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].x,
                            landmarks[self.mp_pose.PoseLandmark.LEFT_HIP].y])
        left_knee = np.array([landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE].x,
                             landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE].y])
        
        right_shoulder = np.array([landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                                  landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y])
        right_hip = np.array([landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].x,
                             landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP].y])
        right_knee = np.array([landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE].x,
                              landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE].y])
        
        # Calculate torso angle (hip-shoulder-vertical)
        left_torso_angle = self.calculate_angle(left_hip, left_shoulder, 
                                               left_shoulder + np.array([0, 0.1]))
        right_torso_angle = self.calculate_angle(right_hip, right_shoulder, 
                                                right_shoulder + np.array([0, 0.1]))
        
        # Use average torso angle
        avg_torso_angle = (left_torso_angle + right_torso_angle) / 2
        
        # Fall detection: if torso is too horizontal (angle < 100 degrees from vertical)
        fall_detected = avg_torso_angle > 80  # More than 80 degrees from vertical indicates fall
        
        return fall_detected, avg_torso_angle
    
    def draw_pose_landmarks(self, frame: np.ndarray, landmarks) -> np.ndarray:
        """Draw pose landmarks on frame."""
        if landmarks:
            self.mp_drawing.draw_landmarks(
                frame, landmarks, self.mp_pose.POSE_CONNECTIONS)
        return frame

def detect_fall_from_frame(frame: np.ndarray) -> Tuple[bool, Optional[float]]:
    """
    Legacy function for backward compatibility.
    Detect fall from frame using global detector instance.
    """
    global _fall_detector
    if '_fall_detector' not in globals():
        _fall_detector = FallDetector()
    return _fall_detector.detect_fall_from_frame(frame)
