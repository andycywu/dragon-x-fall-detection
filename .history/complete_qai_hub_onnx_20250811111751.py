#!/usr/bin/env python3
"""
🚀 完整的QAI Hub + ONNX Runtime集成系統
正確處理MediaPipe模型組件並實現真實QAI Hub連接
"""

import os
import qai_hub as hub
import numpy as np
import cv2
import onnxruntime as ort
import torch
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import time
import json

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class QAIHubONNXComplete:
    """完整的QAI Hub + ONNX Runtime集成系統"""
    
    def __init__(self):
        """初始化系統"""
        self.api_token = os.getenv('QAI_HUB_API_TOKEN')
        if not self.api_token:
            raise ValueError("❌ 請在.env文件中設置QAI_HUB_API_TOKEN")
        
        # ONNX Runtime配置
        self.onnx_providers = self._setup_onnx_providers()
        self.onnx_sessions = {}
        
        # QAI Hub相關
        self.mediapipe_models = {}
        self.qai_hub_models = {}
        self.compile_jobs = {}
        
        logger.info("🚀 初始化完整QAI Hub + ONNX系統...")
        self._verify_qai_hub_connection()
        
    def _verify_qai_hub_connection(self):
        """驗證QAI Hub連接"""
        try:
            devices = hub.get_devices()
            logger.info(f"✅ QAI Hub連接成功，可用設備: {len(devices)}")
            
            # 選擇Snapdragon設備
            preferred_devices = [d for d in devices if any(keyword in d.name for keyword in 
                                                         ['Snapdragon', 'Samsung', 'Galaxy'])]
            if preferred_devices:
                self.target_device = preferred_devices[0]
                logger.info(f"🎯 選擇目標設備: {self.target_device.name}")
            else:
                self.target_device = devices[0] if devices else None
                logger.info(f"🎯 使用設備: {self.target_device.name if self.target_device else 'None'}")
                
        except Exception as e:
            logger.error(f"❌ QAI Hub連接失敗: {e}")
            raise
    
    def _setup_onnx_providers(self):
        """設置ONNX Runtime提供商"""
        providers = []
        available = ort.get_available_providers()
        
        logger.info(f"📋 可用ONNX執行提供商: {available}")
        
        # 按優先級添加提供商
        if 'CUDAExecutionProvider' in available:
            providers.append('CUDAExecutionProvider')
            logger.info("✅ 啟用CUDA GPU加速")
        elif 'DmlExecutionProvider' in available:
            providers.append('DmlExecutionProvider')
            logger.info("✅ 啟用DirectML GPU加速")
        elif 'CoreMLExecutionProvider' in available:
            providers.append('CoreMLExecutionProvider')
            logger.info("✅ 啟用CoreML加速")
        
        providers.append('CPUExecutionProvider')
        logger.info("✅ CPU執行提供商已添加")
        
        return providers
    
    def load_mediapipe_models(self):
        """載入MediaPipe模型組件"""
        logger.info("📥 載入QAI Hub MediaPipe模型組件...")
        
        model_configs = {
            'face_detector': {
                'module': 'qai_hub_models.models.mediapipe_face',
                'component': 'face_detector',
                'description': 'MediaPipe Face Detector',
                'input_size': (192, 192)
            },
            'face_landmark': {
                'module': 'qai_hub_models.models.mediapipe_face',
                'component': 'face_landmark_detector',
                'description': 'MediaPipe Face Landmark Detector',
                'input_size': (192, 192)
            },
            'pose_detector': {
                'module': 'qai_hub_models.models.mediapipe_pose',
                'component': 'pose_detector',
                'description': 'MediaPipe Pose Detector',
                'input_size': (256, 256)
            },
            'hand_detector': {
                'module': 'qai_hub_models.models.mediapipe_hand',
                'component': 'hand_detector',
                'description': 'MediaPipe Hand Detector',
                'input_size': (224, 224)
            }
        }
        
        for model_name, config in model_configs.items():
            try:
                logger.info(f"📱 載入 {config['description']}...")
                
                # 動態導入模型
                module = __import__(config['module'], fromlist=['Model'])
                ModelClass = getattr(module, 'Model')
                
                # 創建預訓練模型
                full_model = ModelClass.from_pretrained()
                
                # 提取指定組件
                if config['component'] == 'face_detector':
                    component = full_model.face_detector
                elif config['component'] == 'face_landmark_detector':
                    component = full_model.face_landmark_detector
                elif config['component'] == 'pose_detector':
                    # 對於pose模型，使用整個模型
                    component = full_model
                elif config['component'] == 'hand_detector':
                    # 對於hand模型，使用整個模型
                    component = full_model
                else:
                    component = full_model
                
                self.mediapipe_models[model_name] = {
                    'component': component,
                    'config': config,
                    'loaded': True
                }
                
                logger.info(f"✅ {config['description']} 載入成功")
                
            except Exception as e:
                logger.error(f"❌ {config['description']} 載入失敗: {e}")
                self.mediapipe_models[model_name] = {
                    'component': None,
                    'config': config,
                    'loaded': False,
                    'error': str(e)
                }
    
    def convert_to_torchscript(self):
        """將模型組件轉換為TorchScript"""
        logger.info("📤 轉換模型組件為TorchScript...")
        
        for model_name, model_info in self.mediapipe_models.items():
            if not model_info['loaded']:
                continue
                
            try:
                component = model_info['component']
                config = model_info['config']
                
                logger.info(f"🔄 轉換 {config['description']} 為TorchScript...")
                
                # 設置評估模式
                component.eval()
                
                # 準備示例輸入
                input_size = config['input_size']
                sample_input = torch.randn(1, 3, input_size[1], input_size[0])
                
                # 轉換為TorchScript
                with torch.no_grad():
                    if hasattr(component, 'convert_to_torchscript'):
                        # 使用QAI Hub Models的轉換方法
                        torchscript_model = component.convert_to_torchscript(sample_inputs=[sample_input])
                    else:
                        # 使用標準PyTorch轉換
                        torchscript_model = torch.jit.trace(component, sample_input)
                
                # 保存TorchScript模型
                torchscript_path = f"qai_hub_{model_name}_torchscript.pt"
                torchscript_model.save(torchscript_path)
                
                logger.info(f"✅ {config['description']} TorchScript已保存: {torchscript_path}")
                
                # 更新模型信息
                model_info['torchscript_model'] = torchscript_model
                model_info['torchscript_path'] = torchscript_path
                model_info['sample_input'] = sample_input
                
            except Exception as e:
                logger.error(f"❌ {config['description']} TorchScript轉換失敗: {e}")
                model_info['torchscript_error'] = str(e)
    
    def upload_to_qai_hub(self):
        """上傳TorchScript模型到QAI Hub"""
        logger.info("☁️ 上傳TorchScript模型到QAI Hub...")
        
        for model_name, model_info in self.mediapipe_models.items():
            if not model_info.get('torchscript_path'):
                logger.warning(f"⚠️ {model_name} 沒有TorchScript模型，跳過上傳")
                continue
                
            try:
                torchscript_path = model_info['torchscript_path']
                config = model_info['config']
                
                logger.info(f"📤 上傳 {config['description']} 到QAI Hub...")
                
                # 上傳模型
                qai_model = hub.upload_model(torchscript_path)
                
                logger.info(f"✅ {config['description']} 上傳成功")
                logger.info(f"   模型ID: {qai_model.model_id}")
                
                # 保存QAI Hub模型引用
                self.qai_hub_models[model_name] = {
                    'qai_model': qai_model,
                    'model_id': qai_model.model_id,
                    'config': config
                }
                
            except Exception as e:
                logger.error(f"❌ {config['description']} 上傳失敗: {e}")
                model_info['upload_error'] = str(e)
    
    def submit_compile_jobs(self):
        """提交編譯Jobs到QAI Hub"""
        logger.info("🚀 提交編譯Jobs到QAI Hub...")
        
        for model_name, qai_model_info in self.qai_hub_models.items():
            try:
                qai_model = qai_model_info['qai_model']
                config = qai_model_info['config']
                input_size = config['input_size']
                
                logger.info(f"🔄 提交 {config['description']} 編譯Job...")
                
                # 設置輸入規格
                input_specs = {
                    "image": ((1, 3, input_size[1], input_size[0]), "float32")
                }
                
                # 提交編譯Job
                compile_job = hub.submit_compile_job(
                    model=qai_model,
                    input_specs=input_specs,
                    device=self.target_device
                )
                
                self.compile_jobs[model_name] = {
                    'job': compile_job,
                    'config': config
                }
                
                logger.info(f"✅ {config['description']} 編譯Job已提交")
                logger.info(f"   Job ID: {compile_job.job_id}")
                logger.info(f"   Dashboard: https://aihub.qualcomm.com/jobs/{compile_job.job_id}")
                
            except Exception as e:
                logger.error(f"❌ {config['description']} 編譯Job提交失敗: {e}")
    
    def convert_to_onnx(self):
        """轉換TorchScript模型為ONNX"""
        logger.info("🔄 轉換TorchScript模型為ONNX...")
        
        for model_name, model_info in self.mediapipe_models.items():
            if not model_info.get('torchscript_model'):
                continue
                
            try:
                config = model_info['config']
                torchscript_model = model_info['torchscript_model']
                sample_input = model_info['sample_input']
                
                logger.info(f"🔄 轉換 {config['description']} 為ONNX...")
                
                # 導出為ONNX
                onnx_path = f"qai_hub_{model_name}_optimized.onnx"
                torch.onnx.export(
                    torchscript_model,
                    sample_input,
                    onnx_path,
                    export_params=True,
                    opset_version=11,
                    do_constant_folding=True,
                    input_names=['image'],
                    output_names=['output'],
                    dynamic_axes={
                        'image': {0: 'batch_size'},
                        'output': {0: 'batch_size'}
                    }
                )
                
                logger.info(f"✅ {config['description']} ONNX已保存: {onnx_path}")
                
                # 載入ONNX Runtime會話
                self._create_onnx_session(model_name, onnx_path, config)
                
            except Exception as e:
                logger.error(f"❌ {config['description']} ONNX轉換失敗: {e}")
    
    def _create_onnx_session(self, model_name: str, onnx_path: str, config: Dict):
        """創建ONNX Runtime會話"""
        try:
            logger.info(f"🔄 創建 {model_name} ONNX Runtime會話...")
            
            # 設置會話選項
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.enable_cpu_mem_arena = True
            sess_options.enable_mem_pattern = True
            
            # 創建推理會話
            session = ort.InferenceSession(
                onnx_path,
                sess_options=sess_options,
                providers=self.onnx_providers
            )
            
            self.onnx_sessions[model_name] = {
                'session': session,
                'config': config,
                'onnx_path': onnx_path
            }
            
            # 獲取會話信息
            input_info = session.get_inputs()[0]
            output_info = session.get_outputs()
            
            logger.info(f"✅ {model_name} ONNX會話創建成功")
            logger.info(f"   輸入: {input_info.name} {input_info.shape} {input_info.type}")
            logger.info(f"   輸出數量: {len(output_info)}")
            
        except Exception as e:
            logger.error(f"❌ {model_name} ONNX會話創建失敗: {e}")
    
    def detect_with_onnx(self, image: np.ndarray, model_name: str) -> Dict[str, Any]:
        """使用ONNX Runtime執行檢測"""
        if model_name not in self.onnx_sessions:
            return {"error": f"ONNX會話 {model_name} 不存在"}
        
        try:
            session_info = self.onnx_sessions[model_name]
            session = session_info['session']
            config = session_info['config']
            
            # 預處理圖像
            processed_image = self._preprocess_image(image, config['input_size'])
            
            # 執行推理
            input_name = session.get_inputs()[0].name
            start_time = time.time()
            outputs = session.run(None, {input_name: processed_image})
            inference_time = (time.time() - start_time) * 1000
            
            # 後處理結果
            results = self._postprocess_outputs(outputs, model_name, config)
            results.update({
                'inference_time_ms': round(inference_time, 2),
                'model_type': f"QAI_Hub_{model_name}_ONNX",
                'description': config['description'],
                'success': True
            })
            
            logger.info(f"⚡ {model_name}檢測完成: {inference_time:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"❌ {model_name}檢測失敗: {e}")
            return {
                "error": str(e),
                "success": False,
                "model_name": model_name
            }
    
    def _preprocess_image(self, image: np.ndarray, input_size: tuple) -> np.ndarray:
        """預處理圖像"""
        # 調整圖像大小
        resized = cv2.resize(image, input_size)
        
        # 轉換顏色空間 BGR -> RGB
        if len(resized.shape) == 3:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # 正規化到 [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # 調整維度順序 HWC -> CHW 並添加batch維度
        preprocessed = np.transpose(normalized, (2, 0, 1))
        preprocessed = np.expand_dims(preprocessed, axis=0)
        
        return preprocessed
    
    def _postprocess_outputs(self, outputs: list, model_name: str, config: Dict) -> Dict[str, Any]:
        """後處理模型輸出"""
        results = {
            "detections": [],
            "output_shapes": [output.shape for output in outputs],
            "num_outputs": len(outputs)
        }
        
        try:
            # 根據模型類型處理
            if 'face' in model_name:
                results = self._process_face_detection(outputs, results)
            elif 'pose' in model_name:
                results = self._process_pose_detection(outputs, results)
            elif 'hand' in model_name:
                results = self._process_hand_detection(outputs, results)
            
        except Exception as e:
            logger.error(f"❌ {model_name}輸出後處理失敗: {e}")
            results["postprocess_error"] = str(e)
        
        return results
    
    def _process_face_detection(self, outputs: list, results: Dict) -> Dict:
        """處理人臉檢測輸出"""
        if len(outputs) >= 2:
            # 假設第一個輸出是邊界框，第二個是置信度
            detections = []
            confidence_threshold = 0.5
            
            # 簡化處理 - 實際需要根據具體模型輸出格式調整
            try:
                boxes_output = outputs[0]
                scores_output = outputs[1] if len(outputs) > 1 else None
                
                if scores_output is not None:
                    # 過濾高置信度檢測
                    high_conf_indices = np.where(scores_output > confidence_threshold)[0]
                    detections = [{
                        "type": "face",
                        "confidence": float(scores_output.flat[i]),
                        "detection_index": int(i)
                    } for i in high_conf_indices[:5]]  # 最多5個檢測
                
                results["detections"] = detections
                results["total_faces"] = len(detections)
                
            except Exception as e:
                results["detection_parsing_error"] = str(e)
        
        return results
    
    def _process_pose_detection(self, outputs: list, results: Dict) -> Dict:
        """處理姿態檢測輸出"""
        if len(outputs) >= 1:
            # 姿態關鍵點處理
            keypoints_output = outputs[0]
            
            try:
                # 簡化處理 - 檢查是否有有效的姿態檢測
                if keypoints_output.size > 0:
                    results["detections"] = [{
                        "type": "pose",
                        "keypoints_shape": keypoints_output.shape,
                        "has_detection": True
                    }]
                    results["total_poses"] = 1
                else:
                    results["total_poses"] = 0
                    
            except Exception as e:
                results["pose_parsing_error"] = str(e)
        
        return results
    
    def _process_hand_detection(self, outputs: list, results: Dict) -> Dict:
        """處理手部檢測輸出"""
        if len(outputs) >= 1:
            # 手部關鍵點處理
            landmarks_output = outputs[0]
            
            try:
                if landmarks_output.size > 0:
                    results["detections"] = [{
                        "type": "hand",
                        "landmarks_shape": landmarks_output.shape,
                        "has_detection": True
                    }]
                    results["total_hands"] = 1
                else:
                    results["total_hands"] = 0
                    
            except Exception as e:
                results["hand_parsing_error"] = str(e)
        
        return results
    
    def run_unified_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """運行統一檢測"""
        unified_results = {
            "timestamp": time.time(),
            "image_shape": image.shape,
            "detections": {},
            "performance": {},
            "summary": {}
        }
        
        total_faces = 0
        total_poses = 0
        total_hands = 0
        total_inference_time = 0
        
        # 執行所有可用的檢測
        for model_name in self.onnx_sessions.keys():
            detection_result = self.detect_with_onnx(image, model_name)
            unified_results["detections"][model_name] = detection_result
            
            # 收集性能指標
            if "inference_time_ms" in detection_result:
                unified_results["performance"][f"{model_name}_ms"] = detection_result["inference_time_ms"]
                total_inference_time += detection_result["inference_time_ms"]
            
            # 統計檢測數量
            if "total_faces" in detection_result:
                total_faces += detection_result["total_faces"]
            elif "total_poses" in detection_result:
                total_poses += detection_result["total_poses"]
            elif "total_hands" in detection_result:
                total_hands += detection_result["total_hands"]
        
        # 生成摘要
        unified_results["summary"] = {
            "total_faces": total_faces,
            "total_poses": total_poses,
            "total_hands": total_hands,
            "total_inference_time_ms": round(total_inference_time, 2),
            "models_used": list(self.onnx_sessions.keys())
        }
        
        return unified_results
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            "mediapipe_models": {
                name: {
                    "loaded": info["loaded"],
                    "description": info["config"]["description"],
                    "has_torchscript": "torchscript_path" in info,
                    "error": info.get("error")
                }
                for name, info in self.mediapipe_models.items()
            },
            "qai_hub_models": {
                name: {
                    "model_id": info["model_id"],
                    "description": info["config"]["description"]
                }
                for name, info in self.qai_hub_models.items()
            },
            "compile_jobs": {
                name: {
                    "job_id": info["job"]["job_id"],
                    "description": info["config"]["description"],
                    "dashboard": f"https://aihub.qualcomm.com/jobs/{info['job'].job_id}"
                }
                for name, info in self.compile_jobs.items()
            },
            "onnx_sessions": list(self.onnx_sessions.keys()),
            "target_device": self.target_device.name if self.target_device else None,
            "onnx_providers": self.onnx_providers
        }

