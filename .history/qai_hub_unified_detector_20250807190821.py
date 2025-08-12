#!/usr/bin/env python3
"""
🚀 QAI Hub 統一檢測系統
使用Qualcomm AI Hub優化的模型進行人臉檢測、姿態檢測等
"""

import cv2
import numpy as np
import time
import os
from typing import Dict, List, Tuple, Any, Optional
import logging
from PIL import Image

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QAIHubUnifiedDetector:
    """QAI Hub統一檢測系統"""
    
    def __init__(self):
        """初始化QAI Hub檢測器"""
        self.face_detector = None
        self.pose_detector = None
        self.selfie_detector = None
        
        logger.info("🚀 初始化 QAI Hub 統一檢測系統...")
        self._init_face_detection()
        self._init_pose_detection()
        self._init_selfie_detection()
        logger.info("✅ QAI Hub 統一檢測系統初始化完成")
    
    def _init_face_detection(self):
        """初始化QAI Hub人臉檢測"""
        try:
            from qai_hub_models.models.mediapipe_face.app import MediaPipeFaceApp
            from qai_hub_models.models.mediapipe_face.model import MediaPipeFace
            
            face_model = MediaPipeFace.from_pretrained()
            self.face_detector = MediaPipeFaceApp.from_pretrained(face_model)
            logger.info("✅ QAI Hub MediaPipe Face 檢測器初始化成功")
        except Exception as e:
            logger.error(f"❌ QAI Hub 人臉檢測器初始化失敗: {e}")
    
    def _init_pose_detection(self):
        """初始化QAI Hub姿態檢測"""
        try:
            from qai_hub_models.models.mediapipe_pose.app import MediaPipePoseApp
            from qai_hub_models.models.mediapipe_pose.model import MediaPipePose
            
            pose_model = MediaPipePose.from_pretrained()
            self.pose_detector = MediaPipePoseApp.from_pretrained(pose_model)
            logger.info("✅ QAI Hub MediaPipe Pose 檢測器初始化成功")
        except Exception as e:
            logger.error(f"❌ QAI Hub 姿態檢測器初始化失敗: {e}")
    
    def _init_selfie_detection(self):
        """初始化QAI Hub Selfie檢測（人像分割）"""
        try:
            from qai_hub_models.models.mediapipe_selfie.app import MediaPipeSelfieApp
            from qai_hub_models.models.mediapipe_selfie.model import MediaPipeSelfie
            
            selfie_model = MediaPipeSelfie.from_pretrained()
            self.selfie_detector = MediaPipeSelfieApp.from_pretrained(selfie_model)
            logger.info("✅ QAI Hub MediaPipe Selfie 檢測器初始化成功")
        except Exception as e:
            logger.error(f"❌ QAI Hub Selfie 檢測器初始化失敗: {e}")
    
    def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """使用QAI Hub檢測人臉"""
        if self.face_detector is None:
            return []
        
        try:
            # 轉換為RGB PIL圖像
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # 使用QAI Hub檢測人臉
            result = self.face_detector.predict_landmarks_from_image(pil_image)
            
            faces = []
            if result and len(result) > 0:
                # 解析人臉檢測結果
                face_landmarks = result[0] if isinstance(result, list) else result
                
                if hasattr(face_landmarks, 'landmark') and face_landmarks.landmark:
                    # 計算人臉邊界框
                    landmarks = face_landmarks.landmark
                    h, w = image.shape[:2]
                    
                    x_coords = [int(lm.x * w) for lm in landmarks]
                    y_coords = [int(lm.y * h) for lm in landmarks]
                    
                    if x_coords and y_coords:
                        x_min, x_max = min(x_coords), max(x_coords)
                        y_min, y_max = min(y_coords), max(y_coords)
                        
                        # 添加邊距
                        margin = 20
                        x_min = max(0, x_min - margin)
                        y_min = max(0, y_min - margin)
                        x_max = min(w, x_max + margin)
                        y_max = min(h, y_max + margin)
                        
                        faces.append({
                            'bbox': [x_min, y_min, x_max - x_min, y_max - y_min],
                            'landmarks': [(int(lm.x * w), int(lm.y * h)) for lm in landmarks],
                            'confidence': 0.95  # QAI Hub通常有很高的置信度
                        })
            
            return faces
            
        except Exception as e:
            logger.error(f"❌ QAI Hub 人臉檢測失敗: {e}")
            return []
    
    def detect_pose(self, image: np.ndarray) -> Dict[str, Any]:
        """使用QAI Hub檢測姿態"""
        if self.pose_detector is None:
            return {'success': False, 'landmarks': [], 'info': 'QAI Hub姿態檢測器未初始化'}
        
        try:
            # 轉換為RGB PIL圖像
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # 使用QAI Hub檢測姿態
            result = self.pose_detector.predict_landmarks_from_image(pil_image, raw_output=True)
            
            if result and len(result) >= 4:
                # 解析姿態檢測結果
                pose_landmarks = result[0]
                
                landmarks = []
                h, w = image.shape[:2]
                
                if hasattr(pose_landmarks, 'landmark') and pose_landmarks.landmark:
                    for lm in pose_landmarks.landmark:
                        landmarks.append((float(lm.x * w), float(lm.y * h)))
                
                return {
                    'success': True,
                    'landmarks': landmarks,
                    'info': f'QAI Hub檢測到 {len(landmarks)} 個姿態關鍵點'
                }
            else:
                return {'success': False, 'landmarks': [], 'info': 'QAI Hub未檢測到姿態'}
            
        except Exception as e:
            logger.error(f"❌ QAI Hub 姿態檢測失敗: {e}")
            return {'success': False, 'landmarks': [], 'info': str(e)}
    
    def detect_person_segmentation(self, image: np.ndarray) -> Dict[str, Any]:
        """使用QAI Hub進行人像分割"""
        if self.selfie_detector is None:
            return {'success': False, 'mask': None, 'info': 'QAI Hub Selfie檢測器未初始化'}
        
        try:
            # 轉換為RGB PIL圖像
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # 使用QAI Hub進行人像分割
            result = self.selfie_detector.predict_mask_from_image(pil_image)
            
            if result is not None:
                # 轉換分割掩碼
                if hasattr(result, 'numpy'):
                    mask = result.numpy()
                else:
                    mask = np.array(result)
                
                return {
                    'success': True,
                    'mask': mask,
                    'info': f'QAI Hub人像分割成功，掩碼尺寸: {mask.shape}'
                }
            else:
                return {'success': False, 'mask': None, 'info': 'QAI Hub人像分割失敗'}
            
        except Exception as e:
            logger.error(f"❌ QAI Hub 人像分割失敗: {e}")
            return {'success': False, 'mask': None, 'info': str(e)}
    
    def unified_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """統一檢測：人臉、姿態、人像分割"""
        results = {
            'timestamp': time.time(),
            'faces': [],
            'pose': {'success': False, 'landmarks': []},
            'segmentation': {'success': False, 'mask': None},
            'summary': {}
        }
        
        # 1. 人臉檢測
        start_time = time.time()
        faces = self.detect_faces(image)
        face_time = time.time() - start_time
        results['faces'] = faces
        
        # 2. 姿態檢測
        start_time = time.time()
        pose_result = self.detect_pose(image)
        pose_time = time.time() - start_time
        results['pose'] = pose_result
        
        # 3. 人像分割
        start_time = time.time()
        seg_result = self.detect_person_segmentation(image)
        seg_time = time.time() - start_time
        results['segmentation'] = seg_result
        
        # 生成摘要
        results['summary'] = {
            'faces_detected': len(faces),
            'pose_detected': pose_result['success'],
            'person_segmented': seg_result['success'],
            'processing_time': {
                'face_detection': face_time,
                'pose_detection': pose_time,
                'segmentation': seg_time,
                'total': face_time + pose_time + seg_time
            }
        }
        
        return results
    
    def extract_face_encoding(self, image: np.ndarray, face_bbox: List[int]) -> Optional[np.ndarray]:
        """從檢測到的人臉提取特徵編碼（用於人臉識別）"""
        try:
            # 提取人臉區域
            x, y, w, h = face_bbox
            face_image = image[y:y+h, x:x+w]
            
            if face_image.size == 0:
                return None
            
            # 使用QAI Hub人臉檢測獲取更詳細的特徵
            faces = self.detect_faces(face_image)
            
            if faces and len(faces) > 0:
                # 將人臉landmarks轉換為特徵向量
                landmarks = faces[0].get('landmarks', [])
                if len(landmarks) > 0:
                    # 簡化的特徵編碼（基於關鍵點距離和角度）
                    encoding = self._landmarks_to_encoding(landmarks)
                    return encoding
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 人臉編碼提取失敗: {e}")
            return None
    
    def _landmarks_to_encoding(self, landmarks: List[Tuple[int, int]]) -> np.ndarray:
        """將人臉關鍵點轉換為特徵編碼"""
        try:
            # 計算關鍵點之間的距離和角度作為特徵
            features = []
            
            if len(landmarks) >= 5:  # 至少需要5個關鍵點
                # 計算眼睛、鼻子、嘴巴之間的距離
                for i in range(len(landmarks)):
                    for j in range(i+1, min(i+10, len(landmarks))):  # 只計算附近的點
                        p1, p2 = landmarks[i], landmarks[j]
                        dist = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                        features.append(dist)
                
                # 正規化特徵
                features = np.array(features)
                if len(features) > 0:
                    features = features / np.linalg.norm(features)
                
                # 填充或截斷到固定長度（128維，類似face_recognition）
                target_size = 128
                if len(features) < target_size:
                    # 填充0
                    encoding = np.zeros(target_size)
                    encoding[:len(features)] = features
                else:
                    # 截斷
                    encoding = features[:target_size]
                
                return encoding
            
            # 如果關鍵點不足，返回零向量
            return np.zeros(128)
            
        except Exception as e:
            logger.error(f"❌ 關鍵點特徵編碼失敗: {e}")
            return np.zeros(128)

