#!/usr/bin/env python3
"""
🐉 Dragon X專用老人跌倒預防檢測系統
專為黑客松優化，使用Snapdragon X Elite平台
"""

import os
import sys
import subprocess
import shutil
import qai_hub as hub
import numpy as np
import cv2
import onnxruntime as ort
import logging
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # make optional
    def load_dotenv(*args, **kwargs):
        print("⚠️ 未安裝 python-dotenv，跳過 .env 載入 (可執行: pip install python-dotenv)")
        return False
from typing import Dict, Any, List, Optional
import time
import json
import argparse
import re

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DragonXFallDetectionSystem:
    """Dragon X專用老人跌倒預防檢測系統"""

    def __init__(self, full_pipeline: bool = False, wait: bool = False, poll_interval: int = 15, debug_link: bool = False, link_python: bool = False):
        """初始化Dragon X檢測系統

        Args:
            full_pipeline: 是否執行 Compile→Profile→Inference (官方示例步驟)
            wait: 是否等待所有 Job 完成
            poll_interval: 輪詢秒數
            debug_link: 是否輸出 link job 除錯資訊
            link_python: 是否使用 Python API submit_link_job 進行多模型 link (否則僅嘗試 CLI)
        """
        # 基本屬性
        self.api_token = os.getenv('QAI_HUB_API_TOKEN')
        self.target_device = None
        # 模型與工作追蹤
        self.qai_hub_models: Dict[str, Any] = {}
        self.compiled_models: Dict[str, Any] = {}
        self.onnx_sessions: Dict[str, Any] = {}
        self.profile_jobs: Dict[str, Any] = {}
        self.link_jobs: Dict[str, Any] = {}
        self.target_models: Dict[str, Any] = {}
        self.inference_jobs: Dict[str, Any] = {}
        self.inference_outputs: Dict[str, Any] = {}
        # 執行參數
        self.full_pipeline = full_pipeline
        self.wait_for_jobs = wait
        self.poll_interval = poll_interval
        self.debug_link = debug_link  # 是否輸出 link job 除錯資訊
        self.python_link_requested = link_python

        logger.info("🐉 初始化Dragon X老人跌倒預防檢測系統...")
        self._find_dragon_x_devices()
        self._initialize_fall_detection_models()

        if self.full_pipeline:
            logger.info("🧪 啟動完整官方流程 (Step 1~6 for each model)")
            self._run_full_official_steps_for_all_models()
            # 如果使用 Python link 先執行 (官方 API)；否則嘗試 CLI；若兩者都想要可自行再呼叫
            if self.python_link_requested:
                self._link_all_models_python()
            else:
                self._attempt_link_jobs_cli()
    
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
                        # 指定目標產出為 Qualcomm AI Engine Direct DLC, 以便後續 link
                        options="--target_runtime qnn_dlc"
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
                        options="--target_runtime qnn_dlc"
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
                        options="--target_runtime qnn_dlc"
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
            real_pose = self._run_pose_inference_local(image)
            if real_pose is None:
                # fallback 模擬
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
            else:
                fall_analysis = self.analyze_fall_risk(real_pose["keypoints"])
                results["fall_prevention_analysis"] = fall_analysis
                results["detections"]["pose"] = real_pose
        
        # 記錄Dragon X編譯Job資訊
        for job_name, job in self.compiled_models.items():
            model_type = job_name.replace('_job', '')
            results["qai_hub_jobs"][model_type] = {
                "job_id": job.job_id,
                "dashboard_url": f"https://app.aihub.qualcomm.com/jobs/{job.job_id}",
                "target_device": self.target_device.name
            }
        
        return results
    
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
            "profile_jobs": {},
            "link_jobs": {},
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

        # Profile jobs
        for name, job in self.profile_jobs.items():
            try:
                job.wait(timeout=1)
                status = "completed"
            except:
                status = "running"
            report["profile_jobs"][name] = {
                "job_id": job.job_id,
                "status": status,
                "dashboard_url": f"https://app.aihub.qualcomm.com/jobs/{job.job_id}"
            }

        # Link jobs (CLI submissions only have ID string)
        for name, info in self.link_jobs.items():
            report["link_jobs"][name] = info
        
        return report

    # ================= 實際執行本地推論 (姿態) =================
    def _run_pose_inference_local(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """嘗試使用已下載的 compiled_pose_fall_detection.onnx 執行本地推論。

        目標: 優先使用 QNN / QNNExecutionProvider (若環境支援) 以觸發 NPU。
        回傳格式: {"keypoints": [{"keypoints": [{x,y,confidence}, ...]}]}
        失敗則回傳 None。
        """
        onnx_path = 'compiled_pose_fall_detection.onnx'
        if not os.path.exists(onnx_path):
            logger.warning("⚠️ 找不到已下載的姿態 ONNX (compiled_pose_fall_detection.onnx)，使用模擬資料")
            return None
        try:
            providers = ort.get_available_providers()
            preferred = []
            # 常見可能名稱（依平台調整）
            for cand in ['QNNExecutionProvider', 'QNN', 'CPUExecutionProvider']:
                if cand in providers and cand not in preferred:
                    preferred.append(cand)
            if not preferred:
                preferred = providers
            logger.info(f"🧩 ONNX Runtime Providers 可用: {providers} -> 使用順序: {preferred}")
            sess = ort.InferenceSession(onnx_path, providers=preferred)

            # 前處理: BGR->RGB, resize 256, normalize 0..1
            img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            img_resized = cv2.resize(img, (256, 256), interpolation=cv2.INTER_LINEAR)
            tensor = img_resized.astype('float32') / 255.0
            tensor = np.transpose(tensor, (2, 0, 1))  # CHW
            tensor = np.expand_dims(tensor, 0)  # NCHW

            input_name = sess.get_inputs()[0].name
            outputs = sess.run(None, {input_name: tensor})
            output_meta = sess.get_outputs()

            # 嘗試從第一個輸出推測 keypoints (假設形狀 [1, K, 3] 或 [1, 3, K])
            keypoints_list = []
            if outputs:
                arr = outputs[0]
                arr_np = np.array(arr)
                kpts = []
                try:
                    if arr_np.ndim == 3:  # 例如 (1, K, C) or (1, C, K)
                        if arr_np.shape[2] == 3:  # (1, K, 3)
                            for i in range(min(arr_np.shape[1], 25)):
                                x, y, c = arr_np[0, i]
                                kpts.append({"x": float(x), "y": float(y), "confidence": float(c)})
                        elif arr_np.shape[1] == 3:  # (1, 3, K)
                            for i in range(min(arr_np.shape[2], 25)):
                                x = arr_np[0, 0, i]
                                y = arr_np[0, 1, i]
                                c = arr_np[0, 2, i] if arr_np.shape[1] > 2 else 0.9
                                kpts.append({"x": float(x), "y": float(y), "confidence": float(c)})
                    elif arr_np.ndim == 2 and arr_np.shape[0] == 1:  # (1, N) 攤平
                        flat = arr_np[0]
                        for i in range(0, min(len(flat), 75), 3):
                            if i + 2 < len(flat):
                                kpts.append({"x": float(flat[i]), "y": float(flat[i+1]), "confidence": float(flat[i+2])})
                    else:
                        logger.warning(f"⚠️ 無法解析姿態輸出 shape={arr_np.shape}，使用模擬 fallback")
                except Exception as e:
                    logger.warning(f"⚠️ 解析姿態輸出失敗:{e}，使用模擬 fallback")
                    return None
                if kpts:
                    keypoints_list.append({"keypoints": kpts})
            if not keypoints_list:
                return None
            return {"keypoints": keypoints_list, "provider": sess.get_providers(), "output_names": [o.name for o in output_meta]}
        except Exception as e:
            logger.warning(f"⚠️ 本地姿態推論失敗 (改用模擬): {e}")
            return None

    # ===================== 新增：完整Pipeline支援 =====================
    def _submit_profile_jobs_for_all(self):
        """為所有已提交的編譯模型提交 profiling job（近似 inference 性能測試）"""
        if not self.target_device:
            logger.warning("⚠️ 無目標設備，跳過 profiling 提交")
            return
        for key, compile_job in self.compiled_models.items():
            model_label = key.replace('_job', '')
            if model_label in self.profile_jobs:
                continue
            try:
                # 等待單一 compile job 完成後再送 profiling (避免 'model not compiled' 錯誤)
                logger.info(f"⏳ 等待編譯完成以便 Profiling: {model_label} ({compile_job.job_id}) ...")
                self._wait_for_single_job(compile_job, f"compile:{model_label}")
                logger.info(f"✅ 編譯已完成，提交 Profiling: {model_label}")
                # 嘗試從原始模型字典找到對應 component
                component_key = None
                if 'pose' in model_label:
                    component_key = 'pose_fall_detection'
                elif 'face' in model_label:
                    component_key = 'face_elderly_id'
                elif 'hand' in model_label:
                    component_key = 'hand_emergency_gesture'
                component = self.qai_hub_models.get(component_key)
                # 準備樣本輸入（僅當 API 支援相關參數時才使用）
                sample_inputs_256 = {"image": np.random.rand(1,3,256,256).astype('float32')}
                sample_inputs_224 = {"image": np.random.rand(1,3,224,224).astype('float32')}
                sample_inputs = sample_inputs_224 if component_key == 'hand_emergency_gesture' else sample_inputs_256

                profile_job = None
                # 1. 嘗試最簡 API 形式（新版 SDK 可能只接受必要參數）
                try:
                    profile_job = hub.submit_profile_job(model=compile_job.model, device=self.target_device)
                except TypeError as te1:
                    # 2. 嘗試參數名稱 'inputs'
                    try:
                        profile_job = hub.submit_profile_job(model=compile_job.model, device=self.target_device, inputs=sample_inputs)
                    except TypeError as te2:
                        # 3. 嘗試舊版可能的 positional 調用
                        try:
                            profile_job = hub.submit_profile_job(compile_job.model, self.target_device)
                        except Exception as te3:
                            raise RuntimeError(f"submit_profile_job 多重呼叫形式均失敗: {te1}; {te2}; {te3}")
                except Exception as e_any:
                    raise RuntimeError(f"submit_profile_job 呼叫失敗: {e_any}")

                if profile_job is None:
                    raise RuntimeError("submit_profile_job 返回 None，可能 API 已變更")
                self.profile_jobs[model_label + '_profile'] = profile_job
                logger.info(f"📈 提交Profiling: {model_label} -> {profile_job.job_id}")
                logger.info(f"🔗 Dashboard: https://app.aihub.qualcomm.com/jobs/{profile_job.job_id}")
            except Exception as e:
                logger.error(f"❌ Profiling 提交失敗 {model_label}: {e}")

    # === 新增：官方 Step1~6 整合執行 ===
    def _run_full_official_steps_for_all_models(self):
        """依照官方教學步驟對每個模型執行:
        Step1 準備/Trace(已於載入時完成 TorchScript 轉換)
        Step2 Compile (已提交)
        Step3 Profile (等待 compile 完成後，以 target_model 執行)
        Step4 Inference (同樣使用 target_model)
        Step5 Post-process (基本輸出形狀/統計)
        Step6 Download target model (ONNX/TorchScript)
        """
        if not self.target_device:
            logger.warning("⚠️ 無目標設備，跳過官方步驟")
            return
        for key, compile_job in list(self.compiled_models.items()):
            model_label = key.replace('_job', '')
            logger.info(f"================ {model_label} PIPELINE ================")
            logger.info(f"🟦 Step 2: 等待 Compile 完成 -> {compile_job.job_id}")
            self._wait_for_single_job(compile_job, f"compile:{model_label}")
            # Step3: Profile 需 target model
            try:
                logger.info("🟩 取得 target_model (get_target_model)")
                target_model = compile_job.get_target_model()
                self.target_models[model_label] = target_model
            except Exception as e:
                logger.error(f"❌ 無法取得 target_model ({model_label}): {e}")
                continue
            # 提交 Profile
            if model_label + '_profile' not in self.profile_jobs:
                try:
                    logger.info("🟨 Step 3: 提交 Profile Job")
                    profile_job = hub.submit_profile_job(model=target_model, device=self.target_device)
                    self.profile_jobs[model_label + '_profile'] = profile_job
                    self._wait_for_single_job(profile_job, f"profile:{model_label}")
                except Exception as e:
                    logger.warning(f"⚠️ Profile 失敗 ({model_label}): {e}")
            # Inference
            if model_label not in self.inference_jobs:
                try:
                    logger.info("🟥 Step 4: 提交 Inference Job")
                    # 建立簡單隨機輸入 (依原始 input spec 尺寸)
                    shape = (1, 3, 256, 256)
                    if 'hand' in model_label:
                        shape = (1, 3, 224, 224)
                    dummy = np.random.rand(*shape).astype('float32')
                    inf_job = hub.submit_inference_job(model=target_model, device=self.target_device, inputs={'image': [dummy]})
                    self.inference_jobs[model_label + '_inference'] = inf_job
                    self._wait_for_single_job(inf_job, f"inference:{model_label}")
                    # Step5: Post-process (下載輸出資料)
                    try:
                        outputs = inf_job.download_output_data()
                        self.inference_outputs[model_label] = {k: (np.array(v).shape if isinstance(v, list) else 'unknown') for k, v in outputs.items()}
                        logger.info(f"🧪 Step 5: 輸出摘要: {self.inference_outputs[model_label]}")
                    except Exception as e:
                        logger.warning(f"⚠️ 下載推論輸出失敗 ({model_label}): {e}")
                except Exception as e:
                    logger.error(f"❌ Inference Job 提交失敗 ({model_label}): {e}")
            # Step6: 下載模型
            if model_label not in self.target_models:
                continue
            try:
                download_name = f"compiled_{model_label}.onnx"
                logger.info(f"💾 Step 6: 下載 target model -> {download_name}")
                # target_model 可能提供 download 方法
                target_model = self.target_models[model_label]
                if hasattr(target_model, 'download'):
                    target_model.download(download_name)
                    logger.info(f"✅ 已下載 {download_name}")
                else:
                    logger.warning(f"⚠️ target_model 無 download 方法，跳過下載 ({model_label})")
            except Exception as e:
                logger.warning(f"⚠️ 下載模型失敗 ({model_label}): {e}")
            logger.info(f"================ {model_label} DONE ==================")

        # 若使用者要求 Python link (多模型打包) 可在完成後執行
        if getattr(self, 'python_link_requested', False):
            self._link_all_models_python()

    def _link_all_models_python(self):
        """使用官方 API hub.submit_link_job 將多個已編譯的 target_models 進行 link。

        注意: 官方範例是同一模型不同輸入尺寸以共享權重; 這裡是不同任務模型 (pose/face/hand),
        仍可嘗試產出一個 context binary, 但權重共享收益有限。
        條件: 需為 Qualcomm AI Engine Direct (qnn_dlc) 輸出; 已在 compile 時加上 --target_runtime qnn_dlc。
        """
        if not self.target_device:
            logger.warning("⚠️ 無目標設備, 無法執行 Python link")
            return
        # 確保 target_models 都已取得
        for job_key, compile_job in self.compiled_models.items():
            label = job_key.replace('_job', '')
            if label not in self.target_models:
                try:
                    self._wait_for_single_job(compile_job, f"compile:{label}")
                    self.target_models[label] = compile_job.get_target_model()
                except Exception as e:
                    logger.warning(f"⚠️ 無法取得 target_model ({label}): {e}，跳過該模型的 link")
        models_to_link = [m for m in self.target_models.values() if m is not None]
        if len(models_to_link) < 2:
            logger.warning("⚠️ 可用 target_models 少於2, 跳過 link")
            return
        try:
            logger.info(f"🔗 (Python API) submit_link_job: {len(models_to_link)} 個模型 -> 單一 context")
            link_job = hub.submit_link_job(models_to_link, device=self.target_device, name="DragonX MultiModel Context")
            self.link_jobs['dragonx_python_link'] = {
                'job_id': link_job.job_id,
                'status': 'submitted',
                'dashboard_url': f'https://app.aihub.qualcomm.com/jobs/{link_job.job_id}'
            }
            # 等待完成 (限制時間避免阻塞過久)
            self._wait_for_single_job(link_job, 'link:dragonx_python', timeout=1800, poll=15)
            try:
                linked_model = link_job.get_target_model()
                if hasattr(linked_model, 'download'):
                    linked_model.download('dragonx_linked_context.bin')
                    logger.info("💾 已下載 linked context -> dragonx_linked_context.bin")
            except Exception as e:
                logger.warning(f"⚠️ 取得/下載 linked model 失敗: {e}")
        except Exception as e:
            logger.error(f"❌ Python link_job 失敗: {e}")

    def _attempt_link_jobs_cli(self):
        """透過 CLI 嘗試提交 link job（若 SDK 無 Python API）。"""
        cli = shutil.which('qai-hub')
        if not cli:
            logger.warning("⚠️ 未找到 qai-hub CLI，跳過 link job")
            return
        if not self.target_device:
            logger.warning("⚠️ 無目標設備，跳過 link job")
            return
        device_name = self.target_device.name
        device_os = getattr(self.target_device, 'os_version', None) or getattr(self.target_device, 'os', None)

        # 1. 取得 help 輸出以動態偵測可用旗標
        help_flags: List[str] = []
        try:
            help_proc = subprocess.run([cli, 'submit-link-job', '-h'], capture_output=True, text=True, timeout=30)
            help_text = (help_proc.stdout + '\n' + help_proc.stderr)
            for line in help_text.splitlines():
                line = line.strip()
                if line.startswith('--'):
                    # 擷取旗標名稱 (空白或=前)
                    flag = line.split()[0]
                    # 移除描述中逗號分隔的其他 alias
                    for part in flag.split(','):
                        if part.startswith('--'):
                            help_flags.append(part.strip())
            logger.info(f"🔍 Link CLI 可用旗標: {help_flags}")
            if self.debug_link:
                with open('qai_hub_submit_link_job_help.txt', 'w') as f:
                    f.write(help_text)
                logger.info("💾 已儲存 submit-link-job help 到 qai_hub_submit_link_job_help.txt")
        except Exception as e:
            logger.warning(f"⚠️ 無法取得 submit-link-job help: {e} (採用保守猜測)")

        # 可能的模型旗標 (依優先順序)
        candidate_model_flags = [f for f in ['--model', '--model-id', '--model_id'] if f in help_flags]
        # 可能的 compile job 旗標
        candidate_compile_flags = [f for f in ['--compile-job-id', '--compile_job_id', '--job-id', '--job_id'] if f in help_flags]
        # 裝置旗標
        candidate_device_flags = [f for f in ['--device', '--target-device', '--target_device'] if f in help_flags]
        # OS 旗標
        candidate_device_os_flags = [f for f in ['--device-os', '--device_os', '--os-version'] if f in help_flags]

        for key, compile_job in self.compiled_models.items():
            model_label = key.replace('_job', '')
            if model_label in self.link_jobs:
                continue

            model_id = getattr(getattr(compile_job, 'model', None), 'model_id', None)
            compile_job_id = getattr(compile_job, 'job_id', None)

            # 建立初始命令 (保守: 只加我們確定存在的旗標)
            base_cmd = [cli, 'submit-link-job']

            # 優先使用 compile job id (若 CLI 支援)
            if compile_job_id and candidate_compile_flags:
                base_cmd += [candidate_compile_flags[0], compile_job_id]
            elif model_id and candidate_model_flags:
                base_cmd += [candidate_model_flags[0], model_id]
            elif model_id:
                # 嘗試 positional model id (無旗標)
                base_cmd.append(model_id)

            # Device
            if candidate_device_flags:
                base_cmd += [candidate_device_flags[0], device_name]
            else:
                # 嘗試推測 --device (即便 help 未列出, 最常見)
                base_cmd += ['--device', device_name]

            # Device OS (僅在旗標存在才加)
            if device_os and candidate_device_os_flags:
                base_cmd += [candidate_device_os_flags[0], str(device_os)]

            # 一些 CLI 沒有 --output json, 故僅在 help 有列出時才加入
            if '--output' in help_flags or '--format' in help_flags:
                if '--output' in help_flags:
                    base_cmd += ['--output', 'json']
                else:
                    base_cmd += ['--format', 'json']

            if self.debug_link:
                base_cmd.append('--verbose') if '--verbose' in help_flags else None
            logger.info(f"🔗 嘗試提交 Link Job (初始): {' '.join(base_cmd)}")

            # 迭代嘗試, 若出現 unrecognized arguments, 動態移除
            attempt_cmd = list(base_cmd)
            raw_capture = ''
            success = False
            attempt_logs: List[str] = []
            for attempt in range(6):
                try:
                    proc = subprocess.run(attempt_cmd, capture_output=True, text=True, timeout=180)
                    stdout = proc.stdout.strip()
                    stderr = proc.stderr.strip()
                    raw_capture = (stdout + '\n' + stderr)
                    if self.debug_link:
                        attempt_logs.append(f"Attempt {attempt+1} CMD: {' '.join(attempt_cmd)}\n--- STDOUT ---\n{stdout}\n--- STDERR ---\n{stderr}\n")

                    # 偵測未支援旗標並移除
                    m = re.search(r'unrecognized arguments?: (.+)', raw_capture)
                    if m:
                        unknown_parts = m.group(1).split()
                        # 嘗試移除出現於命令列的旗標 (與其後值)
                        removed_any = False
                        for up in unknown_parts:
                            token = up.strip(',')
                            if token in attempt_cmd:
                                idx = attempt_cmd.index(token)
                                # 同時移除後一個值 (若存在且非以--開頭)
                                removal = [attempt_cmd[idx]]
                                if idx + 1 < len(attempt_cmd) and not attempt_cmd[idx+1].startswith('--'):
                                    removal.append(attempt_cmd[idx+1])
                                for r in removal:
                                    attempt_cmd.remove(r)
                                removed_any = True
                        if removed_any:
                            logger.warning(f"⚠️ 移除未支援旗標後重試: {' '.join(attempt_cmd)}")
                            continue  # 重跑下一輪

                    # 解析 job id
                    job_id = None
                    # Regex 1: 括號形式 (jxxxxxxx)
                    m2 = re.search(r'\(j[a-z0-9]{6,}\)', raw_capture, re.IGNORECASE)
                    if m2:
                        job_id = m2.group(0).strip('()')
                    if not job_id:
                        # 直接 token 掃描
                        for token in raw_capture.split():
                            t = token.strip('(),.\r\n')
                            if re.fullmatch(r'j[a-z0-9]{6,}', t.lower()):
                                job_id = t
                                break
                    if job_id:
                        self.link_jobs[model_label + '_link'] = {
                            'job_id': job_id,
                            'status': 'submitted',
                            'dashboard_url': f'https://app.aihub.qualcomm.com/jobs/{job_id}'
                        }
                        logger.info(f"✅ Link Job 提交成功: {job_id}")
                        success = True
                        break
                    else:
                        # 若沒有 unrecognized 而也沒 job id, 可能需要換 model / compile id 旗標策略
                        if attempt == 0 and model_id and compile_job_id and candidate_model_flags and candidate_compile_flags:
                            # 交替使用另一種類旗標
                            if candidate_model_flags[0] in attempt_cmd:
                                # 換成 compile 旗標
                                for f in candidate_model_flags:
                                    if f in attempt_cmd:
                                        idx = attempt_cmd.index(f)
                                        # 刪除旗標與其值
                                        del attempt_cmd[idx:idx+2]
                                attempt_cmd += [candidate_compile_flags[0], compile_job_id]
                            else:
                                for f in candidate_compile_flags:
                                    if f in attempt_cmd:
                                        idx = attempt_cmd.index(f)
                                        del attempt_cmd[idx:idx+2]
                                attempt_cmd += [candidate_model_flags[0], model_id]
                            logger.warning(f"⚠️ 切換旗標策略重試: {' '.join(attempt_cmd)}")
                            continue
                        logger.warning(f"⚠️ 未解析到 Link Job ID (嘗試次數 {attempt+1})")
                except Exception as e:
                    logger.warning(f"⚠️ Link Job 執行錯誤 (重試 {attempt+1}): {e}")
                    time.sleep(1)
            if not success:
                self.link_jobs[model_label + '_link'] = {
                    'job_id': None,
                    'status': 'parse_failed',
                    'raw_output': raw_capture[:800] if raw_capture else 'no_output'
                }
                logger.warning(f"⚠️ 無法解析 Link Job ID ({model_label}) - 已記錄 raw_output")
            if self.debug_link:
                log_path = f'link_attempt_{model_label}.log'
                try:
                    with open(log_path, 'w') as f:
                        f.write('\n'.join(attempt_logs) or raw_capture or 'no output captured')
                    logger.info(f"💾 已儲存 link 除錯紀錄: {log_path}")
                except Exception as e:
                    logger.warning(f"⚠️ 無法寫入除錯檔 {log_path}: {e}")

    def _wait_for_single_job(self, job_obj, label: str, timeout: int = 1800, poll: int = 10):
        """輪詢等待單一 job 完成。timeout 秒後放棄 (標記為 still_running)。"""
        start = time.time()
        while True:
            try:
                job_obj.wait(timeout=1)
                return True
            except Exception:
                pass
            elapsed = time.time() - start
            if elapsed >= timeout:
                logger.warning(f"⚠️ 等待超時 ({timeout}s) job 仍未完成: {label}")
                return False
            if int(elapsed) % (poll) == 0:
                logger.info(f"⏳ {label} 進行中... 已等待 {int(elapsed)}s")
            time.sleep(1)

    def wait_for_all_jobs(self):
        """等待所有 compile / profile job 完成（link 為 CLI 暫不輪詢）。"""
        logger.info("⏳ 等待所有 QAI Hub Jobs 完成 (compile + profile)...")
        unfinished = True
        last_status_emit = 0
        while unfinished:
            unfinished = False
            status_snapshot = {}
            # Compile jobs
            for name, job in self.compiled_models.items():
                try:
                    job.wait(timeout=1)
                    status_snapshot[name] = 'completed'
                except Exception:
                    status_snapshot[name] = 'running'
                    unfinished = True
            # Profile jobs
            for name, job in self.profile_jobs.items():
                try:
                    job.wait(timeout=1)
                    status_snapshot[name] = 'completed'
                except Exception:
                    status_snapshot[name] = 'running'
                    unfinished = True
            now = time.time()
            if now - last_status_emit > self.poll_interval:
                last_status_emit = now
                compiling = [k for k,v in status_snapshot.items() if v != 'completed']
                logger.info(f"📊 Job 狀態: 完成 {len(status_snapshot)-len(compiling)}/{len(status_snapshot)}; 進行中: {', '.join(compiling) if compiling else '無'}")
            if unfinished:
                time.sleep(self.poll_interval)
        logger.info("✅ 所有 compile / profile jobs 已完成")

    def export_pipeline_status(self, path: str = 'dragon_x_pipeline_status.json'):
        report = self.get_dragon_x_status_report()
        with open(path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"📝 Pipeline 狀態已輸出: {path}")

def main():
    """主函數：Dragon X老人跌倒預防檢測系統測試 / Pipeline"""
    parser = argparse.ArgumentParser(description='Dragon X 跌倒預防系統')
    parser.add_argument('--full-pipeline', action='store_true', help='執行 Compile→Profile→(Link) 完整流程並輸出狀態')
    parser.add_argument('--wait', action='store_true', help='等待所有雲端 Jobs 完成')
    parser.add_argument('--poll-interval', type=int, default=15, help='Job 輪詢秒數 (default:15)')
    parser.add_argument('--export-status', action='store_true', help='額外輸出 pipeline 狀態 JSON')
    parser.add_argument('--debug-link', action='store_true', help='輸出 link job 除錯資訊並保存 log 檔')
    parser.add_argument('--link-python', action='store_true', help='使用 Python API submit_link_job 對已編譯模型進行 link')
    parser.add_argument('--image', type=str, help='提供本地影像路徑以進行實際本地推論 (姿態)')
    args = parser.parse_args()

    print("🐉 Dragon X老人跌倒預防檢測系統")
    print("=" * 60)
    print("🎯 專為黑客松打造的Snapdragon X Elite平台解決方案")
    print()
    
    try:
        dragon_system = DragonXFallDetectionSystem(full_pipeline=args.full_pipeline, wait=args.wait, poll_interval=args.poll_interval, debug_link=args.debug_link, link_python=args.link_python)

        status_report = dragon_system.get_dragon_x_status_report()
        print("📊 Dragon X系統狀態:")
        print(f"   🐉 目標設備: {status_report['dragon_x_device']['name']}")
        print(f"   📱 設備狀態: {status_report['dragon_x_device']['status']}")
        print(f"   🧠 已載入模型: {len(status_report['models_status'])}")
        print(f"   ⚡ Compile Jobs: {len(status_report['qai_hub_jobs'])}")
        print(f"   📈 Profile Jobs: {len(status_report['profile_jobs'])}")
        print(f"   🔗 Link Jobs: {len(status_report['link_jobs'])}")
        print()

        print("🔗 Compile Jobs:")
        for job_name, job_info in status_report['qai_hub_jobs'].items():
            print(f"   {job_name}: {job_info['job_id']} ({job_info['status']})")
            print(f"      Dashboard: {job_info['dashboard_url']}")
        if status_report['profile_jobs']:
            print("\n📈 Profile Jobs:")
            for name, info in status_report['profile_jobs'].items():
                print(f"   {name}: {info['job_id']} ({info['status']})")
                print(f"      Dashboard: {info['dashboard_url']}")
        if status_report['link_jobs']:
            print("\n🔗 Link Jobs:")
            for name, info in status_report['link_jobs'].items():
                print(f"   {name}: {info.get('job_id') or 'N/A'} ({info.get('status')})")
                if 'dashboard_url' in info:
                    print(f"      Dashboard: {info['dashboard_url']}")

        print("\n🧪 測試跌倒預防檢測 (本地模擬)...")
        if args.image and os.path.exists(args.image):
            img = cv2.imread(args.image)
            if img is None:
                print(f"⚠️ 無法讀取影像 {args.image}，改用隨機圖像")
                img = np.random.randint(0,255,(480,640,3),dtype=np.uint8)
        else:
            if args.image:
                print(f"⚠️ 指定影像不存在: {args.image}，改用隨機圖像")
            img = np.random.randint(0,255,(480,640,3),dtype=np.uint8)
        detection_results = dragon_system.comprehensive_fall_prevention_detection(img)

        print("✅ 跌倒預防分析結果:")
        fall_analysis = detection_results.get('fall_prevention_analysis', {})
        print(f"   {fall_analysis.get('message', '未知狀態')}")
        print(f"   風險評分: {fall_analysis.get('risk_score', 0):.2f}")
        print(f"   建議: {fall_analysis.get('recommendation', '無建議')}")
        if fall_analysis.get('indicators'):
            print(f"   風險指標: {', '.join(fall_analysis['indicators'])}")

        # 保存報告
        with open('dragon_x_fall_detection_report.json', 'w') as f:
            json.dump({
                "status_report": status_report,
                "detection_results": detection_results
            }, f, indent=2, default=str)
        print("\n📝 Dragon X報告已保存: dragon_x_fall_detection_report.json")

        if args.export_status:
            dragon_system.export_pipeline_status()

        print("🎉 完成!")
        if args.full_pipeline:
            print("🏁 完整Pipeline已執行 (Compile→Profile→Link[嘗試])")
        else:
            print("ℹ️ 使用 --full-pipeline 可執行完整流程")
        print("💡 使用 --wait 可等待雲端Jobs完成, --export-status 輸出JSON狀態")

    except Exception as e:
        print(f"❌ Dragon X系統初始化失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
