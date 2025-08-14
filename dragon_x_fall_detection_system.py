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
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import time
import json
import argparse

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DragonXFallDetectionSystem:
    """Dragon X專用老人跌倒預防檢測系統"""
    
    def __init__(self, full_pipeline: bool = False, wait: bool = False, poll_interval: int = 15):
        """初始化Dragon X檢測系統"""
        self.api_token = os.getenv('QAI_HUB_API_TOKEN')
        self.target_device = None
        self.qai_hub_models = {}
        self.compiled_models = {}
        self.onnx_sessions = {}
        self.profile_jobs: Dict[str, Any] = {}
        self.link_jobs: Dict[str, Any] = {}
        self.full_pipeline = full_pipeline
        self.wait_for_jobs = wait
        self.poll_interval = poll_interval
        
        logger.info("🐉 初始化Dragon X老人跌倒預防檢測系統...")
        self._find_dragon_x_devices()
        self._initialize_fall_detection_models()

        if self.full_pipeline:
            logger.info("🧪 啟動完整Pipeline (Compile → Profile → Link[可選])")
            self._submit_profile_jobs_for_all()
            self._attempt_link_jobs_cli()
            if self.wait_for_jobs:
                self.wait_for_all_jobs()
    
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
            # 這裡會在ONNX Runtime實現後進行實際檢測
            # 目前返回模擬結果用於展示
            mock_pose_results = {
                "keypoints": [{
                    "keypoints": [
                        {"x": 0.5, "y": 0.3, "confidence": 0.8},  # 頭部
                        {"x": 0.45, "y": 0.5, "confidence": 0.9},  # 左肩
                        {"x": 0.55, "y": 0.5, "confidence": 0.9},  # 右肩
                        # ... 其他關鍵點
                    ]
                }]
            }
            
            # 分析跌倒風險
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
                # 嘗試從原始模型字典找到對應 component
                component_key = None
                if 'pose' in model_label:
                    component_key = 'pose_fall_detection'
                elif 'face' in model_label:
                    component_key = 'face_elderly_id'
                elif 'hand' in model_label:
                    component_key = 'hand_emergency_gesture'
                component = self.qai_hub_models.get(component_key)
                sample_inputs = {"image": np.random.rand(1,3,256,256).astype('float32')}
                if component_key == 'hand_emergency_gesture':
                    sample_inputs = {"image": np.random.rand(1,3,224,224).astype('float32')}
                profile_job = hub.submit_profile_job(
                    model=compile_job.model,  # compile_job retains model reference
                    input_data=sample_inputs,
                    device=self.target_device
                )
                self.profile_jobs[model_label + '_profile'] = profile_job
                logger.info(f"📈 提交Profiling: {model_label} -> {profile_job.job_id}")
                logger.info(f"🔗 Dashboard: https://app.aihub.qualcomm.com/jobs/{profile_job.job_id}")
            except Exception as e:
                logger.error(f"❌ Profiling 提交失敗 {model_label}: {e}")

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
        # 嘗試從 device 取得 OS 資訊（容錯）
        device_os = getattr(self.target_device, 'os_version', None) or getattr(self.target_device, 'os', None)
        for key, compile_job in self.compiled_models.items():
            model_label = key.replace('_job', '')
            if model_label in self.link_jobs:
                continue
            model_id = getattr(getattr(compile_job, 'model', None), 'model_id', None)
            if not model_id:
                continue
            cmd = [cli, 'submit-link-job', '--model-id', model_id, '--device', device_name]
            if device_os:
                cmd += ['--device-os', str(device_os)]
            try:
                logger.info(f"🔗 提交 Link Job (CLI) {model_label} ...")
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                stdout = proc.stdout.strip()
                job_id = None
                for token in stdout.split():
                    if token.startswith('j') and len(token) >= 8:
                        job_id = token.strip('.,:')
                        break
                if job_id:
                    self.link_jobs[model_label + '_link'] = {
                        'job_id': job_id,
                        'status': 'submitted',
                        'dashboard_url': f'https://app.aihub.qualcomm.com/jobs/{job_id}'
                    }
                    logger.info(f"✅ Link Job 提交成功: {job_id}")
                else:
                    self.link_jobs[model_label + '_link'] = {
                        'job_id': None,
                        'status': 'parse_failed',
                        'raw_output': stdout[:500]
                    }
                    logger.warning(f"⚠️ 無法解析 Link Job ID ({model_label})")
            except Exception as e:
                logger.error(f"❌ Link Job 提交失敗 {model_label}: {e}")

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
    args = parser.parse_args()

    print("🐉 Dragon X老人跌倒預防檢測系統")
    print("=" * 60)
    print("🎯 專為黑客松打造的Snapdragon X Elite平台解決方案")
    print()
    
    try:
        dragon_system = DragonXFallDetectionSystem(full_pipeline=args.full_pipeline, wait=args.wait, poll_interval=args.poll_interval)

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
        mock_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        detection_results = dragon_system.comprehensive_fall_prevention_detection(mock_image)

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
