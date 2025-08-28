
#!/usr/bin/env python3
"""
📌 Module: elderly_behavior_predictor.py
🧠 完整老人行為預測與風險評估系統

整合人臉識別、姿態追蹤、風險評估和語音互動功能
"""

import cv2
import numpy as np
import json
import sqlite3
import time
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import logging
from dataclasses import dataclass, asdict
import math
from collections import deque, defaultdict
import warnings
warnings.filterwarnings("ignore")

# Optional dependencies: try to import, set to None on failure
try:
    import face_recognition
except Exception:
    face_recognition = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    import whisper
except Exception:
    whisper = None

# 嘗試導入官方QAI Hub檢測系統
try:
    from official_qai_hub_detector import OfficialQAIHubDetector
    print("✅ 成功導入官方QAI Hub檢測系統")
except ImportError:
    print("⚠️ 無法導入官方QAI Hub檢測系統")
    OfficialQAIHubDetector = None

# 嘗試導入fallback檢測系統
try:
    from qaihub_optimize.completely_fixed_detector import CompletelyFixedHackathonDetector
    print("✅ Fallback檢測系統可用")
except ImportError:
    print("⚠️ 無法導入fallback檢測系統，將使用模擬模式")
    CompletelyFixedHackathonDetector = None

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PostureData:
    """姿態數據結構"""
    timestamp: float
    user_id: str
    joint_angles: Dict[str, float]
    balance_score: float
    stability_score: float
    posture_deviation: float
    activity_level: float
    face_detected: bool
    
@dataclass
class RiskAssessment:
    """風險評估結果"""
    fall_risk_score: float
    stability_trend: str
    activity_level: str
    fatigue_indicator: float
    alert_level: str
    recommendations: List[str]
    last_updated: float

