#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用真實圖像測試檢測方法
解決 QAI Hub MediaPipe 和標準 MediaPipe 的問題
"""

import cv2
import numpy as np
import time
import logging
from PIL import Image
from typing import List, Tuple, Optional, Dict, Any
import os
import sys

# 環境配置
os.environ['PYTHONPATH'] = '/Users/andycyw/mvp_fall_detection_starter/.venv_mediapipe/lib/python3.11/site-packages'

# 日誌配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealImageFallDetector:
    def __init__(self):
        self.current_method = "QAI_Hub_MediaPipe"
        self.detection_methods = [
            "QAI_Hub_MediaPipe",
            "Standard_MediaPipe", 
            "OpenCV_Fallback",
            "Simulation_Demo"
        ]
        
        # 性能統計
        self.performance_stats = {method: {'success': 0, 'total': 0, 'times': []} 
                                for method in self.detection_methods}
        
        # 初始化各種檢測器
        self.qai_hub_models = None
        self.mediapipe_pose = None
        self.opencv_detector = None
        
        self._initialize_detectors()
    
    def _initialize_detectors(self):
        """初始化所有檢測器"""
        print("🚀 初始化檢測器...")
        
        # 1. QAI Hub MediaPipe
        try:
            from qai_hub_models.models.mediapipe_pose.app import MediaPipePoseApp
            from qai_hub_models.models.mediapipe_pose.model import MediaPipePose
            
            pose_model = MediaPipePose.from_pretrained()
            self.qai_hub_models = MediaPipePoseApp.from_pretrained(pose_model)
            print("✅ QAI Hub MediaPipe 初始化成功")
        except Exception as e:
            print(f"⚠️ QAI Hub MediaPipe 初始化失敗: {e}")
        
        # 2. 標準 MediaPipe
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            
            # 優化配置用於更好的檢測
            self.mediapipe_pose = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,  # 最高複雜度
                smooth_landmarks=True,
                enable_segmentation=True,  # 啟用分割
                min_detection_confidence=0.1,  # 非常低的檢測閾值
                min_tracking_confidence=0.1
            )
            print("✅ 標準 MediaPipe 初始化成功")
        except Exception as e:
            print(f"⚠️ 標準 MediaPipe 初始化失敗: {e}")
    
    def load_official_test_image(self):
        """載入官方測試圖像"""
        try:
            from qai_hub_models.models.mediapipe_pose.model import MODEL_ID, MODEL_ASSET_VERSION
            from qai_hub_models.utils.asset_loaders import CachedWebModelAsset, load_image
            
            print("📥 載入官方測試圖像...")
            official_image_asset = CachedWebModelAsset.from_asset_store(
                MODEL_ID, MODEL_ASSET_VERSION, "pose.jpeg"
            )
            official_image = load_image(official_image_asset)
            
            if isinstance(official_image, Image.Image):
                official_image = np.array(official_image)
                # 轉換 RGB 到 BGR (OpenCV 格式)
                official_image = cv2.cvtColor(official_image, cv2.COLOR_RGB2BGR)
            
            print(f"✅ 官方圖像尺寸: {official_image.shape}")
            return official_image
            
        except Exception as e:
            print(f"❌ 無法載入官方測試圖像: {e}")
            return None
    
    def _detect_qai_hub_mediapipe(self, image: np.ndarray) -> Tuple[bool, List[Tuple[float, float]], str]:
        """改進的 QAI Hub MediaPipe 檢測"""
        try:
            if self.qai_hub_models is None:
                return False, [], "QAI Hub 模型未初始化"
            
            # 轉換為 RGB PIL 圖像
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # 使用 raw_output=True 獲取詳細結果
            start_time = time.time()
            result = self.qai_hub_models.predict_landmarks_from_image(pil_image, raw_output=True)
            detection_time = time.time() - start_time
            
            print(f"  QAI Hub 結果類型: {type(result)}")
            print(f"  QAI Hub 結果長度: {len(result) if hasattr(result, '__len__') else 'N/A'}")
            
            if not isinstance(result, tuple) or len(result) < 4:
                return False, [], f"無效的結果格式: {type(result)}"
            
            batched_selected_boxes, batched_selected_keypoints, batched_roi_4corners, landmarks_out = result
            
            print(f"  Boxes 數量: {len(batched_selected_boxes)}")
            print(f"  Keypoints 數量: {len(batched_selected_keypoints)}")
            print(f"  Landmarks 數量: {len(landmarks_out) if landmarks_out else 0}")
            
            # 檢查第一個 batch
            if len(batched_selected_boxes) > 0:
                boxes = batched_selected_boxes[0]
                print(f"  第一個 Boxes 形狀: {boxes.shape if hasattr(boxes, 'shape') else type(boxes)}")
                print(f"  第一個 Boxes 元素數量: {boxes.numel() if hasattr(boxes, 'numel') else 'N/A'}")
                
                if hasattr(boxes, 'numel') and boxes.numel() > 0:
                    print(f"  ✅ 檢測到邊界框!")
                    
                    # 解析關鍵點
                    pose_landmarks = []
                    
                    if landmarks_out and len(landmarks_out) > 0:
                        landmarks = landmarks_out[0]
                        print(f"  Landmarks 類型: {type(landmarks)}")
                        
                        if isinstance(landmarks, list) and len(landmarks) > 0:
                            for i, landmark_tensor in enumerate(landmarks):
                                print(f"    Landmark {i}: {landmark_tensor.shape if hasattr(landmark_tensor, 'shape') else type(landmark_tensor)}")
                                
                                if hasattr(landmark_tensor, 'shape') and landmark_tensor.numel() > 0:
                                    # landmark_tensor 形狀應該是 [1, N, 4] (batch, landmarks, coordinates)
                                    if len(landmark_tensor.shape) >= 2:
                                        if len(landmark_tensor.shape) == 3:
                                            landmark_data = landmark_tensor[0]  # 取第一個 batch
                                        else:
                                            landmark_data = landmark_tensor
                                        
                                        print(f"      處理形狀: {landmark_data.shape}")
                                        
                                        for j in range(min(landmark_data.shape[0], 33)):  # 最多33個關鍵點
                                            if landmark_data.shape[1] >= 2:  # 至少有 x, y
                                                x, y = float(landmark_data[j, 0]), float(landmark_data[j, 1])
                                                
                                                # 檢查是否為歸一化座標 (0-1) 或圖像座標
                                                if 0 <= x <= 1 and 0 <= y <= 1:
                                                    # 歸一化座標，轉換為圖像座標
                                                    img_x = x * image.shape[1]
                                                    img_y = y * image.shape[0]
                                                else:
                                                    # 假設已經是圖像座標
                                                    img_x, img_y = x, y
                                                
                                                if 0 <= img_x <= image.shape[1] and 0 <= img_y <= image.shape[0]:
                                                    pose_landmarks.append((img_x, img_y))
                    
                    if pose_landmarks:
                        self.performance_stats['QAI_Hub_MediaPipe']['times'].append(detection_time)
                        return True, pose_landmarks, f"檢測到 {len(pose_landmarks)} 個關鍵點"
                    else:
                        return False, [], "有邊界框但無法解析關鍵點"
                else:
                    return False, [], "未檢測到邊界框"
            
            return False, [], "無檢測結果"
                
        except Exception as e:
            logger.error(f"QAI Hub MediaPipe 檢測錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False, [], f"檢測錯誤: {str(e)}"
    
    def _detect_standard_mediapipe(self, image: np.ndarray) -> Tuple[bool, List[Tuple[float, float]], str]:
        """改進的標準 MediaPipe 檢測"""
        try:
            if self.mediapipe_pose is None:
                return False, [], "MediaPipe 模型未初始化"
            
            # 轉換為 RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            start_time = time.time()
            results = self.mediapipe_pose.process(rgb_image)
            detection_time = time.time() - start_time
            
            print(f"  MediaPipe 結果: {results.pose_landmarks is not None}")
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                print(f"  關鍵點數量: {len(landmarks)}")
                
                pose_landmarks = []
                
                # 轉換關鍵點座標
                height, width = image.shape[:2]
                visible_count = 0
                
                for i, landmark in enumerate(landmarks):
                    x = landmark.x * width
                    y = landmark.y * height
                    visibility = landmark.visibility
                    
                    if visibility > 0.1:  # 降低可見性閾值
                        pose_landmarks.append((x, y))
                        if visibility > 0.5:
                            visible_count += 1
                
                if pose_landmarks:
                    self.performance_stats['Standard_MediaPipe']['times'].append(detection_time)
                    return True, pose_landmarks, f"檢測到 {len(pose_landmarks)} 個關鍵點 (高可見性: {visible_count})"
            
            return False, [], "未檢測到姿態關鍵點"
            
        except Exception as e:
            logger.error(f"標準 MediaPipe 檢測錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False, [], f"檢測錯誤: {str(e)}"
    
    def _detect_simulation_demo(self, image: np.ndarray) -> Tuple[bool, List[Tuple[float, float]], str]:
        """智能模擬檢測（用於演示）"""
        try:
            start_time = time.time()
            
            height, width = image.shape[:2]
            center_x, center_y = width // 2, height // 2
            
            # 生成標準的 33 個 MediaPipe 關鍵點
            pose_landmarks = [
                # 臉部關鍵點 (0-10)
                (center_x, center_y - height//3),  # 0: 鼻子
                (center_x - 10, center_y - height//3 - 5),  # 1: 左眼內角
                (center_x - 20, center_y - height//3),  # 2: 左眼
                (center_x - 30, center_y - height//3 - 5),  # 3: 左眼外角
                (center_x + 10, center_y - height//3 - 5),  # 4: 右眼內角
                (center_x + 20, center_y - height//3),  # 5: 右眼
                (center_x + 30, center_y - height//3 - 5),  # 6: 右眼外角
                (center_x - 25, center_y - height//3 + 10),  # 7: 左耳
                (center_x + 25, center_y - height//3 + 10),  # 8: 右耳
                (center_x - 10, center_y - height//3 + 15),  # 9: 嘴左
                (center_x + 10, center_y - height//3 + 15),  # 10: 嘴右
                
                # 上身關鍵點 (11-22)
                (center_x - 40, center_y - height//6),  # 11: 左肩
                (center_x + 40, center_y - height//6),  # 12: 右肩
                (center_x - 80, center_y),  # 13: 左肘
                (center_x + 80, center_y),  # 14: 右肘
                (center_x - 100, center_y + height//8),  # 15: 左手腕
                (center_x + 100, center_y + height//8),  # 16: 右手腕
                (center_x - 110, center_y + height//6),  # 17: 左手指
                (center_x + 110, center_y + height//6),  # 18: 右手指
                (center_x - 15, center_y + height//8),  # 19: 左臀
                (center_x + 15, center_y + height//8),  # 20: 右臀
                (center_x - 120, center_y + height//6),  # 21: 左小指
                (center_x + 120, center_y + height//6),  # 22: 右小指
                
                # 下身關鍵點 (23-32)
                (center_x - 20, center_y + height//4),  # 23: 左膝
                (center_x + 20, center_y + height//4),  # 24: 右膝
                (center_x - 25, center_y + height//2.5),  # 25: 左腳踝
                (center_x + 25, center_y + height//2.5),  # 26: 右腳踝
                (center_x - 30, center_y + height//2.2),  # 27: 左腳跟
                (center_x + 30, center_y + height//2.2),  # 28: 右腳跟
                (center_x - 35, center_y + height//2),  # 29: 左腳趾
                (center_x + 35, center_y + height//2),  # 30: 右腳趾
                (center_x - 40, center_y + height//2),  # 31: 左腳外側
                (center_x + 40, center_y + height//2),  # 32: 右腳外側
            ]
            
            # 確保座標在圖像範圍內
            valid_landmarks = []
            for x, y in pose_landmarks:
                x = max(0, min(width, x))
                y = max(0, min(height, y))
                valid_landmarks.append((x, y))
            
            detection_time = time.time() - start_time
            self.performance_stats['Simulation_Demo']['times'].append(detection_time)
            
            return True, valid_landmarks, f"模擬檢測生成 {len(valid_landmarks)} 個關鍵點（演示模式）"
            
        except Exception as e:
            logger.error(f"模擬檢測錯誤: {e}")
            return False, [], f"模擬錯誤: {str(e)}"
    
    def detect_pose(self, image: np.ndarray) -> Tuple[bool, List[Tuple[float, float]], str]:
        """統一的姿態檢測接口"""
        method = self.current_method
        self.performance_stats[method]['total'] += 1
        
        # 根據當前方法進行檢測
        if method == "QAI_Hub_MediaPipe":
            success, landmarks, info = self._detect_qai_hub_mediapipe(image)
        elif method == "Standard_MediaPipe":
            success, landmarks, info = self._detect_standard_mediapipe(image)
        elif method == "Simulation_Demo":
            success, landmarks, info = self._detect_simulation_demo(image)
        else:
            return False, [], f"未知檢測方法: {method}"
        
        # 更新統計
        if success:
            self.performance_stats[method]['success'] += 1
        
        return success, landmarks, info
    
    def switch_detection_method(self, method: str):
        """切換檢測方法"""
        if method in self.detection_methods:
            old_method = self.current_method
            self.current_method = method
            print(f"🔄 切換檢測方法: {old_method} → {method}")
        else:
            print(f"❌ 無效的檢測方法: {method}")
    
    def get_performance_summary(self) -> str:
        """獲取性能統計摘要"""
        summary = "\n📊 檢測性能統計:\n" + "="*50 + "\n"
        
        for method, stats in self.performance_stats.items():
            total = stats['total']
            success = stats['success']
            success_rate = (success / total * 100) if total > 0 else 0
            
            avg_time = 0
            if stats['times']:
                avg_time = sum(stats['times']) / len(stats['times'])
            
            status = "✅" if success_rate > 80 else "⚠️" if success_rate > 50 else "❌"
            
            summary += f"{status} {method}:\n"
            summary += f"   成功率: {success_rate:.1f}% ({success}/{total})\n"
            summary += f"   平均耗時: {avg_time:.3f}秒\n"
            if method == self.current_method:
                summary += f"   📍 當前使用中\n"
            summary += "\n"
        
        return summary

def main():
    """主函數"""
    print("🎯 真實圖像跌倒檢測測試")
    print("=" * 50)
    
    detector = RealImageFallDetector()
    
    # 載入官方測試圖像
    test_image = detector.load_official_test_image()
    
    if test_image is None:
        print("❌ 無法載入測試圖像，退出")
        return
    
    # 保存測試圖像
    cv2.imwrite("official_test_image.jpg", test_image)
    print("💾 保存官方測試圖像: official_test_image.jpg")
    
    # 測試每個檢測方法
    test_methods = ["QAI_Hub_MediaPipe", "Standard_MediaPipe", "Simulation_Demo"]
    
    for method in test_methods:
        print(f"\n🧪 測試方法: {method}")
        print("-" * 40)
        
        detector.switch_detection_method(method)
        success, landmarks, info = detector.detect_pose(test_image)
        
        status = "✅" if success else "❌"
        print(f"{status} 結果: {info}")
        
        if success and landmarks:
            # 繪製檢測結果
            result_image = test_image.copy()
            for i, (x, y) in enumerate(landmarks):
                cv2.circle(result_image, (int(x), int(y)), 5, (0, 255, 0), -1)
                cv2.putText(result_image, str(i), (int(x)+8, int(y)-8), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imwrite(f"result_{method.lower()}.jpg", result_image)
            print(f"💾 保存結果圖像: result_{method.lower()}.jpg")
    
    # 顯示性能統計
    print(detector.get_performance_summary())

if __name__ == "__main__":
    main()
