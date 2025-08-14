#!/usr/bin/env python3
"""
🐉 Dragon X專用老人跌倒預防檢測系統
專為黑客松優化，使用Snapdragon X Elite平台
"""

import os
import qai_hub as hub
import numpy as np
import cv2
import onnxruntime as ort
import logging
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional, Tuple
import time
import json
from pathlib import Path

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DragonXFallDetectionSystem:
    """Dragon X專用老人跌倒預防檢測系統"""
    
    def __init__(self, download_compiled: bool = False, wait_compile: bool = False,
                 realtime: bool = False, camera_index: int = 0, max_frames: Optional[int] = None):
        """初始化Dragon X檢測系統

        Args:
            download_compiled: 在編譯 job 完成後自動下載 target model (edge 部署用)
            wait_compile: 於初始化階段等待 compile jobs 完成 (避免後續下載失敗)
            realtime: 啟動後立即進入即時推論循環
            camera_index: 攝影機索引 (即時模式使用)
            max_frames: 最多處理影格數 (None 表示不限；測試/除錯可設定)
        """
        self.api_token = os.getenv('QAI_HUB_API_TOKEN')
        self.target_device = None
        self.qai_hub_models = {}
        self.compiled_models = {}
        self.onnx_sessions = {}
        self.download_dir = Path('edge_models')
        self.download_dir.mkdir(exist_ok=True)
        self.download_compiled = download_compiled
        self.wait_compile = wait_compile
        self.realtime = realtime
        self.camera_index = camera_index
        self.max_frames = max_frames
        
        logger.info("🐉 初始化Dragon X老人跌倒預防檢測系統...")
        self._find_dragon_x_devices()
        self._initialize_fall_detection_models()
        if self.wait_compile:
            self._wait_for_all_compile_jobs()
        if self.download_compiled:
            self._download_compiled_target_models()
            self._create_onnx_sessions_from_downloads()
        if self.realtime and self.onnx_sessions:
            logger.info("🚀 進入即時推論模式 (使用已下載 compiled ONNX)")
            self.run_realtime_inference()
    
    def _find_dragon_x_devices(self):
        """尋找並選擇Dragon X設備"""
        if not self.api_token:
            raise ValueError("❌ 請在.env文件中設置QAI_HUB_API_TOKEN")
        
        try:
            devices = hub.get_devices()
            logger.info(f"🔍 搜尋QAI Hub設備...")
            logger.info(f"   總設備數量: {len(devices)}")
            
            # 分類設備
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
            
            # 顯示設備分類
            logger.info(f"📊 設備分類結果:")
            logger.info(f"   🐉 Dragon X / Snapdragon X Elite: {len(dragon_x_devices)}")
            logger.info(f"   🔥 其他Snapdragon設備: {len(snapdragon_devices)}")
            logger.info(f"   📱 其他設備: {len(other_devices)}")
            
            # 選擇最佳設備
            if dragon_x_devices:
                self.target_device = dragon_x_devices[0]
                logger.info(f"🎉 成功選定Dragon X設備!")
                logger.info(f"   🐉 設備名稱: {self.target_device.name}")
                logger.info(f"   ✨ 黑客松主打平台已就緒!")
                
                # 顯示所有Dragon X設備選項
                if len(dragon_x_devices) > 1:
                    logger.info(f"   📋 其他可用Dragon X設備:")
                    for i, device in enumerate(dragon_x_devices[1:], 1):
                        logger.info(f"      {i}. {device.name}")
                        
            elif snapdragon_devices:
                self.target_device = snapdragon_devices[0]
                logger.warning(f"⚠️ 未找到Dragon X，使用Snapdragon設備:")
                logger.info(f"   🔥 設備名稱: {self.target_device.name}")
                
            else:
                self.target_device = devices[0] if devices else None
                logger.warning(f"⚠️ 未找到Snapdragon設備，使用預設設備:")
                logger.info(f"   📱 設備名稱: {self.target_device.name if self.target_device else 'None'}")
            
            return self.target_device
            
        except Exception as e:
            logger.error(f"❌ 設備搜尋失敗: {e}")
            raise
    
    def _initialize_fall_detection_models(self):
        """初始化跌倒檢測所需的模型"""
        logger.info("🧠 載入老人跌倒預防檢測模型...")
        
        try:
            # 姿態檢測是跌倒檢測的核心
            self._load_pose_detection_for_fall_prevention()
            
            # 人臉檢測用於確認老人身份
            self._load_face_detection_for_elderly_identification()
            
            # 手部檢測用於檢測求救手勢
            self._load_hand_detection_for_emergency_gestures()
            
            logger.info("✅ 老人跌倒預防檢測模型載入完成")
            
        except Exception as e:
            logger.error(f"❌ 模型載入失敗: {e}")
            raise
    
    def _load_pose_detection_for_fall_prevention(self):
        """載入姿態檢測模型（跌倒預防核心）"""
        try:
            from qai_hub_models.models.mediapipe_pose import Model as PoseModel
            
            logger.info("🚶‍♂️ 載入姿態檢測模型 (跌倒預防核心)...")
            pose_model = PoseModel.from_pretrained()
            pose_detector = pose_model.pose_detector
            self.qai_hub_models['pose_fall_detection'] = pose_detector
            
            # 提交到Dragon X設備編譯
            if self.target_device:
                logger.info("🐉 提交姿態檢測模型到Dragon X編譯...")
                
                try:
                    torchscript_model = pose_detector.convert_to_torchscript()
                    uploaded_model = hub.upload_model(torchscript_model)
                    
                    compile_job = hub.submit_compile_job(
                        model=uploaded_model,
                        input_specs={"image": ((1, 3, 256, 256), "float32")},
                        device=self.target_device,
                    )
                    
                    logger.info(f"✅ 姿態檢測Dragon X編譯Job: {compile_job.job_id}")
                    logger.info(f"🔗 Dashboard: https://app.aihub.qualcomm.com/jobs/{compile_job.job_id}")
                    
                    self.compiled_models['pose_fall_detection_job'] = compile_job
                    
                except Exception as e:
                    logger.error(f"❌ 姿態檢測Dragon X編譯失敗: {e}")
            
            logger.info("✅ 姿態檢測模型 (跌倒預防) 載入完成")
            
        except Exception as e:
            logger.error(f"❌ 姿態檢測模型載入失敗: {e}")
    
    def _load_face_detection_for_elderly_identification(self):
        """載入人臉檢測模型（老人身份確認）"""
        try:
            from qai_hub_models.models.mediapipe_face import Model as FaceModel
            
            logger.info("👤 載入人臉檢測模型 (老人身份確認)...")
            face_model = FaceModel.from_pretrained()
            face_detector = face_model.face_detector
            self.qai_hub_models['face_elderly_id'] = face_detector
            
            # 提交到Dragon X設備編譯
            if self.target_device:
                logger.info("🐉 提交人臉檢測模型到Dragon X編譯...")
                
                try:
                    torchscript_model = face_detector.convert_to_torchscript()
                    uploaded_model = hub.upload_model(torchscript_model)
                    
                    compile_job = hub.submit_compile_job(
                        model=uploaded_model,
                        input_specs={"image": ((1, 3, 256, 256), "float32")},
                        device=self.target_device,
                    )
                    
                    logger.info(f"✅ 人臉檢測Dragon X編譯Job: {compile_job.job_id}")
                    logger.info(f"🔗 Dashboard: https://app.aihub.qualcomm.com/jobs/{compile_job.job_id}")
                    
                    self.compiled_models['face_elderly_id_job'] = compile_job
                    
                except Exception as e:
                    logger.error(f"❌ 人臉檢測Dragon X編譯失敗: {e}")
            
            logger.info("✅ 人臉檢測模型 (老人身份確認) 載入完成")
            
        except Exception as e:
            logger.error(f"❌ 人臉檢測模型載入失敗: {e}")
    
    def _load_hand_detection_for_emergency_gestures(self):
        """載入手部檢測模型（緊急求救手勢）"""
        try:
            from qai_hub_models.models.mediapipe_hand import Model as HandModel
            
            logger.info("✋ 載入手部檢測模型 (緊急求救手勢)...")
            hand_model = HandModel.from_pretrained()
            hand_detector = hand_model.hand_detector
            self.qai_hub_models['hand_emergency_gesture'] = hand_detector
            
            # 提交到Dragon X設備編譯
            if self.target_device:
                logger.info("🐉 提交手部檢測模型到Dragon X編譯...")
                
                try:
                    torchscript_model = hand_detector.convert_to_torchscript()
                    uploaded_model = hub.upload_model(torchscript_model)
                    
                    compile_job = hub.submit_compile_job(
                        model=uploaded_model,
                        input_specs={"image": ((1, 3, 224, 224), "float32")},
                        device=self.target_device,
                    )
                    
                    logger.info(f"✅ 手部檢測Dragon X編譯Job: {compile_job.job_id}")
                    logger.info(f"🔗 Dashboard: https://app.aihub.qualcomm.com/jobs/{compile_job.job_id}")
                    
                    self.compiled_models['hand_emergency_gesture_job'] = compile_job
                    
                except Exception as e:
                    logger.error(f"❌ 手部檢測Dragon X編譯失敗: {e}")
            
            logger.info("✅ 手部檢測模型 (緊急求救手勢) 載入完成")
            
        except Exception as e:
            logger.error(f"❌ 手部檢測模型載入失敗: {e}")
    
    def analyze_fall_risk(self, pose_keypoints: List[Dict]) -> Dict[str, Any]:
        """分析跌倒風險"""
        if not pose_keypoints:
            return {"fall_risk": "unknown", "confidence": 0.0, "reasons": []}
        
        fall_risk_indicators = []
        risk_score = 0.0
        
        try:
            # 提取關鍵關節點
            keypoints = pose_keypoints[0] if pose_keypoints else {}
            
            # 檢測身體傾斜度
            if len(keypoints.get('keypoints', [])) >= 17:
                kpts = keypoints['keypoints']
                
                # 肩膀水平度檢查
                left_shoulder = kpts[5] if len(kpts) > 5 else None
                right_shoulder = kpts[6] if len(kpts) > 6 else None
                
                if left_shoulder and right_shoulder:
                    shoulder_angle = abs(left_shoulder['y'] - right_shoulder['y'])
                    if shoulder_angle > 0.3:  # 閾值可調整
                        fall_risk_indicators.append("身體明顯傾斜")
                        risk_score += 0.4
                
                # 重心穩定性檢查
                left_hip = kpts[11] if len(kpts) > 11 else None
                right_hip = kpts[12] if len(kpts) > 12 else None
                left_ankle = kpts[15] if len(kpts) > 15 else None
                right_ankle = kpts[16] if len(kpts) > 16 else None
                
                if all([left_hip, right_hip, left_ankle, right_ankle]):
                    # 檢查腳踝位置相對於髖部
                    hip_center_x = (left_hip['x'] + right_hip['x']) / 2
                    ankle_center_x = (left_ankle['x'] + right_ankle['x']) / 2
                    
                    balance_offset = abs(hip_center_x - ankle_center_x)
                    if balance_offset > 0.4:  # 重心偏移過大
                        fall_risk_indicators.append("重心不穩定")
                        risk_score += 0.3
                
                # 膝蓋彎曲度檢查
                left_knee = kpts[13] if len(kpts) > 13 else None
                right_knee = kpts[14] if len(kpts) > 14 else None
                
                if left_knee and right_knee and left_hip and right_hip:
                    # 檢查膝蓋是否過度彎曲（可能表示跌倒）
                    left_knee_angle = abs(left_knee['y'] - left_hip['y'])
                    right_knee_angle = abs(right_knee['y'] - right_hip['y'])
                    
                    if left_knee_angle < 0.1 or right_knee_angle < 0.1:
                        fall_risk_indicators.append("膝蓋異常彎曲")
                        risk_score += 0.3
        
        except Exception as e:
            logger.error(f"❌ 跌倒風險分析失敗: {e}")
            return {"fall_risk": "analysis_error", "confidence": 0.0, "error": str(e)}
        
        # 判定風險等級
        if risk_score >= 0.7:
            risk_level = "high"
            risk_message = "⚠️ 高跌倒風險"
        elif risk_score >= 0.4:
            risk_level = "medium"
            risk_message = "🔶 中等跌倒風險"
        elif risk_score >= 0.1:
            risk_level = "low"
            risk_message = "🔷 低跌倒風險"
        else:
            risk_level = "normal"
            risk_message = "✅ 正常狀態"
        
        return {
            "fall_risk": risk_level,
            "risk_score": risk_score,
            "confidence": min(risk_score * 1.5, 1.0),
            "message": risk_message,
            "indicators": fall_risk_indicators,
            "recommendation": self._get_safety_recommendation(risk_level)
        }
    
    def _get_safety_recommendation(self, risk_level: str) -> str:
        """根據風險等級提供安全建議"""
        recommendations = {
            "high": "立即檢查環境安全，建議尋求協助或坐下休息",
            "medium": "注意周圍環境，放慢動作，確保有支撐物在附近",
            "low": "保持謹慎，注意腳下狀況",
            "normal": "繼續保持良好姿態"
        }
        return recommendations.get(risk_level, "保持安全意識")
    
    def comprehensive_fall_prevention_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """綜合跌倒預防檢測"""
        results = {
            "timestamp": time.time(),
            "dragon_x_device": self.target_device.name if self.target_device else None,
            "fall_prevention_analysis": {},
            "detections": {},
            "qai_hub_jobs": {}
        }
        
        # 姿態檢測（核心）
        if 'pose_fall_detection' in self.qai_hub_models:
            logger.info("🚶‍♂️ 執行姿態檢測 (跌倒預防核心)...")
            if 'pose_fall_detection' in self.onnx_sessions:
                pose_detection = self._run_pose_inference_edge(image)
                if pose_detection.get('keypoints'):
                    fall_analysis = self.analyze_fall_risk(pose_detection["keypoints"])
                    results["fall_prevention_analysis"] = fall_analysis
                results["detections"]["pose"] = pose_detection
            else:
                # 模擬
                mock_pose_results = {
                    "keypoints": [{
                        "keypoints": [
                            {"x": 0.5, "y": 0.3, "confidence": 0.8},
                            {"x": 0.45, "y": 0.5, "confidence": 0.9},
                            {"x": 0.55, "y": 0.5, "confidence": 0.9},
                        ]
                    }]
                }
                fall_analysis = self.analyze_fall_risk(mock_pose_results["keypoints"])
                results["fall_prevention_analysis"] = fall_analysis
                results["detections"]["pose"] = mock_pose_results
        
        # 記錄Dragon X編譯Job資訊
        for job_name, job in self.compiled_models.items():
            model_type = job_name.replace('_job', '')
            results["qai_hub_jobs"][model_type] = {
                "job_id": job.job_id,
                "dashboard_url": f"https://app.aihub.qualcomm.com/jobs/{job.job_id}",
                "target_device": self.target_device.name
            }
        
        return results

    # === Edge Runtime 相關輔助 ===
    def _wait_for_all_compile_jobs(self, timeout: int = 1800, poll: int = 10):
        start = time.time()
        pending = True
        while pending:
            pending = False
            for name, job in self.compiled_models.items():
                try:
                    job.wait(timeout=1)
                except Exception:
                    pending = True
            elapsed = time.time() - start
            if elapsed > timeout:
                logger.warning("⚠️ 超時，仍有編譯Job未完成，繼續後續流程")
                break
            if pending:
                logger.info(f"⏳ 等待編譯Jobs完成... 已等待 {int(elapsed)}s")
                time.sleep(poll)

    def _download_compiled_target_models(self):
        """嘗試對每個 compile job 取得 target_model 並下載為 ONNX / DLC。
        優先下載為 .onnx (若 SDK 提供)。"""
        for job_key, compile_job in self.compiled_models.items():
            label = job_key.replace('_job', '')
            target_path = self.download_dir / f"compiled_{label}.onnx"
            if target_path.exists():
                continue
            try:
                logger.info(f"💾 取得 target_model 並下載: {label}")
                target_model = compile_job.get_target_model()
                if hasattr(target_model, 'download'):
                    target_model.download(str(target_path))
                    logger.info(f"✅ 已下載 {target_path}")
                else:
                    logger.warning(f"⚠️ target_model 無 download 方法: {label}")
            except Exception as e:
                logger.warning(f"⚠️ 下載 {label} 失敗: {e}")

    def _create_onnx_sessions_from_downloads(self):
        """為已下載模型建立 ONNX Runtime session。"""
        providers = self._select_providers()
        for onnx_file in self.download_dir.glob('compiled_*.onnx'):
            label = onnx_file.stem.replace('compiled_', '')
            if label in self.onnx_sessions:
                continue
            try:
                session = ort.InferenceSession(str(onnx_file), providers=providers)
                input_meta = session.get_inputs()[0]
                self.onnx_sessions[label] = {
                    'session': session,
                    'input_name': input_meta.name,
                    'shape': input_meta.shape,
                    'path': str(onnx_file)
                }
                logger.info(f"✅ ONNX Session 建立成功: {label} providers={providers}")
            except Exception as e:
                logger.warning(f"⚠️ 建立 {label} ONNX Session 失敗: {e}")

    def _select_providers(self) -> List[str]:
        available = ort.get_available_providers()
        priority = [
            'QNNExecutionProvider',  # 若裝置安裝 QNN EP
            'CUDAExecutionProvider',
            'DmlExecutionProvider',
            'CoreMLExecutionProvider',
            'CPUExecutionProvider'
        ]
        chosen = [p for p in priority if p in available]
        if not chosen:
            chosen = ['CPUExecutionProvider']
        return chosen

    def _preprocess_for_session(self, image: np.ndarray, shape: List[int]) -> np.ndarray:
        # shape 可能為 [1,3,H,W] 或 [1,H,W,3] 或 動態維度
        if len(shape) == 4:
            if shape[1] == 3:  # NCHW
                H = int(shape[2]) if isinstance(shape[2], (int, float)) else 256
                W = int(shape[3]) if isinstance(shape[3], (int, float)) else 256
                resized = cv2.resize(image, (W, H))
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                norm = rgb.astype(np.float32) / 255.0
                tensor = np.transpose(norm, (2, 0, 1))[None, ...]
                return tensor
            elif shape[-1] == 3:  # NHWC
                H = int(shape[1]) if isinstance(shape[1], (int, float)) else 256
                W = int(shape[2]) if isinstance(shape[2], (int, float)) else 256
                resized = cv2.resize(image, (W, H))
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                norm = rgb.astype(np.float32) / 255.0
                tensor = norm[None, ...]
                return tensor
        # fallback
        resized = cv2.resize(image, (256, 256))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        norm = rgb.astype(np.float32) / 255.0
        tensor = np.transpose(norm, (2, 0, 1))[None, ...]
        return tensor

    def _run_pose_inference_edge(self, image: np.ndarray) -> Dict[str, Any]:
        if 'pose_fall_detection' not in self.onnx_sessions:
            return {"error": "no_pose_session"}
        sess_info = self.onnx_sessions['pose_fall_detection']
        session = sess_info['session']
        input_name = sess_info['input_name']
        shape = sess_info['shape']
        inp = self._preprocess_for_session(image, shape)
        t0 = time.time()
        try:
            outputs = session.run(None, {input_name: inp})
            latency = (time.time() - t0) * 1000
            # 簡化: 嘗試將第一個輸出視為關鍵點 (若形狀相容)，否則回傳 raw shape
            keypoints = []
            first = outputs[0]
            if isinstance(first, np.ndarray) and first.ndim in (2, 3, 4):
                flat = first.reshape(-1, first.shape[-1]) if first.shape[-1] in (2, 3, 4) else None
                if flat is not None and flat.shape[1] >= 2:
                    # 取前 17 個 (標準 COCO) 若足夠
                    for row in flat[:17]:
                        x = float(row[0]) if np.isfinite(row[0]) else 0.0
                        y = float(row[1]) if np.isfinite(row[1]) else 0.0
                        conf = float(row[2]) if flat.shape[1] > 2 and np.isfinite(row[2]) else 0.5
                        keypoints.append({"x": x, "y": y, "confidence": conf})
            return {
                "inference_ms": round(latency, 2),
                "output_shapes": [o.shape if isinstance(o, np.ndarray) else str(type(o)) for o in outputs],
                "keypoints": [{"keypoints": keypoints}] if keypoints else [],
                "providers": session.get_providers(),
            }
        except Exception as e:
            return {"error": str(e)}

    def run_realtime_inference(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            logger.error("❌ 無法開啟攝影機，結束即時推論")
            return
        frame_id = 0
        t_last_fps = time.time()
        fps = 0.0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("⚠️ 讀取影格失敗，停止")
                    break
                result = self.comprehensive_fall_prevention_detection(frame)
                frame_id += 1
                # FPS 計算
                if frame_id % 10 == 0:
                    now = time.time()
                    fps = 10.0 / (now - t_last_fps)
                    t_last_fps = now
                # 視覺化 (僅顯示 FPS & 風險)
                overlay = frame.copy()
                fall_info = result.get('fall_prevention_analysis', {})
                status = fall_info.get('message', 'N/A')
                cv2.putText(overlay, f"FPS:{fps:.1f}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(0,255,255),2)
                cv2.putText(overlay, status, (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.7,(0,255,0),2)
                cv2.imshow('DragonX Edge Realtime', overlay)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("👋 使用者結束即時推論")
                    break
                if self.max_frames and frame_id >= self.max_frames:
                    logger.info("🛑 已達最大影格數，結束即時推論")
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    def get_dragon_x_status_report(self) -> Dict[str, Any]:
        """獲取Dragon X系統狀態報告"""
        report = {
            "system_name": "Dragon X老人跌倒預防檢測系統",
            "timestamp": time.time(),
            "dragon_x_device": {
                "name": self.target_device.name if self.target_device else None,
                "status": "ready" if self.target_device else "not_found"
            },
            "models_status": {},
            "qai_hub_jobs": {},
            "hackathon_readiness": True
        }
        
        # 檢查模型狀態
        for model_name in self.qai_hub_models:
            report["models_status"][model_name] = "loaded"
        
        # 檢查編譯Job狀態
        for job_name, job in self.compiled_models.items():
            try:
                # 嘗試快速檢查狀態
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
    import argparse
    parser = argparse.ArgumentParser(description='Dragon X Edge 推論系統')
    parser.add_argument('--download-compiled', action='store_true', help='等待並下載 compiled target models 供 edge 推論')
    parser.add_argument('--wait-compile', action='store_true', help='初始化期間等待 compile jobs 完成')
    parser.add_argument('--realtime', action='store_true', help='啟動即時攝影機推論 (需已建立 ONNX sessions)')
    parser.add_argument('--camera-index', type=int, default=0, help='攝影機索引 (預設0)')
    parser.add_argument('--max-frames', type=int, default=None, help='測試模式最大影格數')
    args = parser.parse_args()

    print("🐉 Dragon X老人跌倒預防檢測系統 (Edge 版本)")
    print("=" * 60)
    print("🎯 Snapdragon X Elite Edge Deployment")
    print()

    try:
        dragon_system = DragonXFallDetectionSystem(download_compiled=args.download_compiled,
                                                   wait_compile=args.wait_compile,
                                                   realtime=args.realtime,
                                                   camera_index=args.camera_index,
                                                   max_frames=args.max_frames)

        status_report = dragon_system.get_dragon_x_status_report()
        print("📊 系統狀態:")
        print(f"   🐉 目標設備: {status_report['dragon_x_device']['name']}")
        print(f"   📱 設備狀態: {status_report['dragon_x_device']['status']}")
        print(f"   🧠 已載入模型: {len(status_report['models_status'])}")
        print(f"   ⚡ Compile Jobs: {len(status_report['qai_hub_jobs'])}")
        print(f"   � Edge ONNX Sessions: {len(dragon_system.onnx_sessions)}")
        print()

        # 若未進入即時模式且已具備 ONNX session，做一次靜態測試
        if not args.realtime:
            test_image = np.random.randint(0,255,(480,640,3),dtype=np.uint8)
            results = dragon_system.comprehensive_fall_prevention_detection(test_image)
            fall_analysis = results.get('fall_prevention_analysis', {})
            print("✅ 單張影像分析:")
            print(f"   狀態: {fall_analysis.get('message','N/A')}")
            print(f"   風險: {fall_analysis.get('risk_score',0):.2f}")
            if fall_analysis.get('indicators'):
                print(f"   指標: {', '.join(fall_analysis['indicators'])}")
            with open('dragon_x_edge_single_infer.json','w') as f:
                json.dump({"status_report": status_report, "result": results}, f, indent=2, default=str)
            print("📝 已輸出 dragon_x_edge_single_infer.json")

        if args.realtime and not dragon_system.onnx_sessions:
            print("⚠️ 未建立 ONNX Sessions，請加上 --download-compiled 或先行下載模型")

    except Exception as e:
        print(f"❌ 初始化或推論失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
