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
import onnx

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PracticalQAIHubONNX:
    def submit_profile_jobs(self):
        """自動提交所有已上傳模型的 profiling job，遇到裝置不支援自動提示/跳過/詢問轉換"""
        logger.info("🚀 提交 Profiling Jobs 到 QAI Hub...")
        # 取得裝置支援格式
        device = self.target_device
        if not device:
            logger.error("❌ 無法取得目標裝置，無法提交 profiling job")
            return
        device_attrs = getattr(device, 'attributes', [])
        support_onnx = any('framework:onnx' in a for a in device_attrs)
        support_tflite = any('framework:tflite' in a for a in device_attrs)
        support_dlc = any('framework:dlc' in a for a in device_attrs)
        logger.info(f"🔍 目標裝置支援: ONNX={support_onnx}, TFLite={support_tflite}, DLC={support_dlc}")
        for model_name, model_info in self.qai_hub_models.items():
            qai_model = model_info.get('qai_hub_model')
            if not qai_model:
                logger.warning(f"⚠️ {model_name} 尚未上傳 QAI Hub，跳過 profiling job 提交")
                continue
            model_path = model_info.get('model_path','')
            ext = os.path.splitext(model_path)[-1].lower()
            try:
                config = model_info['config']
                # 判斷格式支援
                if ext == '.onnx' and not support_onnx:
                    logger.warning(f"⚠️ 目標裝置不支援 ONNX，{model_name} 跳過 profiling job 提交")
                    continue
                if ext == '.tflite' and not support_tflite:
                    # 詢問是否要自動轉換 onnx
                    print(f"⚠️ 目標裝置不支援 TFLite，模型 {model_name} 無法直接 profile。是否要自動轉換為 ONNX？(y/n)")
                    user_input = input().strip().lower()
                    if user_input == 'y':
                        # 嘗試自動轉換 tflite->onnx
                        try:
                            import subprocess
                            onnx_path = os.path.splitext(model_path)[0] + '.onnx'
                            print(f"🔄 自動轉換 {model_path} → {onnx_path} ...")
                            result = subprocess.run(['tflite2onnx', model_path, onnx_path], capture_output=True, text=True)
                            if result.returncode == 0 and os.path.exists(onnx_path):
                                print(f"✅ 轉換成功: {onnx_path}")
                                # 重新上傳 onnx
                                uploaded_model = hub.upload_model(onnx_path)
                                model_info['qai_hub_model'] = uploaded_model
                                model_info['model_path'] = onnx_path
                                model_info['format'] = 'onnx'
                                qai_model = uploaded_model
                                ext = '.onnx'
                            else:
                                print(f"❌ 轉換失敗: {result.stderr}")
                                continue
                        except Exception as te:
                            print(f"❌ tflite 轉 onnx 發生錯誤: {te}")
                            continue
                    else:
                        print(f"⏭️ 跳過 {model_name}")
                        continue
                if ext == '.dlc' and not support_dlc:
                    logger.warning(f"⚠️ 目標裝置不支援 DLC，{model_name} 跳過 profiling job 提交")
                    continue
                logger.info(f"📈 提交 {config['description']} profiling job...")
                profile_job = hub.submit_profile_job(
                    model=qai_model,
                    device=self.target_device
                )
                logger.info(f"✅ {config['description']} Profiling Job已提交: {profile_job.job_id}")
                logger.info(f"   Dashboard: https://aihub.qualcomm.com/jobs/{profile_job.job_id}")
                model_info['profile_job'] = profile_job
            except Exception as e:
                logger.error(f"❌ {config['description']} Profiling Job提交失敗: {e}")
                model_info['profile_error'] = str(e)
    def __init__(self, target_device_name: str = "Snapdragon X Elite CRD"):
        self.qai_hub_models = {}
        self.onnx_sessions = {}
        self.target_device = None
        self.target_device_name = target_device_name
        # 預設 ONNX providers：安全取得可用 providers，否則回退到 CPU
        try:
            available = ort.get_available_providers()
            if available:
                self.onnx_providers = available
            else:
                self.onnx_providers = ['CPUExecutionProvider']
        except Exception:
            self.onnx_providers = ['CPUExecutionProvider']
        # 依名稱自動選擇目標設備
        try:
            devices = hub.get_devices()
            if not devices:
                logger.warning("❌ 無可用QAI Hub設備，請確認帳號或API Key")
                self.target_device = None
            else:
                # 先精確比對名稱
                matched = [d for d in devices if d.name == self.target_device_name]
                if matched:
                    self.target_device = matched[0]
                else:
                    # 再用關鍵字模糊比對
                    target_devices = [d for d in devices if any(kw in d.name for kw in ["Snapdragon", "X Elite", "CPU"])]
                    self.target_device = target_devices[0] if target_devices else devices[0]
                logger.info(f"🎯 目標設備: {self.target_device.name}")
        except Exception as e:
            logger.error(f"❌ 取得QAI Hub設備失敗: {e}")
            self.target_device = None
    """實用的QAI Hub + ONNX Runtime系統"""
    
    def load_mediapipe_models(self, source: str = 'onnx', model_dir: str = None, ext: str = None):
        """
        自動載入指定目錄下所有副檔名正確的模型（onnx/tflite/dlc），不再只依 key 對應。
        source: 標記來源類型
        model_dir: 指定目錄（如 org-onnx、org-tflite、org-dlc...）
        ext: 指定副檔名（.onnx/.tflite/.dlc）
        """
        logger.info(f"📥 載入MediaPipe模型來源: {source}")
        base_dir = Path(__file__).parent.parent / 'models'
        if model_dir is not None and ext is not None:
            model_dir = base_dir / model_dir
        else:
            if source == 'onnx':
                model_dir = base_dir / 'onnx'
                ext = '.onnx'
            elif source == 'original':
                model_dir = base_dir / 'original'
                ext = '.tflite'
            else:
                raise ValueError(f"未知模型來源: {source}")

        if not model_dir.exists() or not model_dir.is_dir():
            logger.warning(f"❌ 模型目錄不存在: {model_dir}")
            return

        found_models = list(model_dir.glob(f"*{ext}"))
        if not found_models:
            logger.warning(f"❌ 目錄 {model_dir} 下找不到任何 {ext} 模型檔案")
        # 常見 MediaPipe 模型 input_size 對應表
        input_size_map = {
            'facedetector': (192, 192),
            'facelandmark': (192, 192),
            'facelandmarkdetector': (192, 192),
            'facelandmark_with_attention': (192, 192),
            'handdetector': (224, 224),
            'handlandmark': (224, 224),
            'handlandmarkdetector': (224, 224),
            'handrecrop': (224, 224),
            'irislandmark': (64, 64),
            'posedetector': (256, 256),
            'poselandmark': (256, 256),
            'poselandmarkdetector': (256, 256),
            'poselandmark_full': (256, 256),
            'poselandmark_heavy': (256, 256),
            'poselandmark_lite': (256, 256),
        }
        default_input_size = (224, 224)
        for model_path in found_models:
            model_name = model_path.stem
            # If the found path is a directory (some models are unpacked into folders
            # named with a .onnx suffix), try to resolve an actual .onnx file inside.
            if model_path.is_dir():
                candidate = model_path / 'model.onnx'
                if candidate.exists():
                    model_path = candidate
                else:
                    inner = list(model_path.glob('*.onnx'))
                    if inner:
                        model_path = inner[0]
                    else:
                        # leave as-is; later loading will warn/error
                        logger.warning(f"⚠️ {model_path} appears to be a directory but contains no .onnx files")
            # 嘗試自動對應 input_size
            key = model_name.lower().replace('mediapipe-', '').replace('_w8a8', '').replace('_with_attention', '').replace('_full', '').replace('_heavy', '').replace('_lite', '').replace('_detector', '').replace('_landmark', 'landmark')
            # 例如 MediaPipe-FaceDetector -> facedetector
            input_size = None
            for k, v in input_size_map.items():
                if k in key:
                    input_size = v
                    break
            if input_size is None:
                input_size = default_input_size
                logger.warning(f"⚠️ {model_name} 未知input_size，自動設為 {default_input_size}")
            self.qai_hub_models[model_name] = {
                'model_path': str(model_path),
                'config': {'description': model_name, 'input_size': input_size},
                'loaded': True,
                'format': source
            }
            logger.info(f"✅ {model_name} 載入成功: {model_path} | input_size={input_size}")
        logger.info("✅ CPU執行提供商已添加")
    
    
    def export_models_to_torchscript(self):
        """將模型導出為TorchScript格式（QAI Hub支援）"""
        logger.info("📤 導出模型為TorchScript格式...")
        
        for model_name, model_info in self.qai_hub_models.items():
            if not model_info.get('loaded'):
                continue
            if 'model' not in model_info:
                logger.info(f"⚠️ {model_name} 無 PyTorch model，跳過 TorchScript 導出。")
                continue
            try:
                model = model_info['model']
                config = model_info.get('config', {'description': model_name})
                logger.info(f"🔄 導出 {config['description']} 為TorchScript...")
                input_size = config['input_size']
                sample_input = torch.randn(1, 3, input_size[1], input_size[0])
                model.eval()
                with torch.no_grad():
                    traced_model = torch.jit.trace(model, sample_input)
                torchscript_path = f"qai_hub_{model_name}_model.pt"
                traced_model.save(torchscript_path)
                logger.info(f"✅ {config['description']} TorchScript已保存: {torchscript_path}")
                model_info['torchscript_path'] = torchscript_path
                model_info['sample_input_shape'] = sample_input.shape
            except Exception as e:
                logger.error(f"❌ {config['description']} TorchScript導出失敗: {e}")
                model_info['export_error'] = str(e)
    
    def upload_models_to_qai_hub(self):
        """上傳模型到QAI Hub (支援 onnx/tflite/torchscript)"""
        logger.info("☁️ 上傳模型到QAI Hub...")
        for model_name, model_info in self.qai_hub_models.items():
            # 優先順序：torchscript > onnx/tflite
            model_path = model_info.get('torchscript_path') or model_info.get('model_path')
            if not model_info.get('loaded') or not model_path or not os.path.exists(model_path):
                logger.warning(f"⚠️ {model_name} 沒有可用模型檔案，跳過上傳")
                continue
            try:
                config = model_info['config']
                logger.info(f"📤 上傳 {config['description']} ({model_path}) 到QAI Hub...")
                uploaded_model = hub.upload_model(model_path)
                logger.info(f"✅ {config['description']} 上傳成功")
                logger.info(f"   模型ID: {uploaded_model.model_id}")
                model_info['qai_hub_model'] = uploaded_model
                model_info['model_id'] = uploaded_model.model_id
            except Exception as e:
                logger.error(f"❌ {config['description']} 上傳失敗: {e}")
                model_info['upload_error'] = str(e)
    
    def submit_compilation_jobs(self):
        """提交編譯Jobs (只要有成功上傳的模型都能提交)"""
        import onnx
        logger.info("🔄 提交模型編譯Jobs到QAI Hub...")
        for model_name, model_info in self.qai_hub_models.items():
            if not model_info.get('qai_hub_model'):
                logger.warning(f"⚠️ {model_name} 沒有上傳到QAI Hub，跳過編譯")
                continue
            try:
                qai_model = model_info['qai_hub_model']
                config = model_info['config']
                logger.info(f"🚀 提交 {config['description']} 編譯Job...")
                # 自動讀取 onnx input shape
                model_path = model_info.get('model_path')
                input_specs = None
                if model_path and model_path.endswith('.onnx'):
                    try:
                        onnx_model = onnx.load(model_path)
                        input_tensor = onnx_model.graph.input[0]
                        input_name = input_tensor.name
                        shape = [d.dim_value for d in input_tensor.type.tensor_type.shape.dim]
                        dtype = onnx.mapping.TENSOR_TYPE_TO_NP_TYPE[input_tensor.type.tensor_type.elem_type]
                        input_specs = {input_name: (tuple(shape), str(dtype))}
                        logger.info(f"   [Auto] input_specs: {input_specs}")
                    except Exception as e:
                        logger.warning(f"   [Auto] 讀取 onnx input shape 失敗: {e}")
                if input_specs is None:
                    # fallback 舊邏輯
                    input_size = config.get('input_size', (224, 224))
                    input_specs = {'input': (1, 3, input_size[1], input_size[0])}
                    logger.info(f"   [Fallback] input_specs: {input_specs}")
                compile_job = hub.submit_compile_job(
                    model=qai_model,
                    input_specs=input_specs,
                    device=self.target_device
                )
                logger.info(f"✅ {config['description']} 編譯Job已提交")
                logger.info(f"   Job ID: {compile_job.job_id}")
                logger.info(f"   Dashboard: https://aihub.qualcomm.com/jobs/{compile_job.job_id}")
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
            # 使用 job_monitor 的統一計數來避免不同來源的狀態不一致
            try:
                from .modules.job_monitor import get_job_monitor
                jm = get_job_monitor()
                compile_jobs_count = len(jm.get_jobs_by_type('compile'))
            except Exception:
                # 回退到原先的計算方法
                compile_jobs_count = len([m for m in self.qai_hub_models.values() if m.get('compile_job')])

            pipeline_results["final_status"] = {
                "loaded_models": list(self.qai_hub_models.keys()),
                "onnx_sessions": list(self.onnx_sessions.keys()),
                "qai_hub_uploads": len([m for m in self.qai_hub_models.values() if m.get('model_id')]),
                "compile_jobs": compile_jobs_count
            }
            
            logger.info("✅ 完整流水線執行成功！")
            
        except Exception as e:
            logger.error(f"❌ 流水線執行失敗: {e}")
            pipeline_results["error"] = str(e)
        
        return pipeline_results

    def check_onnx_models(self):
        """檢查所有 onnx 檔案是否合法，回傳異常清單"""
        invalid = []
        for model_name, model_info in self.qai_hub_models.items():
            if model_info.get('format') == 'onnx' and model_info.get('loaded'):
                path = model_info['model_path']
                try:
                    onnx.checker.check_model(path, full_check=True)
                except Exception as e:
                    invalid.append((model_name, path, str(e)))
        return invalid