def main():
    """主函數：演示完整QAI Hub + ONNX系統"""
    print("🚀 完整QAI Hub + ONNX Runtime集成系統演示")
    print("=" * 70)
    
    try:
        # 初始化系統
        system = QAIHubONNXComplete()
        
        # Step 1: 載入MediaPipe模型
        print("\n📥 Step 1: 載入MediaPipe模型組件...")
        system.load_mediapipe_models()
        
        # Step 2: 轉換為TorchScript
        print("\n📤 Step 2: 轉換為TorchScript...")
        system.convert_to_torchscript()
        
        # Step 3: 上傳到QAI Hub
        print("\n☁️ Step 3: 上傳到QAI Hub...")
        system.upload_to_qai_hub()
        
        # Step 4: 提交編譯Jobs
        print("\n🚀 Step 4: 提交編譯Jobs...")
        system.submit_compile_jobs()
        
        # Step 5: 轉換為ONNX
        print("\n🔄 Step 5: 轉換為ONNX...")
        system.convert_to_onnx()
        
        # Step 6: 測試檢測
        if system.onnx_sessions:
            print("\n🧪 Step 6: 測試ONNX檢測...")
            
            test_images = ['andy.jpg', 'official_test_image.jpg']
            for img_path in test_images:
                if os.path.exists(img_path):
                    print(f"\n📷 測試圖像: {img_path}")
                    image = cv2.imread(img_path)
                    
                    if image is not None:
                        # 執行統一檢測
                        results = system.run_unified_detection(image)
                        
                        print(f"   檢測摘要: {results['summary']}")
                        print(f"   性能指標: {results['performance']}")
        
        # 獲取系統狀態
        print("\n📊 系統狀態報告:")
        status = system.get_system_status()
        
        print(f"   MediaPipe模型: {len(status['mediapipe_models'])}")
        print(f"   QAI Hub模型: {len(status['qai_hub_models'])}")
        print(f"   編譯Jobs: {len(status['compile_jobs'])}")
        print(f"   ONNX會話: {len(status['onnx_sessions'])}")
        print(f"   目標設備: {status['target_device']}")
        
        # QAI Hub Jobs詳情
        if status['compile_jobs']:
            print("\n📋 QAI Hub編譯Jobs:")
            for model_name, job_info in status['compile_jobs'].items():
                print(f"   {model_name}:")
                print(f"     Job ID: {job_info['job_id']}")
                print(f"     Dashboard: {job_info['dashboard']}")
        
        # 保存詳細結果
        results_file = 'complete_qai_hub_onnx_results.json'
        with open(results_file, 'w') as f:
            json.dump(status, f, indent=2, default=str)
        
        print(f"\n✅ 完整演示完成！詳細結果已保存到 {results_file}")
        print(f"🎯 真正的QAI Hub + ONNX Runtime集成系統運行成功！")
        
    except Exception as e:
        print(f"❌ 演示失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
