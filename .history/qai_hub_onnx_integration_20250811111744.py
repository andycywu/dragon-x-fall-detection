#!/usr/bin/env python3
"""
🌐 實用的QAI Hub + ONNX Runtime集成系統
真正連接QAI Hub並導出優化後的ONNX模型
"""

import os
import qai_hub as hub
import numpy as np
import cv2
import onnxruntime as ort
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import time
import json
import tempfile

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QAIHubONNXIntegration:
    """QAI Hub + ONNX Runtime集成系統"""
    
    def __init__(self):
        """初始化系統"""
        self.api_token = os.getenv('QAI_HUB_API_TOKEN')
        if not self.api_token:
            raise ValueError("❌ 請在.env文件中設置QAI_HUB_API_TOKEN")
        
        # ONNX Runtime配置
        self.onnx_providers = self._get_onnx_providers()
        self.onnx_sessions = {}
        
        # QAI Hub模型和Jobs
        self.models = {}
        self.compile_jobs = {}
        
        logger.info("🚀 初始化QAI Hub + ONNX集成系統...")
        self._verify_connection()
        
    def _verify_connection(self):
        """驗證QAI Hub連接"""
        try:
            devices = hub.get_devices()
            logger.info(f"✅ QAI Hub連接成功，可用設備: {len(devices)}")
            
            # 選擇目標設備
            self.target_device = devices[0] if devices else None
            if self.target_device:
                logger.info(f"🎯 目標設備: {self.target_device.name}")
        except Exception as e:
            logger.error(f"❌ QAI Hub連接失敗: {e}")
            raise
    
    def _get_onnx_providers(self):
        """獲取ONNX Runtime提供商"""
        providers = []
        available = ort.get_available_providers()
        
        if 'CUDAExecutionProvider' in available:
            providers.append('CUDAExecutionProvider')
            logger.info("✅ 啟用CUDA加速")
        elif 'DmlExecutionProvider' in available:
            providers.append('DmlExecutionProvider')
            logger.info("✅ 啟用DirectML加速")
        
        providers.append('CPUExecutionProvider')
        return providers
    
    def load_mediapipe_models(self):
        """載入MediaPipe模型"""
        logger.info("📥 載入MediaPipe模型...")
        
        model_configs = {
            'face': {
                'import_path': 'qai_hub_models.models.mediapipe_face',
                'input_shape': (1, 3, 192, 192),
                'description': 'MediaPipe Face Detection'
            },
            'pose': {
                'import_path': 'qai_hub_models.models.mediapipe_pose',
                'input_shape': (1, 3, 256, 256),
                'description': 'MediaPipe Pose Estimation'
            },
            'hand': {
                'import_path': 'qai_hub_models.models.mediapipe_hand',
                'input_shape': (1, 3, 224, 224),
                'description': 'MediaPipe Hand Detection'
            }
        }
        
        for model_name, config in model_configs.items():
            try:
                logger.info(f"📱 載入{config['description']}...")
                
                # 動態導入模型
                module_path = config['import_path']
                module = __import__(module_path, fromlist=['Model'])
                ModelClass = getattr(module, 'Model')
                
                # 創建模型實例
                model = ModelClass.from_pretrained()
                self.models[model_name] = {
                    'model': model,
                    'input_shape': config['input_shape'],
                    'description': config['description']
                }
                
                logger.info(f"✅ {config['description']}載入成功")
                
            except Exception as e:
                logger.error(f"❌ {config['description']}載入失敗: {e}")
    
    def submit_compile_jobs(self):
        """提交編譯Jobs到QAI Hub"""
        if not self.target_device:
            logger.error("❌ 沒有可用的目標設備")
            return
        
        logger.info("🔄 提交模型編譯Jobs...")
        
        for model_name, model_info in self.models.items():
            try:
                model = model_info['model']
                input_shape = model_info['input_shape']
                
                logger.info(f"📤 提交{model_info['description']}編譯Job...")
                
                # 提交編譯Job
                compile_job = hub.submit_compile_job(
                    model=model,
                    input_specs={"image": (input_shape, "float32")},
                    device=self.target_device,
                )
                
                self.compile_jobs[model_name] = compile_job
                
                logger.info(f"✅ {model_info['description']}編譯Job提交成功")
                logger.info(f"   Job ID: {compile_job.job_id}")
                logger.info(f"   Dashboard: https://aihub.qualcomm.com/jobs/{compile_job.job_id}")
                
            except Exception as e:
                logger.error(f"❌ {model_info['description']}編譯Job提交失敗: {e}")
    
    def export_onnx_models(self, wait_for_compilation=False):
        """導出ONNX模型"""
        logger.info("📤 導出ONNX模型...")
        
        for model_name, model_info in self.models.items():
            try:
                model = model_info['model']
                input_shape = model_info['input_shape']
                
                logger.info(f"🔄 導出{model_info['description']}為ONNX...")
                
                # 準備示例輸入
                sample_input = {"image": np.random.randn(*input_shape).astype(np.float32)}
                
                # 如果有編譯Job且等待編譯完成
                if wait_for_compilation and model_name in self.compile_jobs:
                    try:
                        logger.info(f"⏳ 等待{model_name}編譯完成...")
                        compile_job = self.compile_jobs[model_name]
                        compile_job.wait(timeout=180)  # 3分鐘超時
                        
                        if compile_job.success:
                            logger.info(f"✅ {model_name}編譯成功，使用優化後的模型")
                            # 使用編譯後的模型導出ONNX
                            optimized_model = compile_job.get_target_model()
                            onnx_model = hub.get_onnx_model(optimized_model, sample_input)
                        else:
                            logger.warning(f"⚠️ {model_name}編譯失敗，使用原始模型")
                            onnx_model = hub.get_onnx_model(model, sample_input)
                    except Exception as e:
                        logger.warning(f"⚠️ 等待編譯超時: {e}，使用原始模型")
                        onnx_model = hub.get_onnx_model(model, sample_input)
                else:
                    # 直接使用原始模型導出
                    onnx_model = hub.get_onnx_model(model, sample_input)
                
                # 保存ONNX文件
                onnx_path = f"qai_hub_{model_name}_optimized.onnx"
                with open(onnx_path, 'wb') as f:
                    f.write(onnx_model.model)
                
                logger.info(f"✅ {model_info['description']} ONNX已保存: {onnx_path}")
                
                # 載入ONNX Runtime會話
                self._load_onnx_session(model_name, onnx_path, model_info)
                
            except Exception as e:
                logger.error(f"❌ {model_info['description']} ONNX導出失敗: {e}")
    
    def _load_onnx_session(self, model_name: str, onnx_path: str, model_info: Dict):
        """載入ONNX Runtime會話"""
        try:
            logger.info(f"🔄 載入{model_name} ONNX Runtime會話...")
            
            # 配置會話選項
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # 創建會話
            session = ort.InferenceSession(
                onnx_path,
                sess_options=sess_options,
                providers=self.onnx_providers
            )
            
            self.onnx_sessions[model_name] = {
                'session': session,
                'input_shape': model_info['input_shape'],
                'description': model_info['description']
            }
            
            logger.info(f"✅ {model_name} ONNX會話載入成功")
            
        except Exception as e:
            logger.error(f"❌ {model_name} ONNX會話載入失敗: {e}")
    
    def detect(self, image: np.ndarray, model_name: str) -> Dict[str, Any]:
        """使用ONNX Runtime執行檢測"""
        if model_name not in self.onnx_sessions:
            return {"error": f"ONNX會話 {model_name} 未載入"}
        
        try:
            session_info = self.onnx_sessions[model_name]
            session = session_info['session']
            
            # 預處理圖像
            processed_image = self._preprocess_image(image, session_info['input_shape'])
            
            # 執行推理
            input_name = session.get_inputs()[0].name
            start_time = time.time()
            outputs = session.run(None, {input_name: processed_image})
            inference_time = (time.time() - start_time) * 1000
            
            # 處理結果
            results = self._process_outputs(outputs, model_name)
            results.update({
                'inference_time_ms': inference_time,
                'model_type': f"QAI_Hub_{model_name}_ONNX",
                'description': session_info['description']
            })
            
            logger.info(f"⚡ {model_name}檢測完成: {inference_time:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"❌ {model_name}檢測失敗: {e}")
            return {"error": str(e)}
    
    def _preprocess_image(self, image: np.ndarray, input_shape: tuple) -> np.ndarray:
        """預處理圖像"""
        target_size = (input_shape[3], input_shape[2])  # (width, height)
        
        # 調整大小
        resized = cv2.resize(image, target_size)
        
        # 轉換顏色空間
        if len(resized.shape) == 3:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # 正規化
        normalized = resized.astype(np.float32) / 255.0
        
        # 調整維度順序和添加batch維度
        preprocessed = np.transpose(normalized, (2, 0, 1))
        preprocessed = np.expand_dims(preprocessed, axis=0)
        
        return preprocessed
    
    def _process_outputs(self, outputs: list, model_name: str) -> Dict[str, Any]:
        """處理模型輸出"""
        results = {"success": True, "detections": []}
        
        try:
            if model_name == 'face' and len(outputs) >= 2:
                # 人臉檢測
                boxes = outputs[0]
                scores = outputs[1]
                
                threshold = 0.5
                for i, score in enumerate(scores[0]):
                    if score > threshold:
                        results["detections"].append({
                            "type": "face",
                            "confidence": float(score),
                            "box": boxes[0][i].tolist()
                        })
                        
                results["total_faces"] = len(results["detections"])
                
            elif model_name == 'pose' and len(outputs) >= 1:
                # 姿態檢測
                keypoints = outputs[0]
                if keypoints.shape[-1] >= 51:  # 17個關鍵點 * 3
                    pose_points = []
                    for i in range(0, 51, 3):
                        pose_points.append({
                            "x": float(keypoints[0][i]),
                            "y": float(keypoints[0][i+1]),
                            "confidence": float(keypoints[0][i+2])
                        })
                    
                    results["detections"] = [{
                        "type": "pose",
                        "keypoints": pose_points
                    }]
                    results["total_poses"] = 1
                    
            elif model_name == 'hand' and len(outputs) >= 1:
                # 手部檢測
                landmarks = outputs[0]
                results["detections"] = [{
                    "type": "hand",
                    "landmarks": landmarks[0].tolist()
                }]
                results["total_hands"] = 1
                
        except Exception as e:
            logger.error(f"❌ 輸出處理失敗: {e}")
            results["success"] = False
            results["error"] = str(e)
        
        return results
    
    def unified_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """統一檢測接口"""
        results = {
            "timestamp": time.time(),
            "image_shape": image.shape,
            "detections": {},
            "performance": {},
            "total_detections": {}
        }
        
        # 執行所有可用的檢測
        for model_name in self.onnx_sessions.keys():
            detection_result = self.detect(image, model_name)
            results["detections"][model_name] = detection_result
            
            if "inference_time_ms" in detection_result:
                results["performance"][f"{model_name}_ms"] = detection_result["inference_time_ms"]
            
            # 統計檢測數量
            if "total_faces" in detection_result:
                results["total_detections"]["faces"] = detection_result["total_faces"]
            elif "total_poses" in detection_result:
                results["total_detections"]["poses"] = detection_result["total_poses"]
            elif "total_hands" in detection_result:
                results["total_detections"]["hands"] = detection_result["total_hands"]
        
        return results
    
    def get_job_statuses(self) -> Dict[str, Any]:
        """獲取所有Job狀態"""
        statuses = {}
        for model_name, job in self.compile_jobs.items():
            try:
                statuses[model_name] = {
                    "job_id": job.job_id,
                    "status": job.status,
                    "dashboard": f"https://aihub.qualcomm.com/jobs/{job.job_id}"
                }
            except Exception as e:
                statuses[model_name] = {"error": str(e)}
        
        return statuses

def demo():
    """演示QAI Hub + ONNX集成系統"""
    print("🌐 QAI Hub + ONNX Runtime集成系統演示")
    print("=" * 50)
    
    try:
        # 初始化系統
        system = QAIHubONNXIntegration()
        
        # 載入模型
        system.load_mediapipe_models()
        
        # 提交編譯Jobs
        system.submit_compile_jobs()
        
        # 導出ONNX模型（不等待編譯完成，使用原始模型）
        system.export_onnx_models(wait_for_compilation=False)
        
        # 測試檢測
        print("\n🧪 測試檢測...")
        test_images = ['andy.jpg', 'official_test_image.jpg']
        
        for img_path in test_images:
            if os.path.exists(img_path):
                print(f"\n📷 測試: {img_path}")
                image = cv2.imread(img_path)
                
                if image is not None:
                    results = system.unified_detection(image)
                    print(f"   檢測結果: {results['total_detections']}")
                    print(f"   性能: {results['performance']}")
        
        # 檢查Job狀態
        print("\n📊 QAI Hub Job狀態:")
        statuses = system.get_job_statuses()
        for model_name, status in statuses.items():
            print(f"   {model_name}: {status}")
        
        # 保存結果摘要
        summary = {
            "system": "QAI Hub + ONNX Runtime Integration",
            "timestamp": time.time(),
            "loaded_models": list(system.models.keys()),
            "onnx_sessions": list(system.onnx_sessions.keys()),
            "job_statuses": statuses,
            "providers": system.onnx_providers
        }
        
        with open('qai_hub_onnx_integration_results.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✅ 演示完成！結果已保存到 qai_hub_onnx_integration_results.json")
        
    except Exception as e:
        print(f"❌ 演示失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo()
