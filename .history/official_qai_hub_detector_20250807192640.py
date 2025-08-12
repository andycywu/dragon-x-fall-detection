#!/usr/bin/env python3
"""
Official QAI Hub Detection System
按照Qualcomm AI Hub官方文檔實現的統一檢測系統
"""

import logging
import numpy as np
import cv2
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image
import torch

# QAI Hub imports (按照官方文檔導入)
from qai_hub_models.models.mediapipe_face.app import MediaPipeFaceApp
from qai_hub_models.models.mediapipe_face.model import MediaPipeFace
from qai_hub_models.models.mediapipe_pose.app import MediaPipePoseApp
from qai_hub_models.models.mediapipe_pose.model import MediaPipePose
from qai_hub_models.models.mediapipe_hand.app import MediaPipeHandApp
from qai_hub_models.models.mediapipe_hand.model import MediaPipeHand

logger = logging.getLogger(__name__)


class OfficialQAIHubDetector:
    """
    官方QAI Hub檢測系統
    完全按照Qualcomm AI Hub官方文檔和示例實現
    """
    
    def __init__(self):
        """初始化官方QAI Hub檢測系統"""
        logger.info("Initializing Official QAI Hub Detection System...")
        
        # 初始化應用程序 (按照官方demo方式)
        self.face_app = None
        self.pose_app = None
        self.hand_app = None
        
        # 初始化標誌
        self._face_initialized = False
        self._pose_initialized = False
        self._hand_initialized = False
        
        logger.info("Official QAI Hub Detection System initialized")
    
    def _init_face_detection(self):
        """初始化人臉檢測 (按照官方文檔)"""
        if self._face_initialized:
            return
            
        try:
            logger.info("Loading QAI Hub MediaPipe Face model...")
            # 按照官方demo.py方式載入
            face_model = MediaPipeFace.from_pretrained()
            self.face_app = MediaPipeFaceApp.from_pretrained(face_model)
            self._face_initialized = True
            logger.info("QAI Hub Face detection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize face detection: {e}")
            raise
    
    def _init_pose_detection(self):
        """初始化姿態檢測 (按照官方文檔)"""
        if self._pose_initialized:
            return
            
        try:
            logger.info("Loading QAI Hub MediaPipe Pose model...")
            # 按照官方demo.py方式載入
            pose_model = MediaPipePose.from_pretrained()
            self.pose_app = MediaPipePoseApp.from_pretrained(pose_model)
            self._pose_initialized = True
            logger.info("QAI Hub Pose detection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pose detection: {e}")
            raise
    
    def _init_hand_detection(self):
        """初始化手部檢測 (按照官方文檔)"""
        if self._hand_initialized:
            return
            
        try:
            logger.info("Loading QAI Hub MediaPipe Hand model...")
            # 按照官方demo.py方式載入
            hand_model = MediaPipeHand.from_pretrained()
            self.hand_app = MediaPipeHandApp.from_pretrained(hand_model)
            self._hand_initialized = True
            logger.info("QAI Hub Hand detection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize hand detection: {e}")
            raise
    
    def detect_faces(self, image: np.ndarray, raw_output: bool = False) -> Dict[str, Any]:
        """
        人臉檢測 (按照官方API)
        
        Args:
            image: RGB格式的numpy array (H, W, C)
            raw_output: 是否返回原始輸出
            
        Returns:
            包含檢測結果的字典
        """
        self._init_face_detection()
        
        try:
            # 按照官方文檔，predict_landmarks_from_image接受PIL Image或numpy array
            if raw_output:
                # 獲取原始輸出 (bounding boxes, keypoints, landmarks等)
                results = self.face_app.predict_landmarks_from_image(image, raw_output=True)
                batched_selected_boxes, batched_selected_keypoints, batched_roi_4corners, batched_selected_landmarks = results
                
                return {
                    'success': True,
                    'method': 'qai_hub_face_raw',
                    'bounding_boxes': batched_selected_boxes,
                    'keypoints': batched_selected_keypoints,
                    'roi_corners': batched_roi_4corners,
                    'landmarks': batched_selected_landmarks,
                    'num_faces': len(batched_selected_boxes[0]) if batched_selected_boxes and len(batched_selected_boxes) > 0 else 0
                }
            else:
                # 獲取帶標註的圖像
                annotated_images = self.face_app.predict_landmarks_from_image(image, raw_output=False)
                
                # 為了獲取檢測數據，我們也要調用raw_output版本
                raw_results = self.face_app.predict_landmarks_from_image(image, raw_output=True)
                batched_selected_boxes, batched_selected_keypoints, batched_roi_4corners, batched_selected_landmarks = raw_results
                
                return {
                    'success': True,
                    'method': 'qai_hub_face',
                    'annotated_image': annotated_images[0] if annotated_images else image,
                    'bounding_boxes': batched_selected_boxes,
                    'keypoints': batched_selected_keypoints,
                    'landmarks': batched_selected_landmarks,
                    'num_faces': len(batched_selected_boxes[0]) if batched_selected_boxes and len(batched_selected_boxes) > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return {
                'success': False,
                'method': 'qai_hub_face',
                'error': str(e),
                'num_faces': 0
            }
    
    def detect_pose(self, image: np.ndarray, raw_output: bool = False) -> Dict[str, Any]:
        """
        姿態檢測 (按照官方API)
        
        Args:
            image: RGB格式的numpy array (H, W, C)
            raw_output: 是否返回原始輸出
            
        Returns:
            包含檢測結果的字典
        """
        self._init_pose_detection()
        
        try:
            if raw_output:
                # 獲取原始輸出
                results = self.pose_app.predict_landmarks_from_image(image, raw_output=True)
                batched_selected_boxes, batched_selected_keypoints, batched_roi_4corners, batched_selected_landmarks = results
                
                return {
                    'success': True,
                    'method': 'qai_hub_pose_raw',
                    'bounding_boxes': batched_selected_boxes,
                    'keypoints': batched_selected_keypoints,
                    'roi_corners': batched_roi_4corners,
                    'landmarks': batched_selected_landmarks,
                    'num_poses': len(batched_selected_boxes[0]) if batched_selected_boxes and len(batched_selected_boxes) > 0 else 0
                }
            else:
                # 獲取帶標註的圖像
                annotated_images = self.pose_app.predict_landmarks_from_image(image, raw_output=False)
                
                # 獲取檢測數據
                raw_results = self.pose_app.predict_landmarks_from_image(image, raw_output=True)
                batched_selected_boxes, batched_selected_keypoints, batched_roi_4corners, batched_selected_landmarks = raw_results
                
                return {
                    'success': True,
                    'method': 'qai_hub_pose',
                    'annotated_image': annotated_images[0] if annotated_images else image,
                    'bounding_boxes': batched_selected_boxes,
                    'keypoints': batched_selected_keypoints,
                    'landmarks': batched_selected_landmarks,
                    'num_poses': len(batched_selected_boxes[0]) if batched_selected_boxes and len(batched_selected_boxes) > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Pose detection failed: {e}")
            return {
                'success': False,
                'method': 'qai_hub_pose',
                'error': str(e),
                'num_poses': 0
            }
    
    def detect_hands(self, image: np.ndarray, raw_output: bool = False) -> Dict[str, Any]:
        """
        手部檢測 (按照官方API)
        
        Args:
            image: RGB格式的numpy array (H, W, C)
            raw_output: 是否返回原始輸出
            
        Returns:
            包含檢測結果的字典
        """
        self._init_hand_detection()
        
        try:
            if raw_output:
                # 獲取原始輸出 (包含右手/左手信息)
                results = self.hand_app.predict_landmarks_from_image(image, raw_output=True)
                batched_selected_boxes, batched_selected_keypoints, batched_roi_4corners, batched_selected_landmarks, batched_is_right_hand = results
                
                return {
                    'success': True,
                    'method': 'qai_hub_hand_raw',
                    'bounding_boxes': batched_selected_boxes,
                    'keypoints': batched_selected_keypoints,
                    'roi_corners': batched_roi_4corners,
                    'landmarks': batched_selected_landmarks,
                    'is_right_hand': batched_is_right_hand,
                    'num_hands': len(batched_selected_boxes[0]) if batched_selected_boxes and len(batched_selected_boxes) > 0 else 0
                }
            else:
                # 獲取帶標註的圖像
                annotated_images = self.hand_app.predict_landmarks_from_image(image, raw_output=False)
                
                # 獲取檢測數據
                raw_results = self.hand_app.predict_landmarks_from_image(image, raw_output=True)
                batched_selected_boxes, batched_selected_keypoints, batched_roi_4corners, batched_selected_landmarks, batched_is_right_hand = raw_results
                
                return {
                    'success': True,
                    'method': 'qai_hub_hand',
                    'annotated_image': annotated_images[0] if annotated_images else image,
                    'bounding_boxes': batched_selected_boxes,
                    'keypoints': batched_selected_keypoints,
                    'landmarks': batched_selected_landmarks,
                    'is_right_hand': batched_is_right_hand,
                    'num_hands': len(batched_selected_boxes[0]) if batched_selected_boxes and len(batched_selected_boxes) > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Hand detection failed: {e}")
            return {
                'success': False,
                'method': 'qai_hub_hand',
                'error': str(e),
                'num_hands': 0
            }
    
    def unified_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """
        統一檢測：同時進行人臉、姿態和手部檢測
        
        Args:
            image: RGB格式的numpy array (H, W, C)
            
        Returns:
            包含所有檢測結果的字典
        """
        try:
            # 並行檢測所有項目
            face_results = self.detect_faces(image, raw_output=True)
            pose_results = self.detect_pose(image, raw_output=True)
            hand_results = self.detect_hands(image, raw_output=True)
            
            return {
                'success': True,
                'method': 'qai_hub_unified',
                'faces': face_results,
                'poses': pose_results,
                'hands': hand_results,
                'total_detections': {
                    'faces': face_results.get('num_faces', 0),
                    'poses': pose_results.get('num_poses', 0),
                    'hands': hand_results.get('num_hands', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Unified detection failed: {e}")
            return {
                'success': False,
                'method': 'qai_hub_unified',
                'error': str(e)
            }
    
    def get_face_landmarks_coordinates(self, detection_result: Dict[str, Any]) -> List[Tuple[int, int]]:
        """
        從檢測結果中提取人臉landmark座標
        
        Args:
            detection_result: detect_faces的返回結果
            
        Returns:
            人臉landmark座標列表 [(x, y), ...]
        """
        coordinates = []
        
        if not detection_result.get('success', False):
            return coordinates
        
        landmarks = detection_result.get('landmarks', [])
        if landmarks and len(landmarks) > 0:
            # landmarks是list[torch.Tensor]格式
            for landmark_batch in landmarks:
                if isinstance(landmark_batch, torch.Tensor) and landmark_batch.nelement() > 0:
                    # landmark_batch shape: [num_faces, num_landmark_points, 3] where 3 == (x, y, confidence)
                    for face_landmarks in landmark_batch:
                        face_coords = []
                        for point in face_landmarks:
                            if len(point) >= 2:
                                x, y = int(point[0].item()), int(point[1].item())
                                face_coords.append((x, y))
                        coordinates.extend(face_coords)
        
        return coordinates
    
    def get_pose_landmarks_coordinates(self, detection_result: Dict[str, Any]) -> List[Tuple[int, int]]:
        """
        從檢測結果中提取姿態landmark座標
        
        Args:
            detection_result: detect_pose的返回結果
            
        Returns:
            姿態landmark座標列表 [(x, y), ...]
        """
        coordinates = []
        
        if not detection_result.get('success', False):
            return coordinates
        
        landmarks = detection_result.get('landmarks', [])
        if landmarks and len(landmarks) > 0:
            for landmark_batch in landmarks:
                if isinstance(landmark_batch, torch.Tensor) and landmark_batch.nelement() > 0:
                    for pose_landmarks in landmark_batch:
                        pose_coords = []
                        for point in pose_landmarks:
                            if len(point) >= 2:
                                x, y = int(point[0].item()), int(point[1].item())
                                pose_coords.append((x, y))
                        coordinates.extend(pose_coords)
        
        return coordinates
    
    def save_annotated_result(self, image_result: np.ndarray, filename: str):
        """保存標註結果圖像"""
        try:
            if image_result is not None:
                # 轉換為PIL Image並保存
                pil_image = Image.fromarray(image_result)
                pil_image.save(filename)
                logger.info(f"Annotated result saved to {filename}")
            else:
                logger.warning("No image result to save")
        except Exception as e:
            logger.error(f"Failed to save result: {e}")


def demo_official_qai_hub_detection():
    """
    官方QAI Hub檢測系統演示
    """
    import os
    
    print("=== Official QAI Hub Detection Demo ===")
    
    # 初始化檢測器
    detector = OfficialQAIHubDetector()
    
    # 測試圖像路徑
    test_images = [
        'andy.jpg',
        'official_test_image.jpg',
        'enhanced_test_image.jpg'
    ]
    
    for image_path in test_images:
        if not os.path.exists(image_path):
            print(f"Skip {image_path} (not found)")
            continue
            
        print(f"\n--- Testing with {image_path} ---")
        
        # 載入圖像
        image = cv2.imread(image_path)
        if image is None:
            print(f"Failed to load {image_path}")
            continue
            
        # 轉換為RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 1. 人臉檢測
        print("1. Face Detection...")
        face_result = detector.detect_faces(image_rgb)
        print(f"   Faces detected: {face_result.get('num_faces', 0)}")
        
        if face_result.get('success') and 'annotated_image' in face_result:
            detector.save_annotated_result(
                face_result['annotated_image'], 
                f"official_qai_hub_face_{os.path.basename(image_path)}"
            )
        
        # 2. 姿態檢測
        print("2. Pose Detection...")
        pose_result = detector.detect_pose(image_rgb)
        print(f"   Poses detected: {pose_result.get('num_poses', 0)}")
        
        if pose_result.get('success') and 'annotated_image' in pose_result:
            detector.save_annotated_result(
                pose_result['annotated_image'], 
                f"official_qai_hub_pose_{os.path.basename(image_path)}"
            )
        
        # 3. 手部檢測
        print("3. Hand Detection...")
        hand_result = detector.detect_hands(image_rgb)
        print(f"   Hands detected: {hand_result.get('num_hands', 0)}")
        
        if hand_result.get('success') and 'annotated_image' in hand_result:
            detector.save_annotated_result(
                hand_result['annotated_image'], 
                f"official_qai_hub_hand_{os.path.basename(image_path)}"
            )
        
        # 4. 統一檢測
        print("4. Unified Detection...")
        unified_result = detector.unified_detection(image_rgb)
        if unified_result.get('success'):
            totals = unified_result['total_detections']
            print(f"   Total: {totals['faces']} faces, {totals['poses']} poses, {totals['hands']} hands")
        
        # 5. 提取座標
        if face_result.get('success'):
            face_coords = detector.get_face_landmarks_coordinates(face_result)
            print(f"   Face landmarks: {len(face_coords)} points")
        
        if pose_result.get('success'):
            pose_coords = detector.get_pose_landmarks_coordinates(pose_result)
            print(f"   Pose landmarks: {len(pose_coords)} points")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(level=logging.INFO)
    
    # 運行演示
    demo_official_qai_hub_detection()
