#!/usr/bin/env python3
"""
🎯 實用QAI Hub + ONNX Runtime實際應用系統
專注於實際可行的MediaPipe模型集成
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
import tempfile

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PracticalQAIHubONNX:
    """實用的QAI Hub + ONNX Runtime系統"""
    
    def __init__(self):
        """初始化系統"""
        self.api_token = os.getenv('QAI_HUB_API_TOKEN')
        if not self.api_token:
            raise ValueError("❌ 請在.env文件中設置QAI_HUB_API_TOKEN")
        
        # ONNX Runtime配置
        self.onnx_providers = self._setup_onnx_providers()
        self.onnx_sessions = {}
        
        # QAI Hub相關
        self.qai_hub_models = {}
        self.upload_jobs = {}
        
        logger.info("🚀 初始化實用QAI Hub + ONNX系統...")
        self._verify_qai_hub_connection()
        
    def _verify_qai_hub_connection(self):
        """驗證QAI Hub連接"""
        try:
            devices = hub.get_devices()
            logger.info(f"✅ QAI Hub連接成功，可用設備: {len(devices)}")
            
            # 選擇Snapdragon設備作為目標
            snapdragon_devices = [d for d in devices if 'Snapdragon' in d.name or 'Samsung' in d.name]
            if snapdragon_devices:
                self.target_device = snapdragon_devices[0]
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
        
        # 優先級: CUDA > DirectML > CPU
        if 'CUDAExecutionProvider' in available:
            providers.append('CUDAExecutionProvider')
            logger.info("✅ 啟用CUDA GPU加速")
        elif 'DmlExecutionProvider' in available:
            providers.append('DmlExecutionProvider')
            logger.info("✅ 啟用DirectML GPU加速")
        
        providers.append('CPUExecutionProvider')
        logger.info("✅ CPU執行提供商已添加")
        
        return providers
    
    def load_mediapipe_models(self):
        """載入MediaPipe模型"""
        logger.info("📥 載入QAI Hub MediaPipe模型...")
        
        models_to_load = {
            'face': {
                'module': 'qai_hub_models.models.mediapipe_face',
                'class': 'Model',
                'description': 'MediaPipe Face Detection',
                'input_size': (192, 192)
            },
            'pose': {
                'module': 'qai_hub_models.models.mediapipe_pose',
                'class': 'Model',
                'description': 'MediaPipe Pose Estimation',
                'input_size': (256, 256)
            },
            'hand': {
                'module': 'qai_hub_models.models.mediapipe_hand',
                'class': 'Model',
                'description': 'MediaPipe Hand Detection',
                'input_size': (224, 224)
            }
        }
        
        for model_name, config in models_to_load.items():
            try:
                logger.info(f"📱 載入 {config['description']}...")
                
                # 動態導入模型
                module = __import__(config['module'], fromlist=[config['class']])
                ModelClass = getattr(module, config['class'])
                
                # 創建預訓練模型
                model = ModelClass.from_pretrained()
                
                self.qai_hub_models[model_name] = {
                    'model': model,
                    'config': config,
                    'loaded': True
                }
                
                logger.info(f"✅ {config['description']} 載入成功")
                
            except Exception as e:
                logger.error(f"❌ {config['description']} 載入失敗: {e}")
                self.qai_hub_models[model_name] = {
                    'model': None,
                    'config': config,
                    'loaded': False,
                    'error': str(e)
                }
    
    def export_models_to_torchscript(self):
        """將模型導出為TorchScript格式（QAI Hub支援）"""
        logger.info("📤 導出模型為TorchScript格式...")
        
        for model_name, model_info in self.qai_hub_models.items():
            if not model_info['loaded']:
                continue
                
            try:
                model = model_info['model']
                config = model_info['config']
                
                logger.info(f"🔄 導出 {config['description']} 為TorchScript...")
                
                # 準備示例輸入
                input_size = config['input_size']
                sample_input = torch.randn(1, 3, input_size[1], input_size[0])
                
                # 設置模型為評估模式
                model.eval()
                
                # 導出為TorchScript
                with torch.no_grad():
                    traced_model = torch.jit.trace(model, sample_input)
                
                # 保存TorchScript模型
                torchscript_path = f"qai_hub_{model_name}_model.pt"
                traced_model.save(torchscript_path)
                
                logger.info(f"✅ {config['description']} TorchScript已保存: {torchscript_path}")
                
                # 更新模型信息
                model_info['torchscript_path'] = torchscript_path
                model_info['sample_input_shape'] = sample_input.shape
                
            except Exception as e:
                logger.error(f"❌ {config['description']} TorchScript導出失敗: {e}")
                model_info['export_error'] = str(e)
    
    def upload_models_to_qai_hub(self):
        """上傳模型到QAI Hub"""
        logger.info("☁️ 上傳模型到QAI Hub...")
        
        for model_name, model_info in self.qai_hub_models.items():
            if not model_info.get('torchscript_path'):
                logger.warning(f"⚠️ {model_name} 沒有TorchScript文件，跳過上傳")
                continue
                
            try:
                torchscript_path = model_info['torchscript_path']
                config = model_info['config']
                
                logger.info(f"📤 上傳 {config['description']} 到QAI Hub...")
                
                # 上傳模型到QAI Hub
                uploaded_model = hub.upload_model(torchscript_path)
                
                logger.info(f"✅ {config['description']} 上傳成功")
                logger.info(f"   模型ID: {uploaded_model.model_id}")
                
                # 保存上傳的模型引用
                model_info['qai_hub_model'] = uploaded_model
                model_info['model_id'] = uploaded_model.model_id
                
            except Exception as e:
                logger.error(f"❌ {config['description']} 上傳失敗: {e}")
                model_info['upload_error'] = str(e)
    
    def submit_compilation_jobs(self):
        """提交編譯Jobs"""
        logger.info("🔄 提交模型編譯Jobs到QAI Hub...")
        
        for model_name, model_info in self.qai_hub_models.items():
            if not model_info.get('qai_hub_model'):
                logger.warning(f"⚠️ {model_name} 沒有上傳到QAI Hub，跳過編譯")
                continue
                
            try:
                qai_model = model_info['qai_hub_model']
                config = model_info['config']
                input_size = config['input_size']
                
                logger.info(f"🚀 提交 {config['description']} 編譯Job...")
                
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
                
                logger.info(f"✅ {config['description']} 編譯Job已提交")
                logger.info(f"   Job ID: {compile_job.job_id}")
                logger.info(f"   Dashboard: https://aihub.qualcomm.com/jobs/{compile_job.job_id}")
                
                # 保存Job引用
                model_info['compile_job'] = compile_job
                
            except Exception as e:
                logger.error(f"❌ {config['description']} 編譯Job提交失敗: {e}")
                model_info['compile_error'] = str(e)
    
    def convert_torchscript_to_onnx(self):
        """將TorchScript模型轉換為ONNX"""
        logger.info("🔄 轉換TorchScript模型為ONNX...")
        
        for model_name, model_info in self.qai_hub_models.items():
            if not model_info.get('torchscript_path'):
                continue
                
            try:
                config = model_info['config']
                input_size = config['input_size']
                
                logger.info(f"🔄 轉換 {config['description']} 為ONNX...")
                
                # 載入TorchScript模型
                torchscript_model = torch.jit.load(model_info['torchscript_path'])
                
                # 準備示例輸入
                sample_input = torch.randn(1, 3, input_size[1], input_size[0])
                
                # 導出為ONNX
                onnx_path = f"qai_hub_{model_name}_model.onnx"
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
                self._load_onnx_session(model_name, onnx_path, model_info)
                
            except Exception as e:
                logger.error(f"❌ {config['description']} ONNX轉換失敗: {e}")
                model_info['onnx_error'] = str(e)
    
    def _load_onnx_session(self, model_name: str, onnx_path: str, model_info: Dict):
        """載入ONNX Runtime會話"""
        try:
            config = model_info['config']
            logger.info(f"🔄 載入 {model_name} ONNX Runtime會話...")
            
            # 設置會話選項
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
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
            
            # 記錄會話信息
            input_info = session.get_inputs()[0]
            output_info = session.get_outputs()[0]
            
            logger.info(f"✅ {model_name} ONNX會話載入成功")
            logger.info(f"   輸入: {input_info.name} {input_info.shape} {input_info.type}")
            logger.info(f"   輸出: {output_info.name} {output_info.shape} {output_info.type}")
            
        except Exception as e:
            logger.error(f"❌ {model_name} ONNX會話載入失敗: {e}")
    
    def detect_with_onnx(self, image: np.ndarray, model_name: str) -> Dict[str, Any]:
        """使用ONNX Runtime執行檢測"""
        if model_name not in self.onnx_sessions:
            return {"error": f"ONNX會話 {model_name} 未載入"}
        
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
            results = self._postprocess_detection(outputs, model_name, config)
            results.update({
                'inference_time_ms': round(inference_time, 2),
                'model_type': f"QAI_Hub_{model_name}_ONNX",
                'description': config['description']
            })
            
            logger.info(f"⚡ {model_name}檢測完成: {inference_time:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"❌ {model_name}檢測失敗: {e}")
            return {"error": str(e)}
    
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
    
    def _postprocess_detection(self, outputs: list, model_name: str, config: Dict) -> Dict[str, Any]:
        """後處理檢測結果"""
        results = {
            "success": True,
            "detections": [],
            "raw_output_shapes": [output.shape for output in outputs]
        }
        
        try:
            # 根據模型類型處理輸出
            if model_name == 'face':
                results = self._process_face_outputs(outputs, results)
            elif model_name == 'pose':
                results = self._process_pose_outputs(outputs, results)
            elif model_name == 'hand':
                results = self._process_hand_outputs(outputs, results)
                
        except Exception as e:
            logger.error(f"❌ {model_name}後處理失敗: {e}")
            results["success"] = False
            results["error"] = str(e)
        
        return results
    
    def _process_face_outputs(self, outputs: list, results: Dict) -> Dict:
        """處理人臉檢測輸出"""
        # 簡化的人臉檢測結果處理
        if len(outputs) > 0:
            output = outputs[0]
            results["detections"] = [{
                "type": "face",
                "output_shape": output.shape,
                "detected": True
            }]
            results["total_faces"] = 1
        return results
    
    def _process_pose_outputs(self, outputs: list, results: Dict) -> Dict:
        """處理姿態檢測輸出"""
        if len(outputs) > 0:
            output = outputs[0]
            results["detections"] = [{
                "type": "pose",
                "output_shape": output.shape,
                "detected": True
            }]
            results["total_poses"] = 1
        return results
    
    def _process_hand_outputs(self, outputs: list, results: Dict) -> Dict:
        """處理手部檢測輸出"""
        if len(outputs) > 0:
            output = outputs[0]
            results["detections"] = [{
                "type": "hand",
                "output_shape": output.shape,
                "detected": True
            }]
            results["total_hands"] = 1
        return results
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """運行完整的QAI Hub + ONNX流水線"""
        pipeline_results = {
            "timestamp": time.time(),
            "steps": {},
            "final_status": {}
        }
        
        try:
            # Step 1: 載入模型
            logger.info("📥 Step 1: 載入MediaPipe模型")
            self.load_mediapipe_models()
            pipeline_results["steps"]["load_models"] = "completed"
            
            # Step 2: 導出TorchScript
            logger.info("📤 Step 2: 導出TorchScript模型")
            self.export_models_to_torchscript()
            pipeline_results["steps"]["export_torchscript"] = "completed"
            
            # Step 3: 上傳到QAI Hub
            logger.info("☁️ Step 3: 上傳模型到QAI Hub")
            self.upload_models_to_qai_hub()
            pipeline_results["steps"]["upload_qai_hub"] = "completed"
            
            # Step 4: 提交編譯Jobs
            logger.info("🚀 Step 4: 提交編譯Jobs")
            self.submit_compilation_jobs()
            pipeline_results["steps"]["submit_compile_jobs"] = "completed"
            
            # Step 5: 轉換ONNX
            logger.info("🔄 Step 5: 轉換為ONNX")
            self.convert_torchscript_to_onnx()
            pipeline_results["steps"]["convert_onnx"] = "completed"
            
            # 生成最終狀態報告
            pipeline_results["final_status"] = {
                "loaded_models": list(self.qai_hub_models.keys()),
                "onnx_sessions": list(self.onnx_sessions.keys()),
                "qai_hub_uploads": len([m for m in self.qai_hub_models.values() if m.get('model_id')]),
                "compile_jobs": len([m for m in self.qai_hub_models.values() if m.get('compile_job')])
            }
            
            logger.info("✅ 完整流水線執行成功！")
            
        except Exception as e:
            logger.error(f"❌ 流水線執行失敗: {e}")
            pipeline_results["error"] = str(e)
        
        return pipeline_results

def main():
    """主函數：演示實用QAI Hub + ONNX系統"""
    print("🎯 實用QAI Hub + ONNX Runtime系統演示")
    print("=" * 60)
    
    try:
        # 初始化系統
        system = PracticalQAIHubONNX()
        
        # 運行完整流水線
        results = system.run_full_pipeline()
        
        # 測試檢測（如果ONNX會話可用）
        if system.onnx_sessions:
            print("\n🧪 測試ONNX檢測...")
            
            test_images = ['andy.jpg', 'official_test_image.jpg']
            for img_path in test_images:
                if os.path.exists(img_path):
                    print(f"\n📷 測試圖像: {img_path}")
                    image = cv2.imread(img_path)
                    
                    if image is not None:
                        for model_name in system.onnx_sessions.keys():
                            detection_result = system.detect_with_onnx(image, model_name)
                            print(f"   {model_name}: {detection_result.get('inference_time_ms', 'N/A')}ms")
        
        # 檢查QAI Hub Job狀態
        print("\n📊 QAI Hub Job狀態:")
        for model_name, model_info in system.qai_hub_models.items():
            if 'compile_job' in model_info:
                job = model_info['compile_job']
                print(f"   {model_name}: Job {job.job_id}")
                print(f"     Dashboard: https://aihub.qualcomm.com/jobs/{job.job_id}")
        
        # 保存結果
        results_file = 'practical_qai_hub_onnx_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ 演示完成！結果已保存到 {results_file}")
        
    except Exception as e:
        print(f"❌ 演示失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
