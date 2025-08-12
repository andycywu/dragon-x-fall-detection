#!/usr/bin/env python3
"""
🌐 真正的QAI Hub + ONNX Runtime 檢測系統
使用真實API Token連接QAI Hub並部署到ONNX Runtime
"""

import os
import qai_hub as hub
import numpy as np
import cv2
import onnxruntime as ort
import tempfile
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Tuple, Optional
import time
import json

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealQAIHubONNXDetector:
    """真正的QAI Hub + ONNX Runtime檢測系統"""
    
    def __init__(self):
        """初始化檢測系統"""
        self.api_token = os.getenv('QAI_HUB_API_TOKEN')
        self.device_group = os.getenv('QAI_HUB_DEVICE_GROUP', 'default')
        self.enable_acceleration = os.getenv('ENABLE_QAI_ACCELERATION', 'true').lower() == 'true'
        
        # ONNX Runtime配置
        self.onnx_providers = self._get_onnx_providers()
        self.onnx_sessions = {}
        
        # QAI Hub模型緩存
        self.qai_hub_models = {}
        self.compiled_models = {}
        
        logger.info("🚀 初始化真正的QAI Hub + ONNX Runtime檢測系統...")
        self._verify_qai_hub_connection()
        self._initialize_models()
    
    def _verify_qai_hub_connection(self):
        """驗證QAI Hub連接"""
        if not self.api_token:
            raise ValueError("❌ 請在.env文件中設置QAI_HUB_API_TOKEN")
        
        try:
            # 測試連接
            devices = hub.get_devices()
            logger.info(f"✅ QAI Hub連接成功，可用設備數量: {len(devices)}")
            
            # 選擇目標設備
            target_devices = [d for d in devices if 'Samsung Galaxy S23' in d.name or 'Snapdragon' in d.name]
            if target_devices:
                self.target_device = target_devices[0]
                logger.info(f"🎯 選擇目標設備: {self.target_device.name}")
            else:
                # 使用第一個可用設備
                self.target_device = devices[0] if devices else None
                logger.info(f"🎯 使用設備: {self.target_device.name if self.target_device else 'None'}")
                
        except Exception as e:
            logger.error(f"❌ QAI Hub連接失敗: {e}")
            raise
    
    def _get_onnx_providers(self):
        """獲取ONNX Runtime提供商"""
        providers = []
        
        # 檢查可用的執行提供商
        available_providers = ort.get_available_providers()
        logger.info(f"📋 可用ONNX提供商: {available_providers}")
        
        # 優先順序：CUDA > DirectML > CPU
        if 'CUDAExecutionProvider' in available_providers:
            providers.append('CUDAExecutionProvider')
            logger.info("✅ 啟用CUDA加速")
        elif 'DmlExecutionProvider' in available_providers:
            providers.append('DmlExecutionProvider')
            logger.info("✅ 啟用DirectML加速")
        
        providers.append('CPUExecutionProvider')
        logger.info("✅ 添加CPU後備支援")
        
        return providers
    
    def _initialize_models(self):
        """初始化QAI Hub模型"""
        logger.info("📥 載入QAI Hub模型...")
        
        try:
            # MediaPipe Face Detection
            self._load_face_detection_model()
            
            # MediaPipe Pose Estimation  
            self._load_pose_estimation_model()
            
            # MediaPipe Hand Detection
            self._load_hand_detection_model()
            
            logger.info("✅ 所有QAI Hub模型載入完成")
            
        except Exception as e:
            logger.error(f"❌ 模型載入失敗: {e}")
            raise
    
    def _load_face_detection_model(self):
        """載入人臉檢測模型"""
        try:
            from qai_hub_models.models.mediapipe_face import Model as FaceModel
            
            logger.info("📱 載入MediaPipe Face Detection...")
            face_model = FaceModel.from_pretrained()
            self.qai_hub_models['face'] = face_model
            
            # 提交編譯Job到QAI Hub
            if self.enable_acceleration and self.target_device:
                logger.info("🔄 提交人臉檢測模型編譯Job...")
                
                compile_job = hub.submit_compile_job(
                    model=face_model,
                    input_specs={"image": ((1, 3, 192, 192), "float32")},
                    device=self.target_device,
                )
                
                logger.info(f"✅ 人臉檢測編譯Job提交: {compile_job.job_id}")
                logger.info(f"🔗 Dashboard: https://aihub.qualcomm.com/jobs/{compile_job.job_id}")
                
                # 等待編譯完成（異步）
                self.compiled_models['face_job'] = compile_job
            
            logger.info("✅ MediaPipe Face Detection載入完成")
            
        except Exception as e:
            logger.error(f"❌ 人臉檢測模型載入失敗: {e}")
    
    def _load_pose_estimation_model(self):
        """載入姿態估計模型"""
        try:
            from qai_hub_models.models.mediapipe_pose_estimation import Model as PoseModel
            
            logger.info("🚶 載入MediaPipe Pose Estimation...")
            pose_model = PoseModel.from_pretrained()
            self.qai_hub_models['pose'] = pose_model
            
            # 提交編譯Job到QAI Hub
            if self.enable_acceleration and self.target_device:
                logger.info("🔄 提交姿態估計模型編譯Job...")
                
                compile_job = hub.submit_compile_job(
                    model=pose_model,
                    input_specs={"image": ((1, 3, 256, 256), "float32")},
                    device=self.target_device,
                )
                
                logger.info(f"✅ 姿態估計編譯Job提交: {compile_job.job_id}")
                logger.info(f"🔗 Dashboard: https://aihub.qualcomm.com/jobs/{compile_job.job_id}")
                
                self.compiled_models['pose_job'] = compile_job
            
            logger.info("✅ MediaPipe Pose Estimation載入完成")
            
        except Exception as e:
            logger.error(f"❌ 姿態估計模型載入失敗: {e}")
    
    def _load_hand_detection_model(self):
        """載入手部檢測模型"""
        try:
            from qai_hub_models.models.mediapipe_hand import Model as HandModel
            
            logger.info("✋ 載入MediaPipe Hand Detection...")
            hand_model = HandModel.from_pretrained()
            self.qai_hub_models['hand'] = hand_model
            
            # 提交編譯Job到QAI Hub
            if self.enable_acceleration and self.target_device:
                logger.info("🔄 提交手部檢測模型編譯Job...")
                
                compile_job = hub.submit_compile_job(
                    model=hand_model,
                    input_specs={"image": ((1, 3, 224, 224), "float32")},
                    device=self.target_device,
                )
                
                logger.info(f"✅ 手部檢測編譯Job提交: {compile_job.job_id}")
                logger.info(f"🔗 Dashboard: https://aihub.qualcomm.com/jobs/{compile_job.job_id}")
                
                self.compiled_models['hand_job'] = compile_job
            
            logger.info("✅ MediaPipe Hand Detection載入完成")
            
        except Exception as e:
            logger.error(f"❌ 手部檢測模型載入失敗: {e}")
    
    def export_to_onnx(self, model_name: str) -> Optional[str]:
        """將QAI Hub模型導出為ONNX格式"""
        if model_name not in self.qai_hub_models:
            logger.error(f"❌ 模型 {model_name} 不存在")
            return None
        
        try:
            logger.info(f"📤 導出 {model_name} 模型為ONNX...")
            
            model = self.qai_hub_models[model_name]
            
            # 創建臨時文件保存ONNX模型
            onnx_path = f"qai_hub_{model_name}_model.onnx"
            
            # 根據模型類型設置輸入規格
            if model_name == 'face':
                sample_input = {"image": np.random.randn(1, 3, 192, 192).astype(np.float32)}
            elif model_name == 'pose':
                sample_input = {"image": np.random.randn(1, 3, 256, 256).astype(np.float32)}
            elif model_name == 'hand':
                sample_input = {"image": np.random.randn(1, 3, 224, 224).astype(np.float32)}
            else:
                sample_input = {"image": np.random.randn(1, 3, 224, 224).astype(np.float32)}
            
            # 使用QAI Hub導出ONNX
            onnx_model = hub.get_onnx_model(model, sample_input)
            
            # 保存ONNX文件
            with open(onnx_path, 'wb') as f:
                f.write(onnx_model.model)
            
            logger.info(f"✅ ONNX模型已保存: {onnx_path}")
            return onnx_path
            
        except Exception as e:
            logger.error(f"❌ ONNX導出失敗: {e}")
            return None
    
    def load_onnx_session(self, model_name: str, onnx_path: str):
        """載入ONNX Runtime會話"""
        try:
            logger.info(f"🔄 載入ONNX Runtime會話: {model_name}")
            
            # 配置ONNX Runtime會話選項
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.enable_cpu_mem_arena = True
            sess_options.enable_mem_pattern = True
            
            # 創建ONNX Runtime會話
            session = ort.InferenceSession(
                onnx_path,
                sess_options=sess_options,
                providers=self.onnx_providers
            )
            
            self.onnx_sessions[model_name] = session
            
            # 記錄模型信息
            input_info = [(inp.name, inp.shape, inp.type) for inp in session.get_inputs()]
            output_info = [(out.name, out.shape, out.type) for out in session.get_outputs()]
            
            logger.info(f"✅ ONNX會話載入成功: {model_name}")
            logger.info(f"   輸入: {input_info}")
            logger.info(f"   輸出: {output_info}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ ONNX會話載入失敗: {e}")
            return False
    
    def detect_with_onnx(self, image: np.ndarray, model_name: str) -> Dict[str, Any]:
        """使用ONNX Runtime進行檢測"""
        if model_name not in self.onnx_sessions:
            return {"error": f"ONNX會話 {model_name} 未載入"}
        
        try:
            session = self.onnx_sessions[model_name]
            
            # 預處理圖像
            processed_image = self._preprocess_image(image, model_name)
            
            # 準備輸入
            input_name = session.get_inputs()[0].name
            input_data = {input_name: processed_image}
            
            # 執行推理
            start_time = time.time()
            outputs = session.run(None, input_data)
            inference_time = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            # 後處理結果
            results = self._postprocess_results(outputs, model_name)
            results['inference_time_ms'] = inference_time
            results['model_name'] = f"QAI_Hub_{model_name}_ONNX"
            
            logger.info(f"⚡ {model_name} ONNX推理完成: {inference_time:.2f}ms")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ ONNX推理失敗: {e}")
            return {"error": str(e)}
    
    def _preprocess_image(self, image: np.ndarray, model_name: str) -> np.ndarray:
        """預處理圖像"""
        # 根據模型類型調整輸入尺寸
        if model_name == 'face':
            target_size = (192, 192)
        elif model_name == 'pose':
            target_size = (256, 256)
        elif model_name == 'hand':
            target_size = (224, 224)
        else:
            target_size = (224, 224)
        
        # 調整圖像大小
        resized = cv2.resize(image, target_size)
        
        # 轉換為RGB（如果需要）
        if len(resized.shape) == 3 and resized.shape[2] == 3:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # 正規化到[0,1]
        normalized = resized.astype(np.float32) / 255.0
        
        # 轉換為CHW格式並添加batch維度
        preprocessed = np.transpose(normalized, (2, 0, 1))
        preprocessed = np.expand_dims(preprocessed, axis=0)
        
        return preprocessed
    
    def _postprocess_results(self, outputs: list, model_name: str) -> Dict[str, Any]:
        """後處理檢測結果"""
        results = {
            "success": True,
            "detections": [],
            "raw_outputs": [out.tolist() for out in outputs]
        }
        
        try:
            if model_name == 'face':
                # 處理人臉檢測結果
                if len(outputs) >= 2:
                    boxes = outputs[0]  # 邊界框
                    scores = outputs[1]  # 置信度分數
                    
                    # 過濾高置信度檢測
                    threshold = 0.5
                    valid_detections = []
                    
                    for i in range(len(scores[0])):
                        if scores[0][i] > threshold:
                            valid_detections.append({
                                "box": boxes[0][i].tolist(),
                                "confidence": float(scores[0][i]),
                                "type": "face"
                            })
                    
                    results["detections"] = valid_detections
                    results["total_faces"] = len(valid_detections)
            
            elif model_name == 'pose':
                # 處理姿態檢測結果
                if len(outputs) >= 1:
                    keypoints = outputs[0]  # 關鍵點
                    
                    # 解析關鍵點
                    if keypoints.shape[-1] >= 51:  # 17個關鍵點 * 3 (x,y,confidence)
                        pose_keypoints = []
                        for i in range(0, 51, 3):
                            pose_keypoints.append({
                                "x": float(keypoints[0][i]),
                                "y": float(keypoints[0][i+1]),
                                "confidence": float(keypoints[0][i+2])
                            })
                        
                        results["detections"] = [{
                            "keypoints": pose_keypoints,
                            "type": "pose"
                        }]
                        results["total_poses"] = 1
            
            elif model_name == 'hand':
                # 處理手部檢測結果
                if len(outputs) >= 1:
                    hand_landmarks = outputs[0]
                    
                    # 解析手部關鍵點
                    results["detections"] = [{
                        "landmarks": hand_landmarks[0].tolist(),
                        "type": "hand"
                    }]
                    results["total_hands"] = 1
        
        except Exception as e:
            logger.error(f"❌ 結果後處理失敗: {e}")
            results["success"] = False
            results["error"] = str(e)
        
        return results
    
    def submit_profiling_job(self, model_name: str) -> Optional[str]:
        """提交profiling job到QAI Hub"""
        if model_name not in self.compiled_models:
            logger.error(f"❌ 編譯Job {model_name} 不存在")
            return None
        
        try:
            compile_job = self.compiled_models[f'{model_name}_job']
            
            logger.info(f"⏳ 等待 {model_name} 編譯完成...")
            
            # 等待編譯完成（設置超時）
            try:
                compile_job.wait(timeout=300)  # 5分鐘超時
            except Exception as e:
                logger.warning(f"⚠️ 編譯超時，但Job仍在進行: {e}")
                return compile_job.job_id
            
            if compile_job.success:
                logger.info(f"✅ {model_name} 編譯成功，提交profiling...")
                
                # 準備測試數據
                if model_name == 'face':
                    test_input = {"image": np.random.randn(1, 3, 192, 192).astype(np.float32)}
                elif model_name == 'pose':
                    test_input = {"image": np.random.randn(1, 3, 256, 256).astype(np.float32)}
                elif model_name == 'hand':
                    test_input = {"image": np.random.randn(1, 3, 224, 224).astype(np.float32)}
                
                # 提交profiling job
                profile_job = hub.submit_profile_job(
                    model=compile_job.get_target_model(),
                    input_data=test_input,
                    device=self.target_device,
                )
                
                logger.info(f"✅ {model_name} Profiling Job提交: {profile_job.job_id}")
                logger.info(f"🔗 Dashboard: https://aihub.qualcomm.com/jobs/{profile_job.job_id}")
                
                return profile_job.job_id
            else:
                logger.error(f"❌ {model_name} 編譯失敗: {compile_job.failure_reason}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Profiling job提交失敗: {e}")
            return None
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """獲取Job狀態"""
        try:
            job = hub.get_job(job_id)
            
            status_info = {
                "job_id": job_id,
                "status": job.status,
                "success": job.success if hasattr(job, 'success') else None,
                "failure_reason": getattr(job, 'failure_reason', None),
                "submitted_at": getattr(job, 'submitted_at', None),
                "dashboard_url": f"https://aihub.qualcomm.com/jobs/{job_id}"
            }
            
            return status_info
            
        except Exception as e:
            logger.error(f"❌ 獲取Job狀態失敗: {e}")
            return {"error": str(e)}
    
    def unified_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """統一檢測接口（ONNX + QAI Hub）"""
        results = {
            "timestamp": time.time(),
            "image_shape": image.shape,
            "detections": {},
            "performance": {},
            "qai_hub_jobs": {}
        }
        
        # 如果ONNX會話可用，使用ONNX Runtime
        for model_name in ['face', 'pose', 'hand']:
            if model_name in self.onnx_sessions:
                logger.info(f"🔄 使用ONNX Runtime檢測: {model_name}")
                detection_result = self.detect_with_onnx(image, model_name)
                results["detections"][model_name] = detection_result
                
                if "inference_time_ms" in detection_result:
                    results["performance"][f"{model_name}_inference_ms"] = detection_result["inference_time_ms"]
        
        # 記錄QAI Hub Job信息
        for model_name in ['face', 'pose', 'hand']:
            job_key = f'{model_name}_job'
            if job_key in self.compiled_models:
                job = self.compiled_models[job_key]
                results["qai_hub_jobs"][model_name] = {
                    "compile_job_id": job.job_id,
                    "dashboard_url": f"https://aihub.qualcomm.com/jobs/{job.job_id}"
                }
        
        # 統計總檢測數量
        total_detections = {}
        for model_name, detection in results["detections"].items():
            if "total_faces" in detection:
                total_detections["faces"] = detection["total_faces"]
            elif "total_poses" in detection:
                total_detections["poses"] = detection["total_poses"]
            elif "total_hands" in detection:
                total_detections["hands"] = detection["total_hands"]
        
        results["total_detections"] = total_detections
        
        return results