class ElderlyBehaviorPredictor:
    """
    🧠 老人行為預測與風險評估系統
    
    功能：
    1. 人臉識別確認用戶身份
    2. 追蹤姿態數據並分析穩定性
    3. 計算跌倒風險評分
    4. 語音互動檢查健康狀況
    5. 生成行為分析報告和預警
    """
    
    def __init__(self, data_dir: str = "elderly_data"):
        """初始化行為預測系統"""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 數據存儲
        self.db_path = os.path.join(data_dir, "elderly_behavior.db")
        self.face_encodings_path = os.path.join(data_dir, "face_encodings.json")
        
        # 姿態追蹤緩存
        self.posture_history = deque(maxlen=1000)  # 最近1000個姿態記錄
        self.user_profiles = {}  # 用戶配置檔案
        self.known_faces = {}  # 已知人臉編碼
        
        # 風險評估參數
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.7,
            'high': 0.9
        }
        
        # 語音系統
        self.tts_engine = None
        self.whisper_model = None
        self.speech_recognizer = None
        
        # 檢測系統
        self.pose_detector = None
        
        # 初始化組件
        self._init_database()
        self._init_face_recognition()
        self._init_voice_systems()
        self._init_pose_detection()
        
        logger.info("🚀 老人行為預測系統初始化完成")
    
    def _init_database(self):
        """初始化SQLite數據庫"""
        try:
            self.db_conn = sqlite3.connect(self.db_path)
            cursor = self.db_conn.cursor()
            
            # 創建姿態數據表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posture_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    user_id TEXT,
                    joint_angles TEXT,
                    balance_score REAL,
                    stability_score REAL,
                    posture_deviation REAL,
                    activity_level REAL,
                    face_detected BOOLEAN
                )
            ''')
            
            # 創建風險評估表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    user_id TEXT,
                    fall_risk_score REAL,
                    stability_trend TEXT,
                    activity_level TEXT,
                    fatigue_indicator REAL,
                    alert_level TEXT,
                    recommendations TEXT
                )
            ''')
            
            # 創建語音記錄表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS voice_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    user_id TEXT,
                    question TEXT,
                    response TEXT,
                    keywords TEXT,
                    sentiment_score REAL
                )
            ''')
            
            self.db_conn.commit()
            logger.info("✅ 數據庫初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 數據庫初始化失敗: {e}")
    
    def _init_face_recognition(self):
        """初始化人臉識別系統（使用官方QAI Hub）"""
        try:
            # 優先初始化官方QAI Hub檢測器
            if OfficialQAIHubDetector:
                self.official_qai_detector = OfficialQAIHubDetector()
                logger.info("✅ 官方QAI Hub檢測器初始化成功")
            else:
                logger.warning("⚠️ 官方QAI Hub檢測器不可用")
                # 嘗試備用檢測器
                try:
                    from qai_hub_unified_detector import QAIHubUnifiedDetector
                    self.qai_detector = QAIHubUnifiedDetector()
                    logger.info("✅ 備用QAI Hub檢測器初始化成功")
                except Exception as e2:
                    logger.error(f"❌ 備用檢測器初始化失敗: {e2}")
                    self.qai_detector = None
            
            # 載入已知人臉編碼
            if os.path.exists(self.face_encodings_path):
                with open(self.face_encodings_path, 'r') as f:
                    face_data = json.load(f)
                    for user_id, encoding_list in face_data.items():
                        self.known_faces[user_id] = np.array(encoding_list)
                logger.info(f"✅ 載入 {len(self.known_faces)} 個已知人臉")
            else:
                logger.info("ℹ️ 尚未有已知人臉數據，請先註冊用戶")
                
        except Exception as e:
            logger.error(f"❌ 人臉識別系統初始化失敗: {e}")
            # 最後備用：使用傳統face_recognition
            try:
                import face_recognition
                self.official_qai_detector = None
                self.qai_detector = None
                logger.info("✅ 使用傳統face_recognition作為備用")
            except ImportError:
                logger.error("❌ 無法導入face_recognition，人臉識別功能不可用")
    
    def _init_voice_systems(self):
        """初始化語音系統"""
        try:
            # TTS 引擎
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)  # 語速
            self.tts_engine.setProperty('volume', 0.8)  # 音量
            
            # Whisper 模型
            self.whisper_model = whisper.load_model("base")
            
            # 語音識別
            self.speech_recognizer = sr.Recognizer()
            
            logger.info("✅ 語音系統初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 語音系統初始化失敗: {e}")
    
    def _init_pose_detection(self):
        """初始化姿態檢測系統（優先使用官方QAI Hub）"""
        try:
            # 檢查是否已有QAI Hub檢測器
            if hasattr(self, 'official_qai_detector') and self.official_qai_detector is not None:
                logger.info("✅ 官方QAI Hub檢測系統已初始化")
                return
                
            # 優先嘗試初始化官方QAI Hub檢測器
            if OfficialQAIHubDetector:
                self.official_qai_detector = OfficialQAIHubDetector()
                logger.info("✅ 官方QAI Hub檢測系統初始化成功")
            elif CompletelyFixedHackathonDetector:
                self.pose_detector = CompletelyFixedHackathonDetector()
                logger.info("✅ 備用檢測系統初始化成功")
            else:
                logger.warning("⚠️ 檢測系統未載入，將使用模擬模式")
                
        except Exception as e:
            logger.error(f"❌ 檢測系統初始化失敗: {e}")
            # 嘗試備用系統
            try:
                if CompletelyFixedHackathonDetector:
                    self.pose_detector = CompletelyFixedHackathonDetector()
                    logger.info("✅ 使用備用檢測系統")
            except Exception as e2:
                logger.error(f"❌ 備用檢測系統也初始化失敗: {e2}")
    
    def register_user(self, user_id: str, name: str, image_path: str, 
                     profile_info: Dict = None) -> bool:
        """
        註冊新用戶並建立人臉編碼（使用QAI Hub）
        
        Args:
            user_id: 用戶唯一標識
            name: 用戶姓名
            image_path: 用戶照片路徑
            profile_info: 額外用戶信息（年齡、健康狀況等）
        """
        try:
            # 載入圖像
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"❌ 無法載入圖像: {image_path}")
                return False
            
            # 優先使用QAI Hub檢測和編碼
            if hasattr(self, 'qai_detector') and self.qai_detector is not None:
                faces = self.qai_detector.detect_faces(image)
                
                if not faces:
                    logger.error(f"❌ QAI Hub在照片中未檢測到人臉: {image_path}")
                    return False
                
                # 使用第一個檢測到的人臉
                face = faces[0]
                bbox = face['bbox']
                face_encoding = self.qai_detector.extract_face_encoding(image, bbox)
                
                if face_encoding is None:
                    logger.error(f"❌ QAI Hub無法提取人臉特徵: {image_path}")
                    return False
                
                self.known_faces[user_id] = face_encoding
                
            else:
                # 備用：使用傳統face_recognition
                import face_recognition
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                face_encodings = face_recognition.face_encodings(rgb_image)
                
                if not face_encodings:
                    logger.error(f"❌ 在照片中未檢測到人臉: {image_path}")
                    return False
                
                # 使用第一個檢測到的人臉
                face_encoding = face_encodings[0]
                self.known_faces[user_id] = face_encoding
            
            # 保存人臉編碼
            face_data = {}
            for uid, encoding in self.known_faces.items():
                face_data[uid] = encoding.tolist()
            
            with open(self.face_encodings_path, 'w') as f:
                json.dump(face_data, f)
            
            # 保存用戶配置
            self.user_profiles[user_id] = {
                'name': name,
                'registered_time': time.time(),
                'profile_info': profile_info or {},
                'last_seen': None
            }
            
            logger.info(f"✅ 用戶 {name} ({user_id}) 註冊成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 用戶註冊失敗: {e}")
            return False
    
    def identify_user(self, frame: np.ndarray) -> Optional[str]:
        """
        從影像中識別用戶（使用官方QAI Hub）
        
        Args:
            frame: 輸入影像 (BGR格式)
            
        Returns:
            識別到的用戶ID，未識別則返回None
        """
        try:
            if not self.known_faces:
                return None
            
            # 轉換為RGB格式
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 優先使用官方QAI Hub檢測
            if hasattr(self, 'official_qai_detector') and self.official_qai_detector is not None:
                face_result = self.official_qai_detector.detect_faces(rgb_frame, raw_output=True)
                
                if face_result.get('success') and face_result.get('num_faces', 0) > 0:
                    # 獲取人臉landmarks座標
                    face_coords = self.official_qai_detector.get_face_landmarks_coordinates(face_result)
                    
                    if face_coords:
                        # 使用face_recognition提取編碼進行識別
                        # (因為QAI Hub主要用於檢測，而不是特徵提取)
                        try:
                            import face_recognition
                            face_locations = face_recognition.face_locations(rgb_frame)
                            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                            
                            for face_encoding in face_encodings:
                                # 與已知人臉比較
                                for user_id, known_encoding in self.known_faces.items():
                                    matches = face_recognition.compare_faces([known_encoding], face_encoding)
                                    if matches[0]:
                                        # 更新最後見到時間
                                        if user_id in self.user_profiles:
                                            self.user_profiles[user_id]['last_seen'] = time.time()
                                        return user_id
                        except ImportError:
                            logger.warning("face_recognition不可用，無法進行人臉識別")
                            
            # 備用：使用QAI Hub檢測器
            elif hasattr(self, 'qai_detector') and self.qai_detector is not None:
                faces = self.qai_detector.detect_faces(frame)
                
                for face in faces:
                    bbox = face['bbox']
                    # 提取人臉特徵編碼
                    face_encoding = self.qai_detector.extract_face_encoding(frame, bbox)
                    
                    if face_encoding is not None:
                        # 與已知人臉比較
                        for user_id, known_encoding in self.known_faces.items():
                            # 計算相似度（使用餘弦相似度）
                            similarity = np.dot(face_encoding, known_encoding) / (
                                np.linalg.norm(face_encoding) * np.linalg.norm(known_encoding)
                            )
                            
                            if similarity > 0.6:  # 相似度閾值
                                # 更新最後見到時間
                                if user_id in self.user_profiles:
                                    self.user_profiles[user_id]['last_seen'] = time.time()
                                return user_id
            else:
                # 最後備用：使用傳統face_recognition
                try:
                    import face_recognition
                    face_locations = face_recognition.face_locations(rgb_frame)
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    
                    for face_encoding in face_encodings:
                        # 與已知人臉比較
                        for user_id, known_encoding in self.known_faces.items():
                            matches = face_recognition.compare_faces([known_encoding], face_encoding)
                            if matches[0]:
                                # 更新最後見到時間
                                if user_id in self.user_profiles:
                                    self.user_profiles[user_id]['last_seen'] = time.time()
                                return user_id
                except ImportError:
                    logger.warning("face_recognition不可用，無法進行人臉識別")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 用戶識別失敗: {e}")
            return None
    
    def analyze_pose_stability(self, landmarks: List[Tuple[float, float]]) -> Dict[str, float]:
        """
        分析姿態穩定性
        
        Args:
            landmarks: MediaPipe 姿態關鍵點
            
        Returns:
            包含各種穩定性指標的字典
        """
        try:
            if not landmarks or len(landmarks) < 33:
                return {'balance_score': 0.0, 'stability_score': 0.0, 'posture_deviation': 1.0}
            
            # 關鍵點索引（MediaPipe Pose）
            nose = landmarks[0] if landmarks[0] else (0, 0)
            left_shoulder = landmarks[11] if landmarks[11] else (0, 0)
            right_shoulder = landmarks[12] if landmarks[12] else (0, 0)
            left_hip = landmarks[23] if landmarks[23] else (0, 0)
            right_hip = landmarks[24] if landmarks[24] else (0, 0)
            left_ankle = landmarks[27] if landmarks[27] else (0, 0)
            right_ankle = landmarks[28] if landmarks[28] else (0, 0)
            
            # 計算身體中線
            shoulder_center = ((left_shoulder[0] + right_shoulder[0]) / 2, 
                             (left_shoulder[1] + right_shoulder[1]) / 2)
            hip_center = ((left_hip[0] + right_hip[0]) / 2, 
                         (left_hip[1] + right_hip[1]) / 2)
            
            # 平衡評分：基於身體中線的垂直度
            if shoulder_center[0] != 0 and hip_center[0] != 0:
                body_angle = math.atan2(
                    hip_center[0] - shoulder_center[0],
                    hip_center[1] - shoulder_center[1]
                )
                balance_score = max(0, 1 - abs(body_angle) / (math.pi / 6))  # 30度內為good
            else:
                balance_score = 0.5
            
            # 穩定性評分：基於雙腳距離和對稱性
            ankle_distance = abs(left_ankle[0] - right_ankle[0]) if left_ankle[0] and right_ankle[0] else 0
            shoulder_distance = abs(left_shoulder[0] - right_shoulder[0]) if left_shoulder[0] and right_shoulder[0] else 0
            
            if shoulder_distance > 0:
                stance_ratio = ankle_distance / shoulder_distance
                stability_score = min(1.0, stance_ratio * 2)  # 腳距與肩距比例
            else:
                stability_score = 0.5
            
            # 姿態偏差：頭部相對於身體中心的位置
            if nose[0] and shoulder_center[0]:
                head_deviation = abs(nose[0] - shoulder_center[0]) / shoulder_distance if shoulder_distance > 0 else 0
                posture_deviation = min(1.0, head_deviation)
            else:
                posture_deviation = 0.5
            
            return {
                'balance_score': float(balance_score),
                'stability_score': float(stability_score),
                'posture_deviation': float(posture_deviation),
                'body_angle': float(body_angle) if 'body_angle' in locals() else 0.0,
                'stance_ratio': float(stance_ratio) if 'stance_ratio' in locals() else 0.0
            }
            
        except Exception as e:
            logger.error(f"❌ 姿態穩定性分析失敗: {e}")
            return {'balance_score': 0.0, 'stability_score': 0.0, 'posture_deviation': 1.0}
    
    def calculate_joint_angles(self, landmarks: List[Tuple[float, float]]) -> Dict[str, float]:
        """
        計算關節角度
        
        Args:
            landmarks: MediaPipe 姿態關鍵點
            
        Returns:
            關節角度字典
        """
        try:
            if not landmarks or len(landmarks) < 33:
                return {}
            
            def calculate_angle(p1, p2, p3):
                """計算三點間的角度"""
                if not all([p1, p2, p3]) or not all([len(p) >= 2 for p in [p1, p2, p3]]):
                    return 0.0
                
                v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
                v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
                
                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                angle = np.arccos(cos_angle)
                return np.degrees(angle)
            
            # 計算主要關節角度
            joint_angles = {}
            
            # 左肘角度 (肩-肘-腕)
            if all([landmarks[11], landmarks[13], landmarks[15]]):
                joint_angles['left_elbow'] = calculate_angle(landmarks[11], landmarks[13], landmarks[15])
            
            # 右肘角度
            if all([landmarks[12], landmarks[14], landmarks[16]]):
                joint_angles['right_elbow'] = calculate_angle(landmarks[12], landmarks[14], landmarks[16])
            
            # 左膝角度 (髖-膝-踝)
            if all([landmarks[23], landmarks[25], landmarks[27]]):
                joint_angles['left_knee'] = calculate_angle(landmarks[23], landmarks[25], landmarks[27])
            
            # 右膝角度
            if all([landmarks[24], landmarks[26], landmarks[28]]):
                joint_angles['right_knee'] = calculate_angle(landmarks[24], landmarks[26], landmarks[28])
            
            # 軀幹角度 (肩中心-髖中心-垂直線)
            if all([landmarks[11], landmarks[12], landmarks[23], landmarks[24]]):
                shoulder_center = ((landmarks[11][0] + landmarks[12][0]) / 2, 
                                 (landmarks[11][1] + landmarks[12][1]) / 2)
                hip_center = ((landmarks[23][0] + landmarks[24][0]) / 2,
                            (landmarks[23][1] + landmarks[24][1]) / 2)
                vertical_point = (hip_center[0], hip_center[1] + 100)
                joint_angles['trunk'] = calculate_angle(shoulder_center, hip_center, vertical_point)
            
            return joint_angles
            
        except Exception as e:
            logger.error(f"❌ 關節角度計算失敗: {e}")
            return {}
    
    def analyze_pose_stability_from_coords(self, pose_coords: List[Tuple[int, int]]) -> Dict[str, float]:
        """
        從座標列表分析姿態穩定性（適配官方QAI Hub輸出）
        
        Args:
            pose_coords: 姿態關鍵點座標列表 [(x, y), ...]
            
        Returns:
            包含各種穩定性指標的字典
        """
        try:
            if not pose_coords or len(pose_coords) < 10:
                return {'balance_score': 0.0, 'stability_score': 0.0, 'posture_deviation': 1.0}
            
            # 將座標轉換為浮點數
            landmarks = [(float(x), float(y)) for x, y in pose_coords]
            
            # 基本身體點（假設MediaPipe Pose順序）
            # 這裡我們取前幾個重要的點
            if len(landmarks) >= 33:
                # 使用標準MediaPipe索引
                return self.analyze_pose_stability(landmarks)
            else:
                # 簡化分析：使用可用的點
                # 計算質心和範圍
                x_coords = [x for x, y in landmarks]
                y_coords = [y for x, y in landmarks]
                
                if not x_coords or not y_coords:
                    return {'balance_score': 0.0, 'stability_score': 0.0, 'posture_deviation': 1.0}
                
                centroid_x = sum(x_coords) / len(x_coords)
                centroid_y = sum(y_coords) / len(y_coords)
                
                # 計算分佈
                x_range = max(x_coords) - min(x_coords) if len(x_coords) > 1 else 0
                y_range = max(y_coords) - min(y_coords) if len(y_coords) > 1 else 0
                
                # 簡化的穩定性評分
                balance_score = 0.8  # 預設值
                stability_score = min(1.0, x_range / (y_range + 1)) if y_range > 0 else 0.5
                posture_deviation = 0.3  # 預設偏差
                
                return {
                    'balance_score': float(balance_score),
                    'stability_score': float(stability_score),
                    'posture_deviation': float(posture_deviation),
                    'body_angle': 0.0,
                    'stance_ratio': float(stability_score)
                }
                
        except Exception as e:
            logger.error(f"❌ 座標穩定性分析失敗: {e}")
            return {'balance_score': 0.0, 'stability_score': 0.0, 'posture_deviation': 1.0}
    
    def calculate_joint_angles_from_coords(self, pose_coords: List[Tuple[int, int]]) -> Dict[str, float]:
        """
        從座標列表計算關節角度（適配官方QAI Hub輸出）
        
        Args:
            pose_coords: 姿態關鍵點座標列表 [(x, y), ...]
            
        Returns:
            關節角度字典
        """
        try:
            if not pose_coords or len(pose_coords) < 10:
                return {}
            
            # 將座標轉換為浮點數
            landmarks = [(float(x), float(y)) for x, y in pose_coords]
            
            if len(landmarks) >= 33:
                # 使用標準方法
                return self.calculate_joint_angles(landmarks)
            else:
                # 簡化的角度計算
                # 假設有基本的身體點
                joint_angles = {}
                
                # 如果有足夠的點，嘗試計算基本角度
                if len(landmarks) >= 6:
                    # 簡化計算：使用前幾個點估算
                    joint_angles['estimated_posture'] = 90.0  # 預設直立姿態
                
                return joint_angles
                
        except Exception as e:
            logger.error(f"❌ 座標角度計算失敗: {e}")
            return {}
    
    def update_posture_history(self, user_id: str, frame: np.ndarray) -> bool:
        """
        更新用戶姿態歷史記錄
        
        Args:
            user_id: 用戶ID
            frame: 當前影像幀
            
        Returns:
            更新是否成功
        """
        try:
            current_time = time.time()
            
            # 姿態檢測
            if self.pose_detector:
                success, landmarks, info = self.pose_detector.detect_pose(frame)
                if not success or not landmarks:
                    return False
            else:
                # 模擬數據
                landmarks = [(100 + i * 10, 100 + i * 5) for i in range(33)]
            
            # 分析穩定性
            stability_metrics = self.analyze_pose_stability(landmarks)
            
            # 計算關節角度
            joint_angles = self.calculate_joint_angles(landmarks)
            
            # 活動水平評估（基於關鍵點變化）
            activity_level = self._calculate_activity_level(landmarks, user_id)
            
            # 創建姿態數據記錄
            posture_data = PostureData(
                timestamp=current_time,
                user_id=user_id,
                joint_angles=joint_angles,
                balance_score=stability_metrics.get('balance_score', 0.0),
                stability_score=stability_metrics.get('stability_score', 0.0),
                posture_deviation=stability_metrics.get('posture_deviation', 0.0),
                activity_level=activity_level,
                face_detected=True  # 已經通過人臉識別確認
            )
            
            # 添加到歷史記錄
            self.posture_history.append(posture_data)
            
            # 保存到數據庫
            self._save_posture_data(posture_data)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 姿態歷史更新失敗: {e}")
            return False
    
    def _calculate_activity_level(self, landmarks: List[Tuple[float, float]], 
                                user_id: str) -> float:
        """計算活動水平"""
        try:
            # 獲取用戶的最近姿態記錄
            recent_data = [data for data in self.posture_history 
                          if data.user_id == user_id and 
                          time.time() - data.timestamp < 30]  # 最近30秒
            
            if len(recent_data) < 2:
                return 0.5  # 默認中等活動水平
            
            # 計算關鍵點位置變化
            movement_sum = 0.0
            for i in range(1, len(recent_data)):
                # 這裡簡化計算，實際應該比較關鍵點位置
                movement_sum += abs(recent_data[i].balance_score - recent_data[i-1].balance_score)
                movement_sum += abs(recent_data[i].stability_score - recent_data[i-1].stability_score)
            
            # 標準化活動水平
            activity_level = min(1.0, movement_sum / len(recent_data))
            return activity_level
            
        except Exception as e:
            logger.error(f"❌ 活動水平計算失敗: {e}")
            return 0.5
    
    def calculate_fall_risk_score(self, user_id: str, time_window: int = 3600) -> float:
        """
        計算跌倒風險評分
        
        Args:
            user_id: 用戶ID
            time_window: 時間窗口（秒），默認1小時
            
        Returns:
            風險評分 (0.0-1.0)
        """
        try:
            current_time = time.time()
            
            # 獲取時間窗口內的數據
            recent_data = [data for data in self.posture_history 
                          if data.user_id == user_id and 
                          current_time - data.timestamp <= time_window]
            
            if not recent_data:
                return 0.5  # 無數據時返回中等風險
            
            # 計算各項指標的平均值
            avg_balance = np.mean([data.balance_score for data in recent_data])
            avg_stability = np.mean([data.stability_score for data in recent_data])
            avg_deviation = np.mean([data.posture_deviation for data in recent_data])
            avg_activity = np.mean([data.activity_level for data in recent_data])
            
            # 計算變異性（不穩定性指標）
            balance_var = np.var([data.balance_score for data in recent_data])
            stability_var = np.var([data.stability_score for data in recent_data])
            
            # 風險評分計算
            risk_factors = {
                'low_balance': max(0, 0.8 - avg_balance),  # 平衡差 -> 風險高
                'low_stability': max(0, 0.8 - avg_stability),  # 穩定性差 -> 風險高
                'high_deviation': min(1.0, avg_deviation),  # 姿態偏差大 -> 風險高
                'low_activity': max(0, 0.3 - avg_activity),  # 活動太少 -> 風險高
                'high_activity': max(0, avg_activity - 0.9),  # 活動過多 -> 風險高
                'balance_instability': min(1.0, balance_var * 10),  # 平衡變異大 -> 風險高
                'stability_instability': min(1.0, stability_var * 10)  # 穩定性變異大 -> 風險高
            }
            
            # 加權計算總風險
            weights = {
                'low_balance': 0.25,
                'low_stability': 0.25,
                'high_deviation': 0.15,
                'low_activity': 0.10,
                'high_activity': 0.10,
                'balance_instability': 0.10,
                'stability_instability': 0.05
            }
            
            total_risk = sum(risk_factors[factor] * weights[factor] 
                           for factor in risk_factors)
            
            # 時間趨勢分析
            if len(recent_data) >= 10:
                recent_half = recent_data[len(recent_data)//2:]
                earlier_half = recent_data[:len(recent_data)//2]
                
                recent_avg_balance = np.mean([data.balance_score for data in recent_half])
                earlier_avg_balance = np.mean([data.balance_score for data in earlier_half])
                
                if recent_avg_balance < earlier_avg_balance - 0.1:
                    total_risk += 0.1  # 平衡能力下降趨勢
            
            return min(1.0, total_risk)
            
        except Exception as e:
            logger.error(f"❌ 風險評分計算失敗: {e}")
            return 0.5
    
    def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """獲取用戶儀表板數據"""
        try:
            # 基本信息
            user_info = self.user_profiles.get(user_id, {})
            
            # 當前風險評分
            current_risk = self.calculate_fall_risk_score(user_id)
            
            # 最近活動
            recent_data = [data for data in self.posture_history 
                          if data.user_id == user_id and 
                          time.time() - data.timestamp <= 3600]  # 最近1小時
            
            return {
                'user_info': user_info,
                'current_risk_score': current_risk,
                'recent_activity_count': len(recent_data),
                'last_seen': user_info.get('last_seen'),
                'monitoring_status': 'active' if recent_data else 'inactive'
            }
            
        except Exception as e:
            logger.error(f"❌ 儀表板數據獲取失敗: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def generate_behavioral_summary(self, user_id: str) -> Dict[str, Any]:
        """生成行為分析摘要"""
        try:
            # 使用正確的數據庫連接屬性
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT * FROM posture_data 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            """, (user_id,))
            
            recent_data = cursor.fetchall()
            
            if not recent_data:
                return {
                    'status': 'success',
                    'total_records': 0,
                    'message': '暫無足夠數據進行分析'
                }
            
            # 計算平均指標
            avg_balance = sum(row[4] for row in recent_data) / len(recent_data)  # balance_score是第4列
            avg_stability = sum(row[5] for row in recent_data) / len(recent_data)  # stability_score是第5列
            avg_posture_deviation = sum(row[6] for row in recent_data) / len(recent_data)  # posture_deviation是第6列
            
            return {
                'status': 'success',
                'total_records': len(recent_data),
                'average_metrics': {
                    'balance_score': avg_balance,
                    'stability_score': avg_stability,
                    'posture_deviation': avg_posture_deviation
                },
                'summary_text': f"""
                📊 行為分析摘要 (近{len(recent_data)}次記錄):
                • 平均平衡分數: {avg_balance:.2f}
                • 平均穩定性: {avg_stability:.2f}
                • 平均姿態偏差: {avg_posture_deviation:.2f}
                
                {"⚠️ 建議多加注意身體平衡" if avg_posture_deviation > 0.6 else "✅ 整體狀況良好"}
                """
            }
            
        except Exception as e:
            logger.error(f"❌ 生成行為摘要失敗: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def ask_user_checkin_question(self, user_id: str = None, custom_question: str = None, speak: bool = False) -> str:
        """詢問用戶健康狀況。

        Args:
            user_id: optional user id for personalized question
            custom_question: override question text
            speak: if True, use internal TTS to speak the question; otherwise only return the text

        Returns:
            The question string.
        """
        try:
            if custom_question:
                question = custom_question
            else:
                questions = [
                    "您今天感覺如何？",
                    "有沒有感到頭暈或不平衡？",
                    "最近有跌倒的經歷嗎？",
                    "現在有任何不適症狀嗎？"
                ]
                import random
                question = random.choice(questions)

            # Only speak if caller explicitly requests it
            if speak and self.tts_engine:
                try:
                    self.tts_engine.say(question)
                    self.tts_engine.runAndWait()
                except Exception:
                    logger.exception('TTS playback failed')

            # Return question text (no blocking recording or recognition here)
            return question

        except Exception as e:
            logger.error(f"❌ 語音詢問失敗: {e}")
            return "語音詢問功能暫時不可用"
    
    def interpret_user_reply(self, text_input: str = None, audio_input = None) -> Dict[str, Any]:
        """解釋用戶回覆並評估健康狀況"""
        try:
            if not text_input and not audio_input:
                return {'status': 'error', 'message': '沒有輸入數據'}
            
            # 如果有音頻輸入，轉換為文字（這裡簡化處理）
            response_text = text_input if text_input else "無法識別音頻"
            
            # 簡單的情感和健康狀況分析
            positive_keywords = ['好', '很好', '不錯', '健康', '正常', '舒服']
            negative_keywords = ['不好', '糟糕', '痛', '暈', '跌倒', '虛弱', '不舒服', '頭暈']
            alert_keywords = ['跌倒', '暈倒', '急救', '幫助', '不能動']
            
            sentiment_score = 0.5  # 中性
            alert_level = 'normal'
            
            # 計算情感評分
            for keyword in positive_keywords:
                if keyword in response_text:
                    sentiment_score += 0.1
            
            for keyword in negative_keywords:
                if keyword in response_text:
                    sentiment_score -= 0.1
            
            # 檢查警報關鍵詞
            for keyword in alert_keywords:
                if keyword in response_text:
                    alert_level = 'high'
                    break
            else:
                # 如果沒有高警報關鍵詞，檢查中度警報
                if any(keyword in response_text for keyword in negative_keywords):
                    alert_level = 'medium'
            
            # 確保評分在 0-1 範圍內
            sentiment_score = max(0, min(1, sentiment_score))
            
            return {
                'status': 'success',
                'response_text': response_text,
                'sentiment_score': sentiment_score,
                'alert_level': alert_level,
                'keywords_detected': [kw for kw in positive_keywords + negative_keywords if kw in response_text]
            }
            
        except Exception as e:
            logger.error(f"❌ 用戶回覆解釋失敗: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def process_user_interaction(self, user_id: str, frame: np.ndarray) -> Dict[str, Any]:
        """
        處理用戶互動（使用官方QAI Hub統一檢測）
        
        Args:
            user_id: 用戶ID
            frame: 輸入影像（BGR格式）
            
        Returns:
            包含檢測結果和分析的字典
        """
        try:
            result = {
                'user_id': user_id,
                'timestamp': time.time(),
                'face_detected': False,
                'pose_analysis': {},
                'risk_assessment': {},
                'alert_triggered': False
            }
            
            # 轉換為RGB格式
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 使用官方QAI Hub統一檢測
            if hasattr(self, 'official_qai_detector') and self.official_qai_detector is not None:
                detection_results = self.official_qai_detector.unified_detection(rgb_frame)
                
                # 處理人臉檢測結果
                if detection_results.get('success') and detection_results['faces'].get('num_faces', 0) > 0:
                    result['face_detected'] = True
                
                # 處理姿態檢測結果
                pose_result = detection_results['poses']
                if pose_result.get('success') and pose_result.get('num_poses', 0) > 0:
                    # 獲取姿態landmarks座標
                    pose_coords = self.official_qai_detector.get_pose_landmarks_coordinates(pose_result)
                    
                    if pose_coords:
                        # 分析姿態穩定性
                        stability_metrics = self.analyze_pose_stability_from_coords(pose_coords)
                        result['pose_analysis'] = stability_metrics
                        
                        # 創建姿態數據記錄
                        posture_data = PostureData(
                            timestamp=time.time(),
                            user_id=user_id,
                            joint_angles=self.calculate_joint_angles_from_coords(pose_coords),
                            balance_score=stability_metrics['balance_score'],
                            stability_score=stability_metrics['stability_score'],
                            posture_deviation=stability_metrics['posture_deviation'],
                            activity_level=0.5,  # 預設活動水平
                            face_detected=result['face_detected']
                        )
                        
                        # 添加到歷史記錄
                        self.posture_history.append(posture_data)
                        
                        # 風險評估
                        risk_score = self.calculate_fall_risk_score(user_id)
                        result['risk_assessment'] = {
                            'score': risk_score,
                            'level': 'high' if risk_score > 0.7 else 'medium' if risk_score > 0.4 else 'low'
                        }
                        
                        # 檢查是否需要觸發警報
                        if risk_score > 0.7:
                            result['alert_triggered'] = True
                            logger.warning(f"⚠️ 用戶 {user_id} 風險評分過高: {risk_score:.2f}")
                
                result['processing_info'] = {
                    'method': 'official_qai_hub',
                    'faces': detection_results['faces'].get('num_faces', 0),
                    'poses': detection_results['poses'].get('num_poses', 0),
                    'hands': detection_results['hands'].get('num_hands', 0)
                }
                
            # 備用：使用QAI Hub檢測器
            elif hasattr(self, 'qai_detector') and self.qai_detector is not None:
                detection_results = self.qai_detector.unified_detection(frame)
                
                # 處理人臉檢測結果
                if detection_results['faces']:
                    result['face_detected'] = True
                
                # 處理姿態檢測結果
                if detection_results['pose']['success']:
                    landmarks = detection_results['pose']['landmarks']
                    
                    # 分析姿態穩定性
                    stability_metrics = self.analyze_pose_stability(landmarks)
                    result['pose_analysis'] = stability_metrics
                    
                    # 創建姿態數據記錄
                    posture_data = PostureData(
                        timestamp=time.time(),
                        user_id=user_id,
                        joint_angles=self.calculate_joint_angles(landmarks),
                        balance_score=stability_metrics['balance_score'],
                        stability_score=stability_metrics['stability_score'],
                        posture_deviation=stability_metrics['posture_deviation'],
                        activity_level=0.5,  # 預設活動水平
                        face_detected=result['face_detected']
                    )
                    
                    # 添加到歷史記錄
                    self.posture_history.append(posture_data)
                    
                    # 風險評估
                    risk_score = self.calculate_fall_risk_score(user_id)
                    result['risk_assessment'] = {
                        'score': risk_score,
                        'level': 'high' if risk_score > 0.7 else 'medium' if risk_score > 0.4 else 'low'
                    }
                    
                    # 檢查是否需要觸發警報
                    if risk_score > 0.7:
                        result['alert_triggered'] = True
                        logger.warning(f"⚠️ 用戶 {user_id} 風險評分過高: {risk_score:.2f}")
                
                result['processing_info'] = detection_results['summary']
                
            else:
                # 備用：使用原有檢測系統
                if hasattr(self, 'pose_detector') and self.pose_detector:
                    # 這裡可以調用原有的檢測邏輯
                    pass
                
                result['pose_analysis'] = {'error': '檢測系統不可用'}
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 用戶互動處理失敗: {e}")
            return {
                'user_id': user_id,
                'timestamp': time.time(),
                'error': str(e),
                'alert_triggered': False
            }


# 示例使用代碼
if __name__ == "__main__":
    # 初始化系統
    predictor = ElderlyBehaviorPredictor()
    
    # 示例：註冊用戶
    # predictor.register_user("elderly_001", "張奶奶", "user_photos/zhang_grandma.jpg", 
    #                        {"age": 75, "medical_conditions": ["高血壓"]})
    
    # 示例：即時監測
    cap = cv2.VideoCapture(0)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 識別用戶
            user_id = predictor.identify_user(frame)
            
            if user_id:
                # 處理用戶互動
                result = predictor.process_user_interaction(user_id, frame)
                
                # 顯示結果
                cv2.putText(frame, f"User: {user_id}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Risk: {result.get('risk_assessment', {}).get('score', 0):.2f}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.imshow('Elderly Behavior Predictor', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
