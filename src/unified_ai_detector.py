#!/usr/bin/env python3
"""
🧠 統一AI檢測模塊
支持Mac和Snapdragon平台的無縫切換
"""

import os
import cv2
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
import json
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedAIDetector:
    """統一AI檢測器 - 跨平台兼容"""
    
    def __init__(self, config_path: str = "cross_platform_config.json"):
        """初始化統一檢測器"""
        self.config = self._load_config(config_path)
        self.platform_info = self._detect_platform()
        self.platform_config = self._get_platform_config()
        
        # 檢測能力
        self.onnx_available = False
        self.qai_hub_available = False
        self.mediapipe_available = False
        
        # 模型和會話
        self.models = {}
        self.sessions = {}
        
        # 初始化系統
        self._initialize_system()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ 配置載入失敗: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            "platform_configs": {
                "fallback": {
                    "batch_size": 1,
                    "num_threads": 2,
                    "providers": ["CPUExecutionProvider"]
                }
            }
        }
    
    def _detect_platform(self) -> Dict[str, str]:
        """檢測當前平台"""
        import platform
        
        system = platform.system().lower()
        machine = platform.machine().lower()
        processor = platform.processor().lower()
        
        platform_info = {
            "system": system,
            "machine": machine,
            "processor": processor
        }
        
        # 判斷平台類型
        if system == "darwin" and ("arm" in machine or "arm64" in machine):
            platform_info["type"] = "mac_apple_silicon"
            platform_info["ai_accelerator"] = "apple_neural_engine"
        elif "snapdragon" in processor.lower() or "qualcomm" in processor.lower():
            platform_info["type"] = "snapdragon_x_elite"
            platform_info["ai_accelerator"] = "hexagon_npu"
        elif system == "windows" and ("arm" in machine or "aarch64" in machine):
            platform_info["type"] = "snapdragon_x_elite"  # Windows ARM可能是Snapdragon
            platform_info["ai_accelerator"] = "hexagon_npu"
        else:
            platform_info["type"] = "fallback"
            platform_info["ai_accelerator"] = "cpu_generic"
        
        return platform_info
    
    def _get_platform_config(self) -> Dict[str, Any]:
        """獲取當前平台配置"""
        platform_type = self.platform_info["type"]
        configs = self.config.get("platform_configs", {})
        return configs.get(platform_type, configs.get("fallback", {}))
    
    def _initialize_system(self):
        """初始化檢測系統"""
        logger.info("🚀 初始化統一AI檢測系統...")
        logger.info(f"🖥️ 檢測平台: {self.platform_info['type']}")
        logger.info(f"🧠 AI加速器: {self.platform_info['ai_accelerator']}")
        
        # 檢查依賴項
        self._check_dependencies()
        
        # 初始化ONNX Runtime
        if self.onnx_available:
            self._initialize_onnx_runtime()
        
        # 初始化QAI Hub
        if self.qai_hub_available:
            self._initialize_qai_hub()
        
        # 初始化MediaPipe後備
        if self.mediapipe_available:
            self._initialize_mediapipe()
    
    def _check_dependencies(self):
        """檢查依賴項可用性"""
        # 檢查ONNX Runtime
        try:
            import onnxruntime as ort
            self.onnx_available = True
            logger.info("✅ ONNX Runtime可用")
        except ImportError:
            logger.warning("⚠️ ONNX Runtime不可用")
        
        # 檢查QAI Hub
        try:
            import qai_hub as hub
            api_token = os.getenv('QAI_HUB_API_TOKEN')
            if api_token:
                self.qai_hub_available = True
                logger.info("✅ QAI Hub可用")
            else:
                logger.warning("⚠️ QAI Hub API Token未設置")
        except ImportError:
            logger.warning("⚠️ QAI Hub SDK不可用")
        
        # 檢查MediaPipe
        try:
            import mediapipe as mp
            self.mediapipe_available = True
            logger.info("✅ MediaPipe可用")
        except ImportError:
            logger.warning("⚠️ MediaPipe不可用")
    
    def _initialize_onnx_runtime(self):
        """初始化ONNX Runtime"""
        try:
            import onnxruntime as ort
            
            # 獲取可用提供商
            available_providers = ort.get_available_providers()
            platform_providers = self.platform_config.get("providers", ["CPUExecutionProvider"])
            
            # 選擇提供商
            self.providers = [p for p in platform_providers if p in available_providers]
            if not self.providers:
                self.providers = ["CPUExecutionProvider"]
            
            logger.info(f"📋 ONNX提供商: {self.providers}")
            
            # 創建會話選項
            self.session_options = ort.SessionOptions()
            self.session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self.session_options.enable_cpu_mem_arena = True
            self.session_options.enable_mem_pattern = True
            
            num_threads = self.platform_config.get("num_threads", 4)
            self.session_options.intra_op_num_threads = num_threads
            
            logger.info("✅ ONNX Runtime初始化完成")
            
        except Exception as e:
            logger.error(f"❌ ONNX Runtime初始化失敗: {e}")
            self.onnx_available = False
    
    def _initialize_qai_hub(self):
        """初始化QAI Hub"""
        try:
            import qai_hub as hub
            
            # 獲取設備列表
            self.devices = hub.get_devices()
            logger.info(f"☁️ QAI Hub設備數量: {len(self.devices)}")
            
            # 選擇目標設備
            preferred_devices = self.config.get("qai_hub_config", {}).get("preferred_devices", [])
            self.target_device = None
            
            for preferred in preferred_devices:
                for device in self.devices:
                    if preferred.lower() in device.name.lower():
                        self.target_device = device
                        logger.info(f"🎯 選擇設備: {device.name}")
                        break
                if self.target_device:
                    break
            
            if not self.target_device and self.devices:
                self.target_device = self.devices[0]
                logger.info(f"🎯 使用預設設備: {self.target_device.name}")
            
            logger.info("✅ QAI Hub初始化完成")
            
        except Exception as e:
            logger.error(f"❌ QAI Hub初始化失敗: {e}")
            self.qai_hub_available = False
    
    def _initialize_mediapipe(self):
        """初始化MediaPipe後備系統"""
        try:
            import mediapipe as mp
            
            # 初始化MediaPipe組件
            self.mp_face_detection = mp.solutions.face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.5)
            
            self.mp_pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5)
            
            self.mp_hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5)
            
            logger.info("✅ MediaPipe後備系統初始化完成")
            
        except Exception as e:
            logger.error(f"❌ MediaPipe初始化失敗: {e}")
            self.mediapipe_available = False
    
    def load_onnx_model(self, model_name: str, model_path: str) -> bool:
        """載入ONNX模型"""
        if not self.onnx_available:
            logger.warning("⚠️ ONNX Runtime不可用，無法載入模型")
            return False
        
        try:
            import onnxruntime as ort
            
            if not os.path.exists(model_path):
                logger.warning(f"⚠️ 模型文件不存在: {model_path}")
                return False
            
            session = ort.InferenceSession(
                model_path,
                sess_options=self.session_options,
                providers=self.providers
            )
            
            self.sessions[model_name] = session
            
            # 記錄模型信息
            input_info = session.get_inputs()[0]
            output_info = session.get_outputs()[0]
            
            logger.info(f"✅ 載入模型 {model_name}")
            logger.info(f"   輸入: {input_info.name} {input_info.shape}")
            logger.info(f"   輸出: {output_info.name} {output_info.shape}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型載入失敗 {model_name}: {e}")
            return False
    
    def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """人臉檢測"""
        results = []
        
        # 嘗試ONNX模型
        if "face_detection" in self.sessions:
            try:
                results = self._onnx_face_detection(image)
                logger.debug("🎯 使用ONNX人臉檢測")
            except Exception as e:
                logger.warning(f"⚠️ ONNX人臉檢測失敗: {e}")
        
        # 後備MediaPipe
        if not results and self.mediapipe_available:
            try:
                results = self._mediapipe_face_detection(image)
                logger.debug("🎯 使用MediaPipe人臉檢測")
            except Exception as e:
                logger.warning(f"⚠️ MediaPipe人臉檢測失敗: {e}")
        
        return results
    
    def detect_pose(self, image: np.ndarray) -> Dict[str, Any]:
        """姿態檢測"""
        result = None
        
        # 嘗試ONNX模型
        if "pose_estimation" in self.sessions:
            try:
                result = self._onnx_pose_detection(image)
                logger.debug("🎯 使用ONNX姿態檢測")
            except Exception as e:
                logger.warning(f"⚠️ ONNX姿態檢測失敗: {e}")
        
        # 後備MediaPipe
        if not result and self.mediapipe_available:
            try:
                result = self._mediapipe_pose_detection(image)
                logger.debug("🎯 使用MediaPipe姿態檢測")
            except Exception as e:
                logger.warning(f"⚠️ MediaPipe姿態檢測失敗: {e}")
        
        return result or {}
    
    def detect_hands(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """手部檢測"""
        results = []
        
        # 嘗試ONNX模型
        if "hand_detection" in self.sessions:
            try:
                results = self._onnx_hand_detection(image)
                logger.debug("🎯 使用ONNX手部檢測")
            except Exception as e:
                logger.warning(f"⚠️ ONNX手部檢測失敗: {e}")
        
        # 後備MediaPipe
        if not results and self.mediapipe_available:
            try:
                results = self._mediapipe_hand_detection(image)
                logger.debug("🎯 使用MediaPipe手部檢測")
            except Exception as e:
                logger.warning(f"⚠️ MediaPipe手部檢測失敗: {e}")
        
        return results
    
    def _onnx_face_detection(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """ONNX人臉檢測實現"""
        session = self.sessions["face_detection"]
        
        # 預處理
        input_shape = self.platform_config.get("input_shape", [1, 3, 224, 224])
        processed_image = self._preprocess_image(image, input_shape[2:])
        
        # 推理
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: processed_image})
        
        # 後處理
        return self._postprocess_face_detection(outputs, image.shape)
    
    def _onnx_pose_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """ONNX姿態檢測實現"""
        session = self.sessions["pose_estimation"]
        
        # 預處理
        input_shape = self.platform_config.get("input_shape", [1, 3, 224, 224])
        processed_image = self._preprocess_image(image, input_shape[2:])
        
        # 推理
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: processed_image})
        
        # 後處理
        return self._postprocess_pose_detection(outputs, image.shape)
    
    def _onnx_hand_detection(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """ONNX手部檢測實現"""
        session = self.sessions["hand_detection"]
        
        # 預處理
        input_shape = self.platform_config.get("input_shape", [1, 3, 224, 224])
        processed_image = self._preprocess_image(image, input_shape[2:])
        
        # 推理
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: processed_image})
        
        # 後處理
        return self._postprocess_hand_detection(outputs, image.shape)
    
    def _mediapipe_face_detection(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """MediaPipe人臉檢測實現"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.mp_face_detection.process(rgb_image)
        
        faces = []
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                h, w = image.shape[:2]
                
                faces.append({
                    "bbox": [
                        int(bbox.xmin * w),
                        int(bbox.ymin * h),
                        int(bbox.width * w),
                        int(bbox.height * h)
                    ],
                    "confidence": detection.score[0],
                    "landmarks": []
                })
        
        return faces
    
    def _mediapipe_pose_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """MediaPipe姿態檢測實現"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.mp_pose.process(rgb_image)
        
        if results.pose_landmarks:
            landmarks = []
            for landmark in results.pose_landmarks.landmark:
                landmarks.append({
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z,
                    "visibility": landmark.visibility
                })
            
            return {
                "landmarks": landmarks,
                "confidence": 0.8  # MediaPipe沒有提供整體置信度
            }
        
        return {}
    
    def _mediapipe_hand_detection(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """MediaPipe手部檢測實現"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.mp_hands.process(rgb_image)
        
        hands = []
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                landmarks = []
                for landmark in hand_landmarks.landmark:
                    landmarks.append({
                        "x": landmark.x,
                        "y": landmark.y,
                        "z": landmark.z
                    })
                
                hands.append({
                    "landmarks": landmarks,
                    "confidence": 0.8
                })
        
        return hands
    
    def _preprocess_image(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """圖像預處理"""
        # 調整大小
        resized = cv2.resize(image, target_size)
        
        # 轉換為RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # 正規化
        normalized = rgb.astype(np.float32) / 255.0
        
        # 轉換維度 (H, W, C) -> (1, C, H, W)
        transposed = np.transpose(normalized, (2, 0, 1))
        batched = np.expand_dims(transposed, axis=0)
        
        return batched
    
    def _postprocess_face_detection(self, outputs: List[np.ndarray], image_shape: Tuple[int, int, int]) -> List[Dict[str, Any]]:
        """人臉檢測後處理"""
        # 這裡需要根據實際的ONNX模型輸出格式來實現
        # 目前返回空列表作為占位符
        return []
    
    def _postprocess_pose_detection(self, outputs: List[np.ndarray], image_shape: Tuple[int, int, int]) -> Dict[str, Any]:
        """姿態檢測後處理"""
        # 這裡需要根據實際的ONNX模型輸出格式來實現
        # 目前返回空字典作為占位符
        return {}
    
    def _postprocess_hand_detection(self, outputs: List[np.ndarray], image_shape: Tuple[int, int, int]) -> List[Dict[str, Any]]:
        """手部檢測後處理"""
        # 這裡需要根據實際的ONNX模型輸出格式來實現
        # 目前返回空列表作為占位符
        return []
    
    def analyze_fall_risk(self, image: np.ndarray) -> Dict[str, Any]:
        """跌倒風險分析"""
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "platform": self.platform_info["type"],
            "fall_risk_score": 0.0,
            "alerts": [],
            "detections": {}
        }
        
        try:
            # 人臉檢測
            faces = self.detect_faces(image)
            analysis_result["detections"]["faces"] = faces
            
            # 姿態檢測
            pose = self.detect_pose(image)
            analysis_result["detections"]["pose"] = pose
            
            # 手部檢測
            hands = self.detect_hands(image)
            analysis_result["detections"]["hands"] = hands
            
            # 跌倒風險評估
            risk_score = self._calculate_fall_risk(faces, pose, hands)
            analysis_result["fall_risk_score"] = risk_score
            
            # 生成警報
            if risk_score > 0.8:
                analysis_result["alerts"].append("高跌倒風險")
            elif risk_score > 0.6:
                analysis_result["alerts"].append("中等跌倒風險")
            
            logger.debug(f"📊 風險分數: {risk_score:.2f}")
            
        except Exception as e:
            logger.error(f"❌ 跌倒風險分析失敗: {e}")
            analysis_result["error"] = str(e)
        
        return analysis_result
    
    def _calculate_fall_risk(self, faces: List[Dict], pose: Dict, hands: List[Dict]) -> float:
        """計算跌倒風險分數"""
        risk_factors = []
        
        # 人臉檢測因子
        if not faces:
            risk_factors.append(0.3)  # 未檢測到人臉
        
        # 姿態分析因子
        if pose and "landmarks" in pose:
            # 這裡可以添加具體的姿態分析邏輯
            # 例如檢查身體傾斜度、平衡狀態等
            pass
        else:
            risk_factors.append(0.2)  # 未檢測到姿態
        
        # 手部檢測因子
        if len(hands) == 0:
            risk_factors.append(0.1)  # 未檢測到手部
        
        # 計算總體風險分數
        base_score = sum(risk_factors)
        return min(base_score, 1.0)
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            "platform": self.platform_info,
            "capabilities": {
                "onnx_runtime": self.onnx_available,
                "qai_hub": self.qai_hub_available,
                "mediapipe": self.mediapipe_available
            },
            "loaded_models": list(self.sessions.keys()),
            "providers": getattr(self, "providers", []),
            "target_device": getattr(self, "target_device", {}).name if hasattr(getattr(self, "target_device", {}), "name") else None
        }

def main():
    """主函數：測試統一檢測器"""
    print("🧠 統一AI檢測器測試")
    print("=" * 50)
    
    try:
        # 初始化檢測器
        detector = UnifiedAIDetector()
        
        # 顯示系統狀態
        status = detector.get_system_status()
        
        print("\n📊 系統狀態:")
        print(f"   平台: {status['platform']['type']}")
        print(f"   AI加速器: {status['platform']['ai_accelerator']}")
        print(f"   ONNX Runtime: {'✅' if status['capabilities']['onnx_runtime'] else '❌'}")
        print(f"   QAI Hub: {'✅' if status['capabilities']['qai_hub'] else '❌'}")
        print(f"   MediaPipe: {'✅' if status['capabilities']['mediapipe'] else '❌'}")
        
        if status['providers']:
            print(f"   執行提供商: {', '.join(status['providers'])}")
        
        if status['target_device']:
            print(f"   目標設備: {status['target_device']}")
        
        # 測試圖像檢測
        test_image_path = "andy.jpg"
        if os.path.exists(test_image_path):
            print(f"\n🖼️ 測試圖像: {test_image_path}")
            
            image = cv2.imread(test_image_path)
            if image is not None:
                # 執行跌倒風險分析
                analysis = detector.analyze_fall_risk(image)
                
                print(f"   風險分數: {analysis['fall_risk_score']:.2f}")
                print(f"   警報: {', '.join(analysis['alerts']) if analysis['alerts'] else '無'}")
                print(f"   檢測結果: {len(analysis['detections'])} 項")
            else:
                print("   ❌ 圖像載入失敗")
        else:
            print("   ⚠️ 測試圖像不存在")
        
        print("\n✅ 統一檢測器測試完成！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
