#!/usr/bin/env python3
"""
AWS Virtual Camera RFC Adapter for Snapdragon X Elite
Provides a unified interface for accessing AWS Virtual Camera RFC
"""

import cv2
import logging
import os
import time
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSVirtualCameraRFC:
    """AWS Virtual Camera RFC implementation for Snapdragon X Elite"""
    
    def __init__(self, camera_id=0, resolution=None):
        """Initialize the AWS Virtual Camera RFC adapter
        
        Args:
            camera_id (int): Camera ID to use (default: 0)
            resolution (tuple): Optional resolution as (width, height)
        """
        self.camera_id = camera_id
        self.resolution = resolution
        self.camera = None
        self.is_open = False
        self.frame_count = 0
        self.start_time = None
        
        logger.info(f"Initializing AWS Virtual Camera RFC with camera ID {camera_id}")
        
    def open(self):
        """Open the camera connection"""
        try:
            # Try to open the camera using OpenCV
            self.camera = cv2.VideoCapture(self.camera_id)
            
            if not self.camera.isOpened():
                logger.error(f"Failed to open AWS Virtual Camera RFC with ID {self.camera_id}")
                return False
            
            # Set resolution if specified
            if self.resolution:
                width, height = self.resolution
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Get actual camera properties
            self.width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"AWS Virtual Camera RFC opened with resolution {self.width}x{self.height}, {self.fps} FPS")
            
            self.is_open = True
            self.frame_count = 0
            self.start_time = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening AWS Virtual Camera RFC: {e}")
            return False
    
    def read_frame(self):
        """Read a frame from the camera
        
        Returns:
            tuple: (success, frame) where success is a boolean indicating if the frame was read successfully,
                  and frame is the image data if successful, None otherwise
        """
        if not self.is_open:
            logger.warning("Attempt to read from closed camera")
            return False, None
        
        try:
            success, frame = self.camera.read()
            
            if success:
                self.frame_count += 1
                
                # Add frame metadata
                # This would be where we would add AWS RFC-specific metadata
                
                return True, frame
            else:
                logger.warning("Failed to read frame from AWS Virtual Camera RFC")
                return False, None
                
        except Exception as e:
            logger.error(f"Error reading from AWS Virtual Camera RFC: {e}")
            return False, None
    
    def get_properties(self):
        """Get camera properties
        
        Returns:
            dict: Camera properties including resolution, FPS, and frame count
        """
        if not self.is_open:
            return {}
        
        current_time = time.time()
        elapsed_time = current_time - self.start_time if self.start_time else 0
        actual_fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0
        
        return {
            'width': self.width,
            'height': self.height,
            'nominal_fps': self.fps,
            'actual_fps': actual_fps,
            'frame_count': self.frame_count,
            'uptime': elapsed_time
        }
    
    def set_property(self, property_name, value):
        """Set a camera property
        
        Args:
            property_name (str): Name of the property to set
            value: Value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_open:
            logger.warning("Attempt to set property on closed camera")
            return False
        
        try:
            # Map property names to OpenCV properties
            property_map = {
                'width': cv2.CAP_PROP_FRAME_WIDTH,
                'height': cv2.CAP_PROP_FRAME_HEIGHT,
                'fps': cv2.CAP_PROP_FPS,
                'brightness': cv2.CAP_PROP_BRIGHTNESS,
                'contrast': cv2.CAP_PROP_CONTRAST,
                'saturation': cv2.CAP_PROP_SATURATION,
                'hue': cv2.CAP_PROP_HUE,
                'gain': cv2.CAP_PROP_GAIN,
                'exposure': cv2.CAP_PROP_EXPOSURE,
            }
            
            if property_name in property_map:
                cv_property = property_map[property_name]
                result = self.camera.set(cv_property, value)
                
                if result:
                    # Update internal properties if needed
                    if property_name == 'width':
                        self.width = value
                    elif property_name == 'height':
                        self.height = value
                    elif property_name == 'fps':
                        self.fps = value
                
                return result
            else:
                logger.warning(f"Unknown property: {property_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting property {property_name}: {e}")
            return False
    
    def close(self):
        """Close the camera connection"""
        if self.is_open and self.camera is not None:
            self.camera.release()
            self.is_open = False
            logger.info("AWS Virtual Camera RFC closed")

def list_available_cameras(max_cameras=10):
    """List all available AWS Virtual Camera RFC devices
    
    Args:
        max_cameras (int): Maximum number of cameras to check
        
    Returns:
        list: List of available camera indices
    """
    available_cameras = []
    
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            available_cameras.append({
                'id': i,
                'width': width,
                'height': height,
                'fps': fps
            })
            
            cap.release()
    
    return available_cameras