def main():
    """主函數：測試真實QAI Hub + ONNX系統"""
    print("🌐 真實QAI Hub + ONNX Runtime檢測系統測試")
    print("=" * 60)
    
    try:
        # 初始化檢測器
        detector = RealQAIHubONNXDetector()
        
        # 導出ONNX模型
        print("\n📤 導出ONNX模型...")
        for model_name in ['face', 'pose', 'hand']:
            if model_name in detector.qai_hub_models:
                onnx_path = detector.export_to_onnx(model_name)
                if onnx_path:
                    detector.load_onnx_session(model_name, onnx_path)
        
        # 提交profiling jobs
        print("\n🚀 提交Profiling Jobs...")
        profiling_jobs = {}
        for model_name in ['face', 'pose', 'hand']:
            job_id = detector.submit_profiling_job(model_name)
            if job_id:
                profiling_jobs[model_name] = job_id
        
        # 測試檢測
        print("\n🧪 測試ONNX Runtime檢測...")
        
        # 載入測試圖像
        test_images = ['andy.jpg', 'official_test_image.jpg']
        for img_path in test_images:
            if os.path.exists(img_path):
                print(f"\n📷 測試圖像: {img_path}")
                
                image = cv2.imread(img_path)
                if image is not None:
                    # 執行統一檢測
                    results = detector.unified_detection(image)
                    
                    print(f"✅ 檢測完成:")
                    print(f"   總檢測數量: {results.get('total_detections', {})}")
                    print(f"   性能指標: {results.get('performance', {})}")
                    
                    # 顯示QAI Hub Job信息
                    qai_jobs = results.get('qai_hub_jobs', {})
                    if qai_jobs:
                        print(f"   QAI Hub Jobs:")
                        for model, job_info in qai_jobs.items():
                            print(f"     {model}: {job_info['compile_job_id']}")
                            print(f"       Dashboard: {job_info['dashboard_url']}")
        
        # 檢查Job狀態
        print("\n📊 檢查QAI Hub Job狀態...")
        for model_name, job_id in profiling_jobs.items():
            status = detector.get_job_status(job_id)
            print(f"   {model_name}: {status.get('status', 'unknown')}")
        
        # 保存結果
        results_summary = {
            "system": "Real QAI Hub + ONNX Runtime",
            "timestamp": time.time(),
            "qai_hub_jobs": profiling_jobs,
            "onnx_models": list(detector.onnx_sessions.keys()),
            "target_device": detector.target_device.name if detector.target_device else None,
            "onnx_providers": detector.onnx_providers
        }
        
        with open('real_qai_hub_onnx_results.json', 'w') as f:
            json.dump(results_summary, f, indent=2)
        
        print(f"\n✅ 結果已保存: real_qai_hub_onnx_results.json")
        print(f"🎯 真實QAI Hub + ONNX系統測試完成！")
        
    except Exception as e:
        print(f"❌ 系統測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
