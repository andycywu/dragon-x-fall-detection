
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
import face_recognition
import pyttsx3
import speech_recognition as sr
import whisper
import math
from collections import deque, defaultdict
import warnings
warnings.filterwarnings("ignore")

# 嘗試導入我們的檢測系統
try:
    from completely_fixed_detector import CompletelyFixedHackathonDetector
except ImportError:
    print("⚠️ 無法導入檢測系統，將使用模擬模式")
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
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
            
            conn.commit()
            conn.close()
            logger.info("✅ 數據庫初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 數據庫初始化失敗: {e}")
    
    def _init_face_recognition(self):
        """初始化人臉識別系統"""
        try:
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
        """初始化姿態檢測系統"""
        try:
            if CompletelyFixedHackathonDetector:
                self.pose_detector = CompletelyFixedHackathonDetector()
                logger.info("✅ 姿態檢測系統初始化成功")
            else:
                logger.warning("⚠️ 姿態檢測系統未載入，將使用模擬模式")
                
        except Exception as e:
            logger.error(f"❌ 姿態檢測系統初始化失敗: {e}")
    
    def register_user(self, user_id: str, name: str, image_path: str, 
                     profile_info: Dict = None) -> bool:
        """
        註冊新用戶並建立人臉編碼
        
        Args:
            user_id: 用戶唯一標識
            name: 用戶姓名
            image_path: 用戶照片路徑
            profile_info: 額外用戶信息（年齡、健康狀況等）
        """
        try:
            # 載入並編碼人臉
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            
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
        從影像中識別用戶
        
        Args:
            frame: 輸入影像
            
        Returns:
            識別到的用戶ID，未識別則返回None
        """
        try:
            if not self.known_faces:
                return None
            
            # 檢測人臉
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 用戶識別失敗: {e}")
            return None
