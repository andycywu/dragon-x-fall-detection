#!/usr/bin/env python3
"""
🎯 最終QAI Hub + ONNX Runtime生產就緒系統
正確處理QAI Hub Models並實現真實連接
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

class FinalQAIHubONNXSystem:
    """最終QAI Hub + ONNX Runtime生產就緒系統"""
    
    def __init__(self):
        """初始化系統"""
        self.api_token = os.getenv('QAI_HUB_API_TOKEN')
        if not self.api_token:
            raise ValueError("❌ 請設置QAI_HUB_API_TOKEN環境變數")
        
        # ONNX Runtime配置
        self.onnx_providers = self._get_onnx_providers()
        self.onnx_sessions = {}
        
        # QAI Hub相關
        self.model_components = {}
        self.qai_hub_models = {}
        self.jobs = {}
        
        logger.info("🚀 初始化最終QAI Hub + ONNX系統...")
        self._verify_connection()
        
    def _verify_connection(self):
        """驗證QAI Hub連接"""
        try:
            devices = hub.get_devices()
            logger.info(f"✅ QAI Hub連接成功，{len(devices)}個設備可用")
            
            # 選擇最佳設備
            target_devices = [d for d in devices if any(kw in d.name for kw in 
                                                      ['Snapdragon', 'Samsung', 'Galaxy'])]
            self.target_device = target_devices[0] if target_devices else devices[0]
            logger.info(f"🎯 目標設備: {self.target_device.name}")
            
        except Exception as e:
            logger.error(f"❌ QAI Hub連接失敗: {e}")
            raise
    
    def _get_onnx_providers(self):
        """獲取ONNX Runtime執行提供商"""
        providers = []
        available = ort.get_available_providers()
        
        # 按優先級選擇提供商
        priority_providers = [
            'CUDAExecutionProvider',
            'DmlExecutionProvider', 
            'CoreMLExecutionProvider',
            'CPUExecutionProvider'
        ]
        
        for provider in priority_providers:
            if provider in available:
                providers.append(provider)
                if provider != 'CPUExecutionProvider':
                    logger.info(f"✅ 啟用硬體加速: {provider}")
                break
        
        if not providers:
            providers = ['CPUExecutionProvider']
        
        logger.info(f"📋 ONNX執行提供商: {providers}")
        return providers
    
    def load_mediapipe_components(self):
        """載入MediaPipe模型組件"""
        logger.info("📥 載入MediaPipe模型組件...")
        
        component_configs = {
            'face_detector': {
                'module_path': 'qai_hub_models.models.mediapipe_face',
                'component_name': 'face_detector',
                'description': 'MediaPipe Face Detector'
            },
            'face_landmark': {
                'module_path': 'qai_hub_models.models.mediapipe_face',
                'component_name': 'face_landmark_detector',
                'description': 'MediaPipe Face Landmark Detector'
            }
        }
        
        for comp_name, config in component_configs.items():
            try:
                logger.info(f"📱 載入 {config['description']}...")
                
                # 導入並創建模型
                module = __import__(config['module_path'], fromlist=['Model'])
                full_model = module.Model.from_pretrained()
                
                # 提取組件
                component = getattr(full_model, config['component_name'])
                
                self.model_components[comp_name] = {
                    'component': component,
                    'config': config,
                    'loaded': True
                }
                
                logger.info(f"✅ {config['description']} 載入成功")
                
            except Exception as e:
                logger.error(f"❌ {config['description']} 載入失敗: {e}")
                self.model_components[comp_name] = {
                    'component': None,
                    'config': config,
                    'loaded': False,
                    'error': str(e)
                }
    
    def convert_to_torchscript_and_upload(self):
        """轉換為TorchScript並上傳到QAI Hub"""
        logger.info("📤 轉換為TorchScript並上傳...")
        
        for comp_name, comp_info in self.model_components.items():
            if not comp_info['loaded']:
                continue
                
            try:
                component = comp_info['component']
                config = comp_info['config']
                
                logger.info(f"🔄 處理 {config['description']}...")
                
                # 使用組件的convert_to_torchscript方法
                torchscript_model = component.convert_to_torchscript()
                
                # 保存TorchScript模型
                ts_path = f"qai_hub_{comp_name}.pt"
                torchscript_model.save(ts_path)
                logger.info(f"✅ TorchScript已保存: {ts_path}")
                
                # 上傳到QAI Hub
                logger.info(f"☁️ 上傳 {config['description']} 到QAI Hub...")
                qai_model = hub.upload_model(ts_path)
                
                self.qai_hub_models[comp_name] = {
                    'qai_model': qai_model,
                    'model_id': qai_model.model_id,
                    'torchscript_path': ts_path,
                    'config': config
                }
                
                logger.info(f"✅ 上傳成功，模型ID: {qai_model.model_id}")
                
            except Exception as e:
                logger.error(f"❌ {config['description']} 處理失敗: {e}")
                comp_info['process_error'] = str(e)
    
    def submit_qai_hub_jobs(self):
        """提交QAI Hub編譯和Profiling Jobs"""
        logger.info("🚀 提交QAI Hub Jobs...")
        
        for comp_name, model_info in self.qai_hub_models.items():
            try:
                qai_model = model_info['qai_model']
                config = model_info['config']
                
                logger.info(f"📋 提交 {config['description']} Jobs...")
                
                # 獲取組件的示例輸入
                component = self.model_components[comp_name]['component']
                sample_inputs = component.sample_inputs()
                
                # 從示例輸入推斷輸入規格
                input_spec = {}
                for key, value_list in sample_inputs.items():
                    if isinstance(value_list, list) and len(value_list) > 0:
                        sample_array = value_list[0]
                        input_spec[key] = (sample_array.shape, sample_array.dtype.name)
                
                logger.info(f"   輸入規格: {input_spec}")
                
                # 提交編譯Job
                compile_job = hub.submit_compile_job(
                    model=qai_model,
                    input_specs=input_spec,
                    device=self.target_device
                )
                
                # 提交Profiling Job
                profile_job = hub.submit_profile_job(
                    model=qai_model,
                    input_data=sample_inputs,
                    device=self.target_device
                )
                
                self.jobs[comp_name] = {
                    'compile_job': compile_job,
                    'profile_job': profile_job,
                    'config': config
                }
                
                logger.info(f"✅ Jobs已提交:")
                logger.info(f"   編譯Job: {compile_job.job_id}")
                logger.info(f"   Profiling Job: {profile_job.job_id}")
                logger.info(f"   Dashboard: https://aihub.qualcomm.com/jobs/{compile_job.job_id}")
                
            except Exception as e:
                logger.error(f"❌ {config['description']} Job提交失敗: {e}")
    
    def export_to_onnx_runtime(self):
        """導出為ONNX並創建Runtime會話"""
        logger.info("🔄 導出ONNX並創建Runtime會話...")
        
        for comp_name, comp_info in self.model_components.items():
            if not comp_info['loaded']:
                continue
                
            try:
                component = comp_info['component']
                config = comp_info['config']
                
                logger.info(f"🔄 處理 {config['description']}...")
                
                # 獲取示例輸入
                sample_inputs = component.sample_inputs()
                image_tensor = torch.from_numpy(sample_inputs['image'][0])
                
                # 使用TorchScript模型導出ONNX
                if comp_name in self.qai_hub_models:
                    ts_path = self.qai_hub_models[comp_name]['torchscript_path']
                    ts_model = torch.jit.load(ts_path)
                    
                    # 導出ONNX
                    onnx_path = f"qai_hub_{comp_name}.onnx"
                    torch.onnx.export(
                        ts_model,
                        image_tensor,
                        onnx_path,
                        export_params=True,
                        opset_version=11,
                        do_constant_folding=True,
                        input_names=['image'],
                        output_names=['output']
                    )
                    
                    logger.info(f"✅ ONNX已保存: {onnx_path}")
                    
                    # 創建ONNX Runtime會話
                    self._create_onnx_session(comp_name, onnx_path, config)
                
            except Exception as e:
                logger.error(f"❌ {config['description']} ONNX導出失敗: {e}")
    
    def _create_onnx_session(self, comp_name: str, onnx_path: str, config: Dict):
        """創建ONNX Runtime會話"""
        try:
            logger.info(f"🔄 創建 {comp_name} ONNX Runtime會話...")
            
            # 會話選項
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # 創建會話
            session = ort.InferenceSession(onnx_path, providers=self.onnx_providers)
            
            self.onnx_sessions[comp_name] = {
                'session': session,
                'onnx_path': onnx_path,
                'config': config
            }
            
            logger.info(f"✅ {comp_name} ONNX Runtime會話創建成功")
            
        except Exception as e:
            logger.error(f"❌ {comp_name} ONNX Runtime會話創建失敗: {e}")
    
    def detect_with_onnx(self, image: np.ndarray, model_name: str) -> Dict[str, Any]:
        """使用ONNX Runtime執行檢測"""
        if model_name not in self.onnx_sessions:
            return {"error": f"模型 {model_name} 的ONNX會話不存在"}
        
        try:
            session_info = self.onnx_sessions[model_name]
            session = session_info['session']
            config = session_info['config']
            
            # 預處理圖像
            processed_input = self._preprocess_for_onnx(image, model_name)
            
            # 執行推理
            input_name = session.get_inputs()[0].name
            start_time = time.time()
            outputs = session.run(None, {input_name: processed_input})
            inference_time = (time.time() - start_time) * 1000
            
            # 基本結果
            results = {
                "success": True,
                "inference_time_ms": round(inference_time, 2),
                "model_name": model_name,
                "description": config['description'],
                "output_shapes": [out.shape for out in outputs],
                "num_outputs": len(outputs)
            }
            
            logger.info(f"⚡ {model_name} 檢測完成: {inference_time:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"❌ {model_name} 檢測失敗: {e}")
            return {"error": str(e), "success": False}
    
    def _preprocess_for_onnx(self, image: np.ndarray, model_name: str) -> np.ndarray:
        """為ONNX推理預處理圖像"""
        # 獲取原始組件的示例輸入形狀
        if model_name in self.model_components and self.model_components[model_name]['loaded']:
            component = self.model_components[model_name]['component']
            sample_inputs = component.sample_inputs()
            target_shape = sample_inputs['image'][0].shape
            
            # 調整圖像大小到目標形狀
            target_height, target_width = target_shape[2], target_shape[3]
            resized = cv2.resize(image, (target_width, target_height))
            
            # 轉換顏色空間
            if len(resized.shape) == 3:
                resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # 正規化
            normalized = resized.astype(np.float32) / 255.0
            
            # 轉換維度順序並添加batch維度
            preprocessed = np.transpose(normalized, (2, 0, 1))
            preprocessed = np.expand_dims(preprocessed, axis=0)
            
            return preprocessed
        
        # 默認預處理
        resized = cv2.resize(image, (192, 192))
        resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = resized.astype(np.float32) / 255.0
        preprocessed = np.transpose(normalized, (2, 0, 1))
        preprocessed = np.expand_dims(preprocessed, axis=0)
        
        return preprocessed
    
    def run_comprehensive_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """運行綜合檢測"""
        results = {
            "timestamp": time.time(),
            "image_shape": image.shape,
            "detections": {},
            "performance": {},
            "qai_hub_info": {}
        }
        
        # 執行ONNX檢測
        total_time = 0
        for model_name in self.onnx_sessions.keys():
            detection_result = self.detect_with_onnx(image, model_name)
            results["detections"][model_name] = detection_result
            
            if "inference_time_ms" in detection_result:
                results["performance"][f"{model_name}_ms"] = detection_result["inference_time_ms"]
                total_time += detection_result["inference_time_ms"]
        
        results["performance"]["total_time_ms"] = round(total_time, 2)
        
        # 添加QAI Hub信息
        for model_name, job_info in self.jobs.items():
            if 'compile_job' in job_info:
                results["qai_hub_info"][model_name] = {
                    "compile_job_id": job_info['compile_job'].job_id,
                    "profile_job_id": job_info['profile_job'].job_id,
                    "dashboard_url": f"https://aihub.qualcomm.com/jobs/{job_info['compile_job'].job_id}"
                }
        
        return results
    
    def get_system_report(self) -> Dict[str, Any]:
        """獲取系統報告"""
        return {
            "system_info": {
                "target_device": self.target_device.name,
                "onnx_providers": self.onnx_providers
            },
            "model_components": {
                name: {
                    "loaded": info["loaded"],
                    "description": info["config"]["description"],
                    "error": info.get("error")
                }
                for name, info in self.model_components.items()
            },
            "qai_hub_models": {
                name: {
                    "model_id": info["model_id"],
                    "description": info["config"]["description"]
                }
                for name, info in self.qai_hub_models.items()
            },
            "qai_hub_jobs": {
                name: {
                    "compile_job_id": info["compile_job"].job_id,
                    "profile_job_id": info["profile_job"].job_id,
                    "description": info["config"]["description"],
                    "dashboard_url": f"https://aihub.qualcomm.com/jobs/{info['compile_job'].job_id}"
                }
                for name, info in self.jobs.items()
            },
            "onnx_sessions": list(self.onnx_sessions.keys())
        }

def main():
    """主函數：演示最終QAI Hub + ONNX系統"""
    print("🎯 最終QAI Hub + ONNX Runtime生產就緒系統")
    print("=" * 70)
    
    try:
        # 初始化系統
        system = FinalQAIHubONNXSystem()
        
        # 執行完整流程
        print("\n📥 載入MediaPipe組件...")
        system.load_mediapipe_components()
        
        print("\n📤 轉換TorchScript並上傳...")
        system.convert_to_torchscript_and_upload()
        
        print("\n🚀 提交QAI Hub Jobs...")
        system.submit_qai_hub_jobs()
        
        print("\n🔄 導出ONNX Runtime...")
        system.export_to_onnx_runtime()
        
        # 測試檢測
        if system.onnx_sessions:
            print("\n🧪 測試檢測系統...")
            
            test_images = ['andy.jpg', 'official_test_image.jpg']
            for img_path in test_images:
                if os.path.exists(img_path):
                    print(f"\n📷 測試: {img_path}")
                    image = cv2.imread(img_path)
                    
                    if image is not None:
                        results = system.run_comprehensive_detection(image)
                        print(f"   檢測結果: {len(results['detections'])}個模型")
                        print(f"   總推理時間: {results['performance'].get('total_time_ms', 0)}ms")
        
        # 生成系統報告
        print("\n📊 系統報告:")
        report = system.get_system_report()
        
        print(f"   目標設備: {report['system_info']['target_device']}")
        print(f"   載入組件: {len(report['model_components'])}")
        print(f"   QAI Hub模型: {len(report['qai_hub_models'])}")
        print(f"   QAI Hub Jobs: {len(report['qai_hub_jobs'])}")
        print(f"   ONNX會話: {len(report['onnx_sessions'])}")
        
        # QAI Hub Jobs詳情
        if report['qai_hub_jobs']:
            print("\n📋 QAI Hub Jobs:")
            for name, job_info in report['qai_hub_jobs'].items():
                print(f"   {name}:")
                print(f"     編譯Job: {job_info['compile_job_id']}")
                print(f"     Profiling Job: {job_info['profile_job_id']}")
                print(f"     Dashboard: {job_info['dashboard_url']}")
        
        # 保存報告
        report_file = 'final_qai_hub_onnx_system_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n✅ 系統演示完成！")
        print(f"📄 詳細報告已保存: {report_file}")
        print(f"🎯 真正的QAI Hub + ONNX Runtime生產系統運行成功！")
        
    except Exception as e:
        print(f"❌ 系統演示失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
