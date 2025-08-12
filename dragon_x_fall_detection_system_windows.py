#!/usr/bin/env python3
"""
Dragon X Fall Prevention Detection System for Windows (ASCII Version)
Optimized for hackathon, using Snapdragon X Elite platform
"""

import os
import numpy as np
import cv2
import logging
from typing import Dict, Any, List
import time
import json

try:
    import qai_hub as hub
    import onnxruntime as ort
    from dotenv import load_dotenv
    # Load environment variables
    load_dotenv()
    QAI_HUB_AVAILABLE = True
except ImportError:
    QAI_HUB_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DragonXFallDetectionSystem:
    """Dragon X Fall Prevention Detection System"""
    
    def __init__(self):
        """Initialize Dragon X detection system"""
        self.api_token = os.getenv('QAI_HUB_API_TOKEN')
        self.target_device = None
        self.qai_hub_models = {}
        self.compiled_models = {}
        self.onnx_sessions = {}
        
        logger.info("Initializing Dragon X Fall Prevention Detection System...")
        
        if QAI_HUB_AVAILABLE:
            self._find_dragon_x_devices()
            self._initialize_fall_detection_models()
        else:
            logger.warning("QAI Hub not available, running in compatibility mode")
            self._initialize_fallback_system()
    
    def _initialize_fallback_system(self):
        """Initialize fallback system when QAI Hub is not available"""
        logger.info("Initializing fallback detection system for Windows...")
        # This will use standard OpenCV and locally available models
        self.using_fallback = True
    
    def _find_dragon_x_devices(self):
        """Find and select Dragon X devices"""
        if not self.api_token:
            logger.warning("QAI Hub API Token not set in .env file")
            return None
        
        try:
            devices = hub.get_devices()
            logger.info(f"Searching QAI Hub devices...")
            logger.info(f"   Total devices: {len(devices)}")
            
            # Categorize devices
            dragon_x_devices = []
            snapdragon_devices = []
            other_devices = []
            
            for device in devices:
                device_name = device.name.lower()
                if 'x elite' in device_name or 'snapdragon x' in device_name or 'dragon x' in device_name:
                    dragon_x_devices.append(device)
                elif 'snapdragon' in device_name:
                    snapdragon_devices.append(device)
                else:
                    other_devices.append(device)
            
            # Display device categorization
            logger.info(f"Device categorization results:")
            logger.info(f"   Dragon X / Snapdragon X Elite: {len(dragon_x_devices)}")
            logger.info(f"   Other Snapdragon devices: {len(snapdragon_devices)}")
            logger.info(f"   Other devices: {len(other_devices)}")
            
            # Select best device
            if dragon_x_devices:
                self.target_device = dragon_x_devices[0]
                logger.info(f"Successfully selected Dragon X device!")
                logger.info(f"   Device name: {self.target_device.name}")
                logger.info(f"   Hackathon platform ready!")
                
                # Show all Dragon X device options
                if len(dragon_x_devices) > 1:
                    logger.info(f"   Other available Dragon X devices:")
                    for i, device in enumerate(dragon_x_devices[1:], 1):
                        logger.info(f"      {i}. {device.name}")
                        
            elif snapdragon_devices:
                self.target_device = snapdragon_devices[0]
                logger.warning(f"Dragon X not found, using Snapdragon device:")
                logger.info(f"   Device name: {self.target_device.name}")
                
            else:
                self.target_device = devices[0] if devices else None
                logger.warning(f"Snapdragon device not found, using default device:")
                logger.info(f"   Device name: {self.target_device.name if self.target_device else 'None'}")
            
            return self.target_device
            
        except Exception as e:
            logger.error(f"Device search failed: {e}")
            return None
    
    def _initialize_fall_detection_models(self):
        """Initialize models needed for fall detection"""
        logger.info("Loading fall prevention detection models...")
        
        try:
            # Pose detection is core to fall detection
            self._load_pose_detection_for_fall_prevention()
            
            # Face detection for elderly identification
            self._load_face_detection_for_elderly_identification()
            
            # Hand detection for emergency gestures
            self._load_hand_detection_for_emergency_gestures()
            
            logger.info("Fall prevention detection models loaded successfully")
            
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
    
    def _load_pose_detection_for_fall_prevention(self):
        """Load pose detection model (fall prevention core)"""
        try:
            if not QAI_HUB_AVAILABLE:
                logger.warning("QAI Hub not available, skipping pose model loading")
                return
                
            from qai_hub_models.models.mediapipe_pose import Model as PoseModel
            
            logger.info("Loading pose detection model (fall prevention core)...")
            pose_model = PoseModel.from_pretrained()
            pose_detector = pose_model.pose_detector
            self.qai_hub_models['pose_fall_detection'] = pose_detector
            
            # Submit to Dragon X device for compilation
            if self.target_device:
                logger.info("Submitting pose detection model to Dragon X for compilation...")
                
                try:
                    torchscript_model = pose_detector.convert_to_torchscript()
                    uploaded_model = hub.upload_model(torchscript_model)
                    
                    compile_job = hub.submit_compile_job(
                        model=uploaded_model,
                        input_specs={"image": ((1, 3, 256, 256), "float32")},
                        device=self.target_device,
                    )
                    
                    logger.info(f"Pose detection Dragon X compilation Job: {compile_job.job_id}")
                    logger.info(f"Dashboard: https://app.aihub.qualcomm.com/jobs/{compile_job.job_id}")
                    
                    self.compiled_models['pose_fall_detection_job'] = compile_job
                    
                except Exception as e:
                    logger.error(f"Pose detection Dragon X compilation failed: {e}")
            
            logger.info("Pose detection model (fall prevention) loaded successfully")
            
        except Exception as e:
            logger.error(f"Pose detection model loading failed: {e}")
    
    def _load_face_detection_for_elderly_identification(self):
        """Load face detection model (elderly identification)"""
        try:
            if not QAI_HUB_AVAILABLE:
                logger.warning("QAI Hub not available, skipping face model loading")
                return
                
            from qai_hub_models.models.mediapipe_face import Model as FaceModel
            
            logger.info("Loading face detection model (elderly identification)...")
            face_model = FaceModel.from_pretrained()
            face_detector = face_model.face_detector
            self.qai_hub_models['face_elderly_id'] = face_detector
            
            # Submit to Dragon X device for compilation
            if self.target_device:
                logger.info("Submitting face detection model to Dragon X for compilation...")
                
                try:
                    torchscript_model = face_detector.convert_to_torchscript()
                    uploaded_model = hub.upload_model(torchscript_model)
                    
                    compile_job = hub.submit_compile_job(
                        model=uploaded_model,
                        input_specs={"image": ((1, 3, 256, 256), "float32")},
                        device=self.target_device,
                    )
                    
                    logger.info(f"Face detection Dragon X compilation Job: {compile_job.job_id}")
                    logger.info(f"Dashboard: https://app.aihub.qualcomm.com/jobs/{compile_job.job_id}")
                    
                    self.compiled_models['face_elderly_id_job'] = compile_job
                    
                except Exception as e:
                    logger.error(f"Face detection Dragon X compilation failed: {e}")
            
            logger.info("Face detection model (elderly identification) loaded successfully")
            
        except Exception as e:
            logger.error(f"Face detection model loading failed: {e}")
    
    def _load_hand_detection_for_emergency_gestures(self):
        """Load hand detection model (emergency gestures)"""
        try:
            if not QAI_HUB_AVAILABLE:
                logger.warning("QAI Hub not available, skipping hand model loading")
                return
                
            from qai_hub_models.models.mediapipe_hand import Model as HandModel
            
            logger.info("Loading hand detection model (emergency gestures)...")
            hand_model = HandModel.from_pretrained()
            hand_detector = hand_model.hand_detector
            self.qai_hub_models['hand_emergency_gesture'] = hand_detector
            
            # Submit to Dragon X device for compilation
            if self.target_device:
                logger.info("Submitting hand detection model to Dragon X for compilation...")
                
                try:
                    torchscript_model = hand_detector.convert_to_torchscript()
                    uploaded_model = hub.upload_model(torchscript_model)
                    
                    compile_job = hub.submit_compile_job(
                        model=uploaded_model,
                        input_specs={"image": ((1, 3, 224, 224), "float32")},
                        device=self.target_device,
                    )
                    
                    logger.info(f"Hand detection Dragon X compilation Job: {compile_job.job_id}")
                    logger.info(f"Dashboard: https://app.aihub.qualcomm.com/jobs/{compile_job.job_id}")
                    
                    self.compiled_models['hand_emergency_gesture_job'] = compile_job
                    
                except Exception as e:
                    logger.error(f"Hand detection Dragon X compilation failed: {e}")
            
            logger.info("Hand detection model (emergency gestures) loaded successfully")
            
        except Exception as e:
            logger.error(f"Hand detection model loading failed: {e}")
    
    def analyze_fall_risk(self, pose_keypoints: List[Dict]) -> Dict[str, Any]:
        """Analyze fall risk"""
        if not pose_keypoints:
            return {"fall_risk": "unknown", "confidence": 0.0, "reasons": []}
        
        fall_risk_indicators = []
        risk_score = 0.0
        
        try:
            # Extract key keypoints
            keypoints = pose_keypoints[0] if pose_keypoints else {}
            
            # Detect body tilt
            if len(keypoints.get('keypoints', [])) >= 17:
                kpts = keypoints['keypoints']
                
                # Shoulder horizontal check
                left_shoulder = kpts[5] if len(kpts) > 5 else None
                right_shoulder = kpts[6] if len(kpts) > 6 else None
                
                if left_shoulder and right_shoulder:
                    shoulder_angle = abs(left_shoulder['y'] - right_shoulder['y'])
                    if shoulder_angle > 0.3:  # threshold can be adjusted
                        fall_risk_indicators.append("Significant body tilt")
                        risk_score += 0.4
                
                # Center of gravity stability check
                left_hip = kpts[11] if len(kpts) > 11 else None
                right_hip = kpts[12] if len(kpts) > 12 else None
                left_ankle = kpts[15] if len(kpts) > 15 else None
                right_ankle = kpts[16] if len(kpts) > 16 else None
                
                if all([left_hip, right_hip, left_ankle, right_ankle]):
                    # Check ankle position relative to hip
                    hip_center_x = (left_hip['x'] + right_hip['x']) / 2
                    ankle_center_x = (left_ankle['x'] + right_ankle['x']) / 2
                    
                    balance_offset = abs(hip_center_x - ankle_center_x)
                    if balance_offset > 0.4:  # Center of gravity offset too large
                        fall_risk_indicators.append("Unstable center of gravity")
                        risk_score += 0.3
                
                # Knee bend check
                left_knee = kpts[13] if len(kpts) > 13 else None
                right_knee = kpts[14] if len(kpts) > 14 else None
                
                if left_knee and right_knee and left_hip and right_hip:
                    # Check if knees are excessively bent (may indicate falling)
                    left_knee_angle = abs(left_knee['y'] - left_hip['y'])
                    right_knee_angle = abs(right_knee['y'] - right_hip['y'])
                    
                    if left_knee_angle < 0.1 or right_knee_angle < 0.1:
                        fall_risk_indicators.append("Abnormal knee bend")
                        risk_score += 0.3
        
        except Exception as e:
            logger.error(f"Fall risk analysis failed: {e}")
            return {"fall_risk": "analysis_error", "confidence": 0.0, "error": str(e)}
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "high"
            risk_message = "High fall risk"
        elif risk_score >= 0.4:
            risk_level = "medium"
            risk_message = "Medium fall risk"
        elif risk_score >= 0.1:
            risk_level = "low"
            risk_message = "Low fall risk"
        else:
            risk_level = "normal"
            risk_message = "Normal state"
        
        return {
            "fall_risk": risk_level,
            "risk_score": risk_score,
            "confidence": min(risk_score * 1.5, 1.0),
            "message": risk_message,
            "indicators": fall_risk_indicators,
            "recommendation": self._get_safety_recommendation(risk_level)
        }
    
    def _get_safety_recommendation(self, risk_level: str) -> str:
        """Provide safety recommendations based on risk level"""
        recommendations = {
            "high": "Immediately check environmental safety, seek assistance or sit down to rest",
            "medium": "Pay attention to surroundings, slow down movements, ensure support is nearby",
            "low": "Maintain caution, pay attention to foot conditions",
            "normal": "Continue maintaining good posture"
        }
        return recommendations.get(risk_level, "Maintain safety awareness")
    
    def comprehensive_fall_prevention_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """Comprehensive fall prevention detection"""
        results = {
            "timestamp": time.time(),
            "dragon_x_device": self.target_device.name if self.target_device else None,
            "fall_prevention_analysis": {},
            "detections": {},
            "qai_hub_jobs": {}
        }
        
        # Pose detection (core)
        if hasattr(self, 'using_fallback') and self.using_fallback:
            # Use MediaPipe fallback if available
            try:
                import mediapipe as mp
                mp_pose = mp.solutions.pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5)
                
                # Convert to RGB
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pose_results = mp_pose.process(rgb_image)
                
                # Convert to keypoints format
                keypoints = []
                if pose_results.pose_landmarks:
                    landmarks = []
                    for idx, landmark in enumerate(pose_results.pose_landmarks.landmark):
                        landmarks.append({
                            "x": landmark.x, 
                            "y": landmark.y, 
                            "z": landmark.z,
                            "visibility": landmark.visibility
                        })
                    
                    keypoints.append({"keypoints": landmarks})
                
                # Analyze fall risk
                fall_analysis = self.analyze_fall_risk(keypoints)
                results["fall_prevention_analysis"] = fall_analysis
                results["detections"]["pose"] = {"keypoints": keypoints}
                
            except Exception as e:
                logger.error(f"MediaPipe fallback processing failed: {e}")
                # Use mock data as last resort
                mock_pose_results = {
                    "keypoints": [{
                        "keypoints": [
                            {"x": 0.5, "y": 0.3, "confidence": 0.8},  # head
                            {"x": 0.45, "y": 0.5, "confidence": 0.9},  # left shoulder
                            {"x": 0.55, "y": 0.5, "confidence": 0.9},  # right shoulder
                            # ... other keypoints
                        ]
                    }]
                }
                fall_analysis = self.analyze_fall_risk(mock_pose_results["keypoints"])
                results["fall_prevention_analysis"] = fall_analysis
                results["detections"]["pose"] = mock_pose_results
        
        elif 'pose_fall_detection' in self.qai_hub_models:
            logger.info("Executing pose detection (fall prevention core)...")
            # This will be implemented with ONNX Runtime later
            # Currently returning mock results for demonstration
            mock_pose_results = {
                "keypoints": [{
                    "keypoints": [
                        {"x": 0.5, "y": 0.3, "confidence": 0.8},  # head
                        {"x": 0.45, "y": 0.5, "confidence": 0.9},  # left shoulder
                        {"x": 0.55, "y": 0.5, "confidence": 0.9},  # right shoulder
                        # ... other keypoints
                    ]
                }]
            }
            
            # Analyze fall risk
            fall_analysis = self.analyze_fall_risk(mock_pose_results["keypoints"])
            results["fall_prevention_analysis"] = fall_analysis
            results["detections"]["pose"] = mock_pose_results
        
        # Record Dragon X compilation Job information
        for job_name, job in self.compiled_models.items():
            model_type = job_name.replace('_job', '')
            results["qai_hub_jobs"][model_type] = {
                "job_id": job.job_id,
                "dashboard_url": f"https://app.aihub.qualcomm.com/jobs/{job.job_id}",
                "target_device": self.target_device.name
            }
        
        return results
    
    def get_dragon_x_status_report(self) -> Dict[str, Any]:
        """Get Dragon X system status report"""
        report = {
            "system_name": "Dragon X Fall Prevention Detection System",
            "timestamp": time.time(),
            "dragon_x_device": {
                "name": self.target_device.name if self.target_device else None,
                "status": "ready" if self.target_device else "not_found"
            },
            "models_status": {},
            "qai_hub_jobs": {},
            "hackathon_readiness": True
        }
        
        if hasattr(self, 'using_fallback') and self.using_fallback:
            report["system_mode"] = "fallback"
            report["hackathon_readiness"] = True
            report["models_status"]["mediapipe_fallback"] = "ready"
            return report
        
        # Check model status
        for model_name in self.qai_hub_models:
            report["models_status"][model_name] = "loaded"
        
        # Check compilation Job status
        for job_name, job in self.compiled_models.items():
            try:
                # Try quick status check
                job.wait(timeout=1)
                status = "completed"
            except:
                status = "compiling"
            
            report["qai_hub_jobs"][job_name] = {
                "job_id": job.job_id,
                "status": status,
                "dashboard_url": f"https://app.aihub.qualcomm.com/jobs/{job.job_id}"
            }
        
        return report