def demo_qai_hub_detection():
    """演示QAI Hub統一檢測"""
    print("🚀 QAI Hub 統一檢測演示")
    print("=" * 60)
    
    # 初始化檢測器
    detector = QAIHubUnifiedDetector()
    
    # 測試圖像檢測
    test_images = ["andy.jpg", "official_test_image.jpg"]
    
    for img_path in test_images:
        if os.path.exists(img_path):
            print(f"\n📷 測試圖像: {img_path}")
            
            # 載入圖像
            image = cv2.imread(img_path)
            if image is None:
                print(f"❌ 無法載入圖像: {img_path}")
                continue
            
            # 統一檢測
            results = detector.unified_detection(image)
            
            # 顯示結果
            print(f"  👤 檢測到人臉: {results['summary']['faces_detected']} 個")
            print(f"  🤸‍♀️ 姿態檢測: {'✅' if results['summary']['pose_detected'] else '❌'}")
            print(f"  🎭 人像分割: {'✅' if results['summary']['person_segmented'] else '❌'}")
            print(f"  ⏱️ 總處理時間: {results['summary']['processing_time']['total']:.3f}秒")
            
            # 可視化結果
            display_image = image.copy()
            
            # 繪製人臉框
            for face in results['faces']:
                x, y, w, h = face['bbox']
                cv2.rectangle(display_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(display_image, f"Face {face['confidence']:.2f}", 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # 繪製姿態關鍵點
            if results['pose']['success']:
                landmarks = results['pose']['landmarks']
                for i, (x, y) in enumerate(landmarks):
                    cv2.circle(display_image, (int(x), int(y)), 3, (255, 0, 0), -1)
                    if i < 10:  # 只標註前10個點避免太亂
                        cv2.putText(display_image, str(i), (int(x)+5, int(y)), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
            
            # 保存結果
            output_path = f"qai_hub_result_{os.path.basename(img_path)}"
            cv2.imwrite(output_path, display_image)
            print(f"  💾 結果已保存: {output_path}")

def test_live_detection():
    """測試即時檢測"""
    print("\n🎥 QAI Hub 即時檢測測試")
    
    detector = QAIHubUnifiedDetector()
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 無法開啟攝像頭")
        return
    
    print("按 'q' 退出即時檢測")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 縮小圖像以提高處理速度
            small_frame = cv2.resize(frame, (640, 480))
            
            # QAI Hub統一檢測
            results = detector.unified_detection(small_frame)
            
            # 繪製檢測結果
            display_frame = small_frame.copy()
            
            # 人臉框
            for face in results['faces']:
                x, y, w, h = face['bbox']
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(display_frame, "QAI Face", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 姿態關鍵點
            if results['pose']['success']:
                landmarks = results['pose']['landmarks']
                for x, y in landmarks[:11]:  # 只顯示主要關鍵點
                    cv2.circle(display_frame, (int(x), int(y)), 4, (255, 0, 0), -1)
            
            # 顯示處理時間
            total_time = results['summary']['processing_time']['total']
            fps = 1.0 / max(total_time, 0.001)
            cv2.putText(display_frame, f"QAI Hub FPS: {fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('QAI Hub Unified Detection', display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # 運行演示
    demo_qai_hub_detection()
    
    # 詢問是否運行即時檢測
    response = input("\n🎥 是否測試即時檢測？(y/n): ")
    if response.lower() == 'y':
        test_live_detection()
    
    print("\n🎉 QAI Hub 統一檢測演示完成！")
