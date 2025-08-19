#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏆 黑客松 - QAI Hub MediaPipe 跌倒檢測系統 (修正版)
使用 Qualcomm AI Hub 的 MediaPipe Pose 模型實現跌倒檢測
完全解決 protobuf 版本衝突問題，正確解析 QAI Hub 輸出格式
"""

import cv2
import numpy as np
import time
import math
from typing import Tuple, List, Optional, Dict, Any, Union
from dataclasses import dataclass
import logging
from PIL import Image
import torch

# QAI Hub MediaPipe Pose 導入
from qai_hub_models.models.mediapipe_pose.app import MediaPipePoseApp
from qai_hub_models.models.mediapipe_pose.model import MediaPipePose, POSE_LANDMARK_CONNECTIONS

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PoseKeypoint:
    """姿態關鍵點"""
    x: float
    y: float
    z: float
    visibility: float

@dataclass
class FallDetectionResult:
    """跌倒檢測結果"""
    is_fall: bool
    confidence: float
    body_angle: float
    risk_level: str
    reason: str
    timestamp: float
    landmarks_count: int

class QAIHubMediaPipeFallDetector:
    """基於 QAI Hub MediaPipe 的跌倒檢測器（修正版）"""
    
    def __init__(self, 
                 fall_threshold: float = 30.0,
                 position_change_threshold: float = 0.3,
                 confidence_threshold: float = 0.5):
        """
        初始化跌倒檢測器
        
        Args:
            fall_threshold: 跌倒角度閾值（度）
            position_change_threshold: 位置變化閾值
            confidence_threshold: 置信度閾值
        """
        self.fall_threshold = fall_threshold
        self.position_change_threshold = position_change_threshold
        self.confidence_threshold = confidence_threshold
        
        # 載入 QAI Hub MediaPipe 模型
        logger.info("🚀 載入 QAI Hub MediaPipe Pose 模型...")
        self.pose_model = MediaPipePose.from_pretrained()
        self.pose_app = MediaPipePoseApp.from_pretrained(self.pose_model)
        logger.info("✅ QAI Hub MediaPipe Pose 模型載入完成")
        
        # 歷史數據用於時序分析
        self.pose_history: List[List[PoseKeypoint]] = []
        self.max_history = 10
        
        # MediaPipe 關鍵點索引 (33點模型)
        self.NOSE = 0
        self.LEFT_EYE_INNER = 1
        self.LEFT_EYE = 2
        self.LEFT_EYE_OUTER = 3
        self.RIGHT_EYE_INNER = 4
        self.RIGHT_EYE = 5
        self.RIGHT_EYE_OUTER = 6
        self.LEFT_EAR = 7
        self.RIGHT_EAR = 8
        self.MOUTH_LEFT = 9
        self.MOUTH_RIGHT = 10
        self.LEFT_SHOULDER = 11
        self.RIGHT_SHOULDER = 12
        self.LEFT_ELBOW = 13
        self.RIGHT_ELBOW = 14
        self.LEFT_WRIST = 15
        self.RIGHT_WRIST = 16
        self.LEFT_PINKY = 17
        self.RIGHT_PINKY = 18
        self.LEFT_INDEX = 19
        self.RIGHT_INDEX = 20
        self.LEFT_THUMB = 21
        self.RIGHT_THUMB = 22
        self.LEFT_HIP = 23
        self.RIGHT_HIP = 24
        self.LEFT_KNEE = 25
        self.RIGHT_KNEE = 26
        self.LEFT_ANKLE = 27
        self.RIGHT_ANKLE = 28
        self.LEFT_HEEL = 29
        self.RIGHT_HEEL = 30
        self.LEFT_FOOT_INDEX = 31
        self.RIGHT_FOOT_INDEX = 32
        
        # 統計數據
        self.stats = {
            'total_frames': 0,
            'successful_detections': 0,
            'fall_detections': 0,
            'avg_processing_time': 0.0,
            'last_detection_time': None
        }
    
    def detect_pose(self, image: np.ndarray) -> Optional[List[PoseKeypoint]]:
        """
        使用 QAI Hub MediaPipe 檢測姿態
        
        Args:
            image: 輸入圖像 (BGR format)
            
        Returns:
            姿態關鍵點列表，如果檢測失敗則返回 None
        """
        try:
            start_time = time.time()
            
            # 轉換圖像格式 (BGR -> RGB)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # 使用 QAI Hub MediaPipe 進行姿態檢測 (raw_output=True 獲取原始數據)
            result = self.pose_app.predict_landmarks_from_image(pil_image, raw_output=True)
            
            processing_time = time.time() - start_time
            self.stats['avg_processing_time'] = (
                self.stats['avg_processing_time'] * self.stats['total_frames'] + processing_time
            ) / (self.stats['total_frames'] + 1)
            
            # 解析 QAI Hub 的輸出
            if result and len(result) >= 4:
                landmarks = self._parse_qai_hub_results(result)
                if landmarks:
                    self.stats['successful_detections'] += 1
                return landmarks
            
            return None
            
        except Exception as e:
            logger.error(f"姿態檢測錯誤: {e}")
            return None
    
    def _parse_qai_hub_results(self, results) -> Optional[List[PoseKeypoint]]:
        """
        解析 QAI Hub MediaPipe 的檢測結果
        
        Args:
            results: QAI Hub 的原始檢測結果
                     (batched_selected_boxes, batched_selected_keypoints, batched_roi_4corners, landmarks_out)
            
        Returns:
            標準化的關鍵點列表
        """
        try:
            batched_selected_boxes, batched_selected_keypoints, batched_roi_4corners, *landmarks_out = results
            
            # 檢查是否有檢測到的姿態
            if not landmarks_out or len(landmarks_out) == 0:
                return None
            
            # 獲取第一批的第一個檢測結果
            batch_landmarks = landmarks_out[0]  # 第一批
            if not isinstance(batch_landmarks, list) or len(batch_landmarks) == 0:
                return None
            
            first_person_landmarks = batch_landmarks[0]  # 第一個人
            if not isinstance(first_person_landmarks, torch.Tensor):
                return None
            
            # 轉換 torch tensor 到 numpy
            landmarks_array = first_person_landmarks.cpu().numpy()
            
            # 確保有正確的形狀 [num_landmarks, 3] 其中 3 = (x, y, confidence)
            if landmarks_array.shape[1] != 3:
                logger.warning(f"意外的 landmarks 形狀: {landmarks_array.shape}")
                return None
            
            # 轉換為我們的 PoseKeypoint 格式
            landmarks = []
            for i in range(landmarks_array.shape[0]):
                x, y, confidence = landmarks_array[i]
                landmarks.append(PoseKeypoint(
                    x=float(x),
                    y=float(y),
                    z=0.0,  # QAI Hub MediaPipe 可能不提供 z 座標
                    visibility=float(confidence)
                ))
            
            return landmarks
            
        except Exception as e:
            logger.error(f"解析 QAI Hub 結果錯誤: {e}")
            return None
    
    def calculate_body_angle(self, landmarks: List[PoseKeypoint]) -> float:
        """
        計算身體傾斜角度
        
        Args:
            landmarks: 姿態關鍵點
            
        Returns:
            身體傾斜角度（度）
        """
        try:
            # 確保有足夠的關鍵點
            if len(landmarks) < 33:
                return 0.0
            
            # 獲取肩膀和髖部的關鍵點
            left_shoulder = landmarks[self.LEFT_SHOULDER]
            right_shoulder = landmarks[self.RIGHT_SHOULDER]
            left_hip = landmarks[self.LEFT_HIP]
            right_hip = landmarks[self.RIGHT_HIP]
            
            # 檢查關鍵點可見性
            min_visibility = 0.3
            if (left_shoulder.visibility < min_visibility or 
                right_shoulder.visibility < min_visibility or
                left_hip.visibility < min_visibility or 
                right_hip.visibility < min_visibility):
                return 0.0
            
            # 計算身體中線向量
            shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
            shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
            hip_center_x = (left_hip.x + right_hip.x) / 2
            hip_center_y = (left_hip.y + right_hip.y) / 2
            
            # 計算身體向量（從肩膀到髖部）
            body_vector_x = hip_center_x - shoulder_center_x
            body_vector_y = hip_center_y - shoulder_center_y
            
            # 計算與垂直軸的夾角
            # 垂直向量為 (0, 1)
            angle_rad = math.atan2(abs(body_vector_x), abs(body_vector_y))
            angle_deg = math.degrees(angle_rad)
            
            return angle_deg
            
        except Exception as e:
            logger.error(f"計算身體角度錯誤: {e}")
            return 0.0
    
    def analyze_fall_risk(self, landmarks: List[PoseKeypoint]) -> FallDetectionResult:
        """
        分析跌倒風險
        
        Args:
            landmarks: 姿態關鍵點
            
        Returns:
            跌倒檢測結果
        """
        timestamp = time.time()
        landmarks_count = len(landmarks) if landmarks else 0
        
        if not landmarks or landmarks_count == 0:
            return FallDetectionResult(
                is_fall=False,
                confidence=0.0,
                body_angle=0.0,
                risk_level="未知",
                reason="無姿態檢測",
                timestamp=timestamp,
                landmarks_count=0
            )
        
        # 計算身體角度
        body_angle = self.calculate_body_angle(landmarks)
        
        # 判斷跌倒風險
        is_fall = body_angle > self.fall_threshold
        confidence = min(body_angle / self.fall_threshold, 1.0) if self.fall_threshold > 0 else 0.0
        
        # 確定風險等級
        if body_angle < 10:
            risk_level = "低"
            reason = "姿態正常"
        elif body_angle < 20:
            risk_level = "中"
            reason = "輕微傾斜"
        elif body_angle < self.fall_threshold:
            risk_level = "高"
            reason = "身體傾斜明顯"
        else:
            risk_level = "危險"
            reason = "檢測到跌倒"
            self.stats['fall_detections'] += 1
            self.stats['last_detection_time'] = timestamp
        
        return FallDetectionResult(
            is_fall=is_fall,
            confidence=confidence,
            body_angle=body_angle,
            risk_level=risk_level,
            reason=reason,
            timestamp=timestamp,
            landmarks_count=landmarks_count
        )
    
    def draw_pose_landmarks(self, image: np.ndarray, landmarks: List[PoseKeypoint]) -> np.ndarray:
        """
        在圖像上繪製姿態關鍵點
        
        Args:
            image: 輸入圖像
            landmarks: 姿態關鍵點
            
        Returns:
            繪製了關鍵點的圖像
        """
        if not landmarks:
            return image
        
        output_image = image.copy()
        height, width = image.shape[:2]
        
        # 繪製關鍵點
        for i, landmark in enumerate(landmarks):
            if landmark.visibility > self.confidence_threshold:
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                
                # 確保座標在圖像範圍內
                if 0 <= x < width and 0 <= y < height:
                    cv2.circle(output_image, (x, y), 3, (0, 255, 0), -1)
                    # 只在重要關鍵點上顯示編號
                    if i in [self.NOSE, self.LEFT_SHOULDER, self.RIGHT_SHOULDER, 
                            self.LEFT_HIP, self.RIGHT_HIP, self.LEFT_KNEE, self.RIGHT_KNEE]:
                        cv2.putText(output_image, str(i), (x, y-5), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        
        # 繪製骨架連接
        for connection in POSE_LANDMARK_CONNECTIONS:
            start_idx, end_idx = connection
            if (start_idx < len(landmarks) and end_idx < len(landmarks) and
                landmarks[start_idx].visibility > self.confidence_threshold and
                landmarks[end_idx].visibility > self.confidence_threshold):
                
                start_x = int(landmarks[start_idx].x * width)
                start_y = int(landmarks[start_idx].y * height)
                end_x = int(landmarks[end_idx].x * width)
                end_y = int(landmarks[end_idx].y * height)
                
                # 確保座標在圖像範圍內
                if (0 <= start_x < width and 0 <= start_y < height and
                    0 <= end_x < width and 0 <= end_y < height):
                    cv2.line(output_image, (start_x, start_y), (end_x, end_y), (255, 0, 0), 2)
        
        return output_image
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, FallDetectionResult]:
        """
        處理單個影像幀
        
        Args:
            frame: 輸入影像幀
            
        Returns:
            處理後的影像和檢測結果
        """
        self.stats['total_frames'] += 1
        
        # 檢測姿態
        landmarks = self.detect_pose(frame)
        
        # 分析跌倒風險
        fall_result = self.analyze_fall_risk(landmarks)
        
        # 繪製姿態
        output_frame = self.draw_pose_landmarks(frame, landmarks) if landmarks else frame
        
        # 添加檢測信息到影像
        self._draw_detection_info(output_frame, fall_result)
        
        # 更新歷史記錄
        if landmarks:
            self.pose_history.append(landmarks)
            if len(self.pose_history) > self.max_history:
                self.pose_history.pop(0)
        
        return output_frame, fall_result
    
    def _draw_detection_info(self, image: np.ndarray, result: FallDetectionResult):
        """在影像上繪製檢測信息"""
        height, width = image.shape[:2]
        
        # 根據風險等級選擇顏色
        color_map = {
            "低": (0, 255, 0),      # 綠色
            "中": (0, 255, 255),    # 黃色
            "高": (0, 165, 255),    # 橙色
            "危險": (0, 0, 255),    # 紅色
            "未知": (128, 128, 128) # 灰色
        }
        color = color_map.get(result.risk_level, (255, 255, 255))
        
        # 繪製檢測信息
        info_texts = [
            f"風險等級: {result.risk_level}",
            f"身體角度: {result.body_angle:.1f}°",
            f"置信度: {result.confidence:.2f}",
            f"關鍵點數: {result.landmarks_count}",
            f"狀態: {result.reason}"
        ]
        
        for i, text in enumerate(info_texts):
            cv2.putText(image, text, (10, 30 + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # 如果檢測到跌倒，添加警告
        if result.is_fall:
            cv2.putText(image, "!! 跌倒警報 !!", (width//2 - 100, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        
        # 添加統計信息
        stats_text = f"檢測成功率: {self.stats['successful_detections']}/{self.stats['total_frames']}"
        cv2.putText(image, stats_text, (10, height - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        stats = self.stats.copy()
        if stats['total_frames'] > 0:
            stats['success_rate'] = stats['successful_detections'] / stats['total_frames']
        else:
            stats['success_rate'] = 0.0
        return stats

def demo_webcam():
    """攝像頭即時演示"""
    print("🎥 啟動攝像頭即時跌倒檢測演示...")
    print("按 'q' 鍵退出")
    
    # 初始化檢測器
    detector = QAIHubMediaPipeFallDetector()
    
    # 打開攝像頭
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 無法打開攝像頭")
        return
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ 無法讀取攝像頭數據")
                break
            
            # 處理幀
            output_frame, result = detector.process_frame(frame)
            
            # 顯示結果
            cv2.imshow('QAI Hub MediaPipe 跌倒檢測', output_frame)
            
            # 如果檢測到跌倒，打印警告
            if result.is_fall:
                print(f"🚨 跌倒警報！角度: {result.body_angle:.1f}°, "
                      f"置信度: {result.confidence:.2f}, 關鍵點: {result.landmarks_count}")
            
            # 按 'q' 退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n👋 用戶中斷程序")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # 顯示統計信息
        stats = detector.get_stats()
        print(f"\n📊 檢測統計:")
        print(f"   總幀數: {stats['total_frames']}")
        print(f"   成功檢測: {stats['successful_detections']}")
        print(f"   成功率: {stats['success_rate']:.2%}")
        print(f"   跌倒檢測次數: {stats['fall_detections']}")
        print(f"   平均處理時間: {stats['avg_processing_time']:.3f}秒")

def demo_test():
    """測試模型載入和基本功能"""
    print("🧪 測試 QAI Hub MediaPipe 模型載入...")
    
    try:
        detector = QAIHubMediaPipeFallDetector()
        print("✅ QAI Hub MediaPipe 模型載入成功！")
        print("🎯 系統已準備就緒，可以進行跌倒檢測")
        
        # 測試一個虛擬幀
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        output_frame, result = detector.process_frame(test_frame)
        
        print(f"📊 測試結果:")
        print(f"   檢測狀態: {result.reason}")
        print(f"   關鍵點數: {result.landmarks_count}")
        print(f"   處理時間: {detector.stats['avg_processing_time']:.3f}秒")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def main():
    """主函數"""
    print("🏆 QAI Hub MediaPipe 跌倒檢測系統 (修正版)")
    print("=" * 55)
    print("選擇演示模式:")
    print("1. 攝像頭即時檢測")
    print("2. 測試模型載入")
    print("3. 退出")
    
    try:
        choice = input("請輸入選擇 (1-3): ").strip()
        
        if choice == "1":
            demo_webcam()
        elif choice == "2":
            demo_test()
        elif choice == "3":
            print("👋 再見！")
        else:
            print("❌ 無效選擇")
            
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    main()