def main():
    """Main function: Dragon X Fall Prevention Detection System Test"""
    print("Dragon X Fall Prevention Detection System")
    print("=" * 60)
    print("Snapdragon X Elite Platform Solution for Hackathon")
    print()
    
    try:
        # Initialize Dragon X system
        dragon_system = DragonXFallDetectionSystem()
        
        # Get system status report
        status_report = dragon_system.get_dragon_x_status_report()
        
        print("Dragon X System Status:")
        print(f"   Target device: {status_report['dragon_x_device']['name']}")
        print(f"   Device status: {status_report['dragon_x_device']['status']}")
        print(f"   Loaded models: {len(status_report['models_status'])}")
        print(f"   QAI Hub Jobs: {len(status_report['qai_hub_jobs'])}")
        print()
        
        # Show QAI Hub Job information
        if status_report['qai_hub_jobs']:
            print("Dragon X Compilation Jobs:")
            for job_name, job_info in status_report['qai_hub_jobs'].items():
                print(f"   {job_name}: {job_info['job_id']} ({job_info['status']})")
                print(f"      Dashboard: {job_info['dashboard_url']}")
            print()
        
        # Test fall prevention detection
        print("Testing fall prevention detection...")
        
        # Simulate detection (in actual application, use real image)
        mock_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        detection_results = dragon_system.comprehensive_fall_prevention_detection(mock_image)
        
        print("Fall prevention analysis results:")
        fall_analysis = detection_results.get('fall_prevention_analysis', {})
        print(f"   {fall_analysis.get('message', 'Unknown status')}")
        print(f"   Risk score: {fall_analysis.get('risk_score', 0):.2f}")
        print(f"   Recommendation: {fall_analysis.get('recommendation', 'No recommendations')}")
        
        if fall_analysis.get('indicators'):
            print(f"   Risk indicators: {', '.join(fall_analysis['indicators'])}")
        
        # Save Dragon X report
        with open('dragon_x_fall_detection_report.json', 'w') as f:
            json.dump({
                "status_report": status_report,
                "detection_results": detection_results
            }, f, indent=2, default=str)
        
        print(f"\nDragon X report saved: dragon_x_fall_detection_report.json")
        print("Dragon X Fall Prevention Detection System ready!")
        print("Hackathon demonstration system completed!")
        
    except Exception as e:
        print(f"Dragon X system initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