def main():
    """主函數：演示實用QAI Hub + ONNX系統"""
    print("🎯 實用QAI Hub + ONNX Runtime系統演示")
    print("=" * 60)
    
    try:
        # 初始化系統
        system = PracticalQAIHubONNX()
        
        # 運行完整流水線
        results = system.run_full_pipeline()
        
        # 顯示將進行 QAI Hub 最佳化的模型數量與清單
        models_to_optimize = [k for k, v in system.qai_hub_models.items() if v.get('loaded')]
        print(f"\n🔎 偵測到 {len(models_to_optimize)} 個模型將進行 QAI Hub 最佳化：")
        for m in models_to_optimize:
            print(f"   - {m}")

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
        
        # 自動查詢 QAI Hub Job 狀態，等待所有 Job 完成
        import time
        print("\n⏳ 等待所有 QAI Hub Job 完成...")
        all_done = False
        poll_interval = 10  # 秒
        max_wait = 60 * 30  # 最長等待 30 分鐘
        waited = 0
        
        # 定義所有完成的狀態
        completed_status = ('COMPLETED', 'SUCCEEDED', 'SUCCESS', 'FINISHED', 
                          'COMPLETED_SUCCESSFULLY', 'RESULTS_READY', 'RESULTS READY', 
                          'results_ready', 'Results Ready')
        
        while not all_done and waited < max_wait:
            all_done = True
            for model_name, model_info in system.qai_hub_models.items():
                job = model_info.get('compile_job')
                if job:
                    job.refresh()  # 重新查詢狀態
                    status = getattr(job, 'status', None) or getattr(job, 'state', None)
                    model_info['job_status'] = status
                    # 檢查狀態是否在完成狀態列表中（不區分大小寫）
                    if status is None or str(status).upper() not in [s.upper() for s in completed_status]:
                        all_done = False
            if not all_done:
                print(f"  ...尚有 Job 執行中，{poll_interval} 秒後再查詢...")
                time.sleep(poll_interval)
                waited += poll_interval
        print("\n📊 QAI Hub Job狀態:")
        for model_name, model_info in system.qai_hub_models.items():
            job = model_info.get('compile_job')
            job_id = job.job_id if job else ''
            status = model_info.get('job_status', '')
            print(f"   {model_name}: Job {job_id} 狀態: {status}")
            if job_id:
                print(f"     Dashboard: https://aihub.qualcomm.com/jobs/{job_id}")

        # 保存結果 (JSON)
        results_file = 'practical_qai_hub_onnx_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        # 產生 HTML 報告
        html_file = 'practical_qai_hub_onnx_report.html'
        with open(html_file, 'w') as f:
            f.write('<html><head><meta charset="utf-8"><title>QAI Hub Pipeline Report</title></head><body>')
            f.write('<h1>QAI Hub Pipeline Report</h1>')
            f.write(f'<p><b>Timestamp:</b> {results.get("timestamp", "")}</p>')
            f.write('<h2>Models & Jobs</h2><table border="1" cellpadding="4"><tr><th>Model</th><th>Status</th><th>Job ID</th><th>Dashboard</th></tr>')
            for model_name, model_info in system.qai_hub_models.items():
                job = model_info.get('compile_job')
                job_id = job.job_id if job else ''
                dashboard = f'<a href="https://aihub.qualcomm.com/jobs/{job_id}">{job_id}</a>' if job_id else ''
                status = model_info.get('job_status', '') or ('已提交' if job_id else (model_info.get('error') or '未提交'))
                f.write(f'<tr><td>{model_name}</td><td>{status}</td><td>{job_id}</td><td>{dashboard}</td></tr>')
            f.write('</table>')
            # pipeline summary
            f.write('<h2>Pipeline Summary</h2><ul>')
            for step, stat in results.get('steps', {}).items():
                f.write(f'<li>{step}: {stat}</li>')
            f.write('</ul>')
            if 'error' in results:
                f.write(f'<p style="color:red"><b>Pipeline Error:</b> {results["error"]}</p>')
            f.write('</body></html>')

        print(f"\n✅ 演示完成！結果已保存到 {results_file}，HTML 報告已產生 {html_file}")
        
    except Exception as e:
        print(f"❌ 演示失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
