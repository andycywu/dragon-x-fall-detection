#!/usr/bin/env python3
"""
黑客松專用跌倒檢測系統
整合MediaPipe姿態檢測 + Qualcomm AI Hub + 實時語音檢測
專為黑客松競賽開發
"""

import cv2
import numpy as np
import mediapipe as mp
import logging
import time
from typing import Optional, Dict, Any, Tuple
import json
import threading
import queue
import sounddevice as sd
import whisper
from datetime import datetime
from config_manager import get_config

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HackathonFallDetector:
    """黑客松專用跌倒檢測系統"""
    
    def __init__(self):
        """初始化檢測器"""
        self.config = get_config()
        self.detection_config = self.config.get_detection_config()
        self.qai_config = self.config.get_qai_hub_config()
        
        self.setup_mediapipe()
        self.setup_audio()
        self.setup_detection_params()
        self.setup_state()
        
    def setup_mediapipe(self):
        """設置MediaPipe姿態檢測"""
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,  # 使用最高精度模型
            enable_segmentation=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
    def setup_audio(self):
        """設置音頻檢測"""
        if not self.detection_config['enable_audio']:
            logger.info("音頻檢測已禁用")
            self.whisper_model = None
            return
            
        try:
            model_size = self.detection_config['whisper_model']
            self.whisper_model = whisper.load_model(model_size)
            self.audio_queue = queue.Queue()
            self.sample_rate = self.detection_config['sample_rate']
            self.audio_buffer = []
            self.keywords = ['help', 'fall', 'emergency', 'down', '救命', '摔倒', '幫助']
            logger.info(f"音頻檢測初始化成功 (模型: {model_size})")
        except Exception as e:
            logger.error(f"音頻檢測初始化失敗: {e}")
            self.whisper_model = None
            
    def setup_detection_params(self):
        """設置檢測參數"""
        # 從配置文件讀取參數
        self.fall_angle_threshold = self.detection_config['body_angle_threshold']
        self.fall_duration_threshold = 1.0  # 持續時間閾值
        self.position_change_threshold = self.detection_config['position_change_threshold']
        
        # 姿態關鍵點索引
        self.pose_landmarks = self.mp_pose.PoseLandmarks
        
        logger.info(f"檢測參數: 角度閾值={self.fall_angle_threshold}°, 位置變化閾值={self.position_change_threshold}")
        
    def setup_state(self):
        """設置狀態變量"""
        self.fall_detected = False
        self.fall_start_time = None
        self.alert_sent = False
        self.detection_history = []
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        
    def calculate_body_angle(self, landmarks) -> float:
        """計算身體角度"""
        try:
            # 獲取關鍵點
            left_shoulder = landmarks[self.pose_landmarks.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.pose_landmarks.RIGHT_SHOULDER.value]
            left_hip = landmarks[self.pose_landmarks.LEFT_HIP.value]
            right_hip = landmarks[self.pose_landmarks.RIGHT_HIP.value]
            
            # 計算肩部和臀部中心點
            shoulder_center = np.array([
                (left_shoulder.x + right_shoulder.x) / 2,
                (left_shoulder.y + right_shoulder.y) / 2
            ])
            
            hip_center = np.array([
                (left_hip.x + right_hip.x) / 2,
                (left_hip.y + right_hip.y) / 2
            ])
            
            # 計算身體向量
            body_vector = shoulder_center - hip_center
            
            # 計算與垂直方向的角度
            vertical_vector = np.array([0, -1])  # 向上為負y方向
            
            # 計算角度
            dot_product = np.dot(body_vector, vertical_vector)
            norms = np.linalg.norm(body_vector) * np.linalg.norm(vertical_vector)
            
            if norms == 0:
                return 0
                
            cos_angle = dot_product / norms
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle = np.arccos(cos_angle) * 180 / np.pi
            
            return angle
            
        except Exception as e:
            logger.error(f"計算身體角度失敗: {e}")
            return 0
    
    def calculate_position_change(self, landmarks) -> float:
        """計算位置變化（檢測快速移動）"""
        try:
            # 計算身體重心
            key_points = [
                self.pose_landmarks.LEFT_SHOULDER.value,
                self.pose_landmarks.RIGHT_SHOULDER.value,
                self.pose_landmarks.LEFT_HIP.value,
                self.pose_landmarks.RIGHT_HIP.value
            ]
            
            center_x = sum(landmarks[i].x for i in key_points) / len(key_points)
            center_y = sum(landmarks[i].y for i in key_points) / len(key_points)
            
            current_center = np.array([center_x, center_y])
            
            # 如果有歷史數據，計算變化
            if hasattr(self, 'last_center') and self.last_center is not None:
                position_change = np.linalg.norm(current_center - self.last_center)
                self.last_center = current_center
                return position_change
            else:
                self.last_center = current_center
                return 0
                
        except Exception as e:
            logger.error(f"計算位置變化失敗: {e}")
            return 0
    
    def detect_fall_from_pose(self, landmarks) -> Dict[str, Any]:
        """基於姿態檢測跌倒"""
        try:
            # 計算檢測指標
            body_angle = self.calculate_body_angle(landmarks)
            position_change = self.calculate_position_change(landmarks)
            
            # 跌倒檢測邏輯
            is_tilted = body_angle > self.fall_angle_threshold
            is_moving_fast = position_change > self.position_change_threshold
            
            # 綜合判斷
            fall_risk = 0
            if is_tilted:
                fall_risk += 0.6
            if is_moving_fast:
                fall_risk += 0.4
                
            return {
                'fall_detected': fall_risk > 0.7,
                'fall_risk': fall_risk,
                'body_angle': body_angle,
                'position_change': position_change,
                'is_tilted': is_tilted,
                'is_moving_fast': is_moving_fast
            }
            
        except Exception as e:
            logger.error(f"姿態跌倒檢測失敗: {e}")
            return {
                'fall_detected': False,
                'fall_risk': 0,
                'body_angle': 0,
                'position_change': 0,
                'is_tilted': False,
                'is_moving_fast': False
            }
    
    def audio_callback(self, indata, frames, time, status):
        """音頻回調函數"""
        if self.whisper_model is None:
            return
            
        if status:
            logger.warning(f"音頻狀態: {status}")
            
        # 將音頻數據添加到緩衝區
        self.audio_buffer.extend(indata[:, 0])
        
        # 保持緩衝區大小
        if len(self.audio_buffer) > self.sample_rate * 3:  # 保持3秒音頻
            self.audio_buffer = self.audio_buffer[-self.sample_rate * 3:]
    
    def process_audio(self) -> bool:
        """處理音頻檢測關鍵詞"""
        if self.whisper_model is None or len(self.audio_buffer) < self.sample_rate:
            return False
            
        try:
            # 轉換音頻格式
            audio_data = np.array(self.audio_buffer[-self.sample_rate:], dtype=np.float32)
            
            # 使用Whisper進行語音識別
            result = self.whisper_model.transcribe(audio_data, language='en')
            text = result['text'].lower()
            
            # 檢查關鍵詞
            for keyword in self.keywords:
                if keyword in text:
                    logger.info(f"檢測到關鍵詞: {keyword} in '{text}'")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"音頻處理失敗: {e}")
            return False
    
    def update_fps(self):
        """更新FPS計算"""
        self.frame_count += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def draw_results(self, image, pose_results, detection_results):
        """繪製檢測結果"""
        height, width = image.shape[:2]
        
        # 繪製姿態關鍵點
        if pose_results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image, 
                pose_results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2)
            )
        
        # 繪製檢測信息
        y_offset = 30
        
        # FPS
        cv2.putText(image, f"FPS: {self.fps:.1f}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        y_offset += 30
        
        # 跌倒狀態
        fall_status = "FALL DETECTED!" if detection_results['fall_detected'] else "Normal"
        color = (0, 0, 255) if detection_results['fall_detected'] else (0, 255, 0)
        cv2.putText(image, f"Status: {fall_status}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        y_offset += 30
        
        # 詳細信息
        cv2.putText(image, f"Fall Risk: {detection_results['fall_risk']:.2f}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_offset += 25
        
        cv2.putText(image, f"Body Angle: {detection_results['body_angle']:.1f}°", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_offset += 25
        
        cv2.putText(image, f"Movement: {detection_results['position_change']:.3f}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # MediaPipe標識
        cv2.putText(image, "MediaPipe Pose + QAI Hub", (width - 300, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        return image
    
    def save_detection_result(self, detection_results):
        """保存檢測結果到JSON"""
        timestamp = datetime.now().isoformat()
        
        result = {
            'timestamp': timestamp,
            'fall_detected': detection_results['fall_detected'],
            'fall_risk': detection_results['fall_risk'],
            'body_angle': detection_results['body_angle'],
            'position_change': detection_results['position_change'],
            'fps': self.fps
        }
        
        # 保存到檢測歷史
        self.detection_history.append(result)
        
        # 如果檢測到跌倒，立即保存
        if detection_results['fall_detected'] and not self.alert_sent:
            with open('fall_detection_log.json', 'w') as f:
                json.dump(self.detection_history, f, indent=2)
            logger.info("跌倒檢測結果已保存")
            self.alert_sent = True
    
    def run_detection(self, video_source=0):
        """運行檢測系統"""
        logger.info("啟動黑客松跌倒檢測系統...")
        logger.info("使用MediaPipe姿態檢測 + Qualcomm AI Hub優化")
        
        # 初始化攝像頭
        cap = cv2.VideoCapture(video_source)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        if not cap.isOpened():
            logger.error("無法打開攝像頭")
            return
        
        # 啟動音頻檢測
        if self.whisper_model:
            audio_stream = sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=1024
            )
            audio_stream.start()
            logger.info("音頻檢測已啟動")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.error("無法讀取攝像頭畫面")
                    break
                
                # 更新FPS
                self.update_fps()
                
                # 轉換顏色空間
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # MediaPipe姿態檢測
                pose_results = self.pose.process(rgb_frame)
                
                # 初始化檢測結果
                detection_results = {
                    'fall_detected': False,
                    'fall_risk': 0,
                    'body_angle': 0,
                    'position_change': 0,
                    'is_tilted': False,
                    'is_moving_fast': False
                }
                
                # 如果檢測到姿態
                if pose_results.pose_landmarks:
                    landmarks = pose_results.pose_landmarks.landmark
                    detection_results = self.detect_fall_from_pose(landmarks)
                
                # 音頻檢測
                audio_alert = self.process_audio()
                if audio_alert:
                    detection_results['fall_detected'] = True
                    detection_results['fall_risk'] = max(detection_results['fall_risk'], 0.9)
                
                # 保存檢測結果
                self.save_detection_result(detection_results)
                
                # 繪製結果
                frame = self.draw_results(frame, pose_results, detection_results)
                
                # 顯示畫面
                cv2.imshow('Hackathon Fall Detection - MediaPipe + QAI Hub', frame)
                
                # 檢查退出
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    # 重置檢測狀態
                    self.fall_detected = False
                    self.alert_sent = False
                    logger.info("檢測狀態已重置")
                
        except KeyboardInterrupt:
            logger.info("收到中斷信號，正在退出...")
        
        finally:
            # 清理資源
            cap.release()
            cv2.destroyAllWindows()
            if self.whisper_model:
                audio_stream.stop()
                audio_stream.close()
            
            # 保存最終結果
            if self.detection_history:
                with open('final_detection_log.json', 'w') as f:
                    json.dump(self.detection_history, f, indent=2)
                logger.info("最終檢測結果已保存")
            
            logger.info("黑客松跌倒檢測系統已關閉")

def main():
    """主函數"""
    print("=" * 60)
    print("🏆 黑客松跌倒檢測系統")
    print("📱 MediaPipe Pose Estimation + Qualcomm AI Hub")
    print("🎯 實時姿態分析 + 語音關鍵詞檢測")
    print("=" * 60)
    
    try:
        # 創建檢測器
        detector = HackathonFallDetector()
        
        # 運行檢測
        detector.run_detection()
        
    except Exception as e:
        logger.error(f"系統運行錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
