#!/usr/bin/env python3
"""
🔧 修復形狀推理錯誤的QAI Hub測試
解決動態batch size (-1)導致的ONNX編譯問題
"""

import os
import qai_hub as hub
import numpy as np
import torch
import logging
from dotenv import load_dotenv
import time
import json

# 載入環境變數
load_dotenv()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedShapeQAIHubTest:
    """修復形狀問題的QAI Hub測試"""
    
    def __init__(self):
        """初始化測試系統"""
        self.api_token = os.getenv('QAI_HUB_API_TOKEN')
        self.target_device = None
        self.model_uploads = {}
        self.compile_jobs = {}
        
        logger.info("🔧 初始化形狀修復測試...")
        self._verify_connection()
    
    def _verify_connection(self):
        """驗證QAI Hub連接"""
        if not self.api_token:
            raise ValueError("❌ 請在.env文件中設置QAI_HUB_API_TOKEN")
        
        try:
            devices = hub.get_devices()
            logger.info(f"✅ QAI Hub連接成功，可用設備: {len(devices)}")
            
            # 選擇Samsung設備
            samsung_devices = [d for d in devices if 'Samsung' in d.name]
            if samsung_devices:
                self.target_device = samsung_devices[0]
                logger.info(f"🎯 選擇Samsung設備: {self.target_device.name}")
            else:
                self.target_device = devices[0] if devices else None
                logger.info(f"🎯 使用設備: {self.target_device.name if self.target_device else 'None'}")
                
        except Exception as e:
            logger.error(f"❌ QAI Hub連接失敗: {e}")
            raise
    
    def create_fixed_shape_model(self, model_type: str):
        """創建固定形狀的PyTorch模型"""
        logger.info(f"🔨 創建固定形狀{model_type}模型...")
        
        try:
            if model_type == 'face':
                from qai_hub_models.models.mediapipe_face import Model as FaceModel
                original_model = FaceModel.from_pretrained()
                
                # 獲取face_detector組件
                detector = original_model.face_detector
                
                # 使用固定輸入形狀轉換為TorchScript
                fixed_input = torch.randn(1, 3, 256, 256)
                torchscript_model = torch.jit.trace(detector, fixed_input)
                
                # 確保模型處於評估模式
                torchscript_model.eval()
                
                logger.info(f"✅ {model_type}模型TorchScript轉換完成")
                return torchscript_model, (1, 3, 256, 256)
                
            elif model_type == 'pose':
                from qai_hub_models.models.mediapipe_pose import Model as PoseModel
                original_model = PoseModel.from_pretrained()
                
                # 獲取pose_detector組件
                detector = original_model.pose_detector
                
                fixed_input = torch.randn(1, 3, 256, 256)
                torchscript_model = torch.jit.trace(detector, fixed_input)
                torchscript_model.eval()
                
                logger.info(f"✅ {model_type}模型TorchScript轉換完成")
                return torchscript_model, (1, 3, 256, 256)
                
            elif model_type == 'hand':
                from qai_hub_models.models.mediapipe_hand import Model as HandModel
                original_model = HandModel.from_pretrained()
                
                # 獲取hand_detector組件
                detector = original_model.hand_detector
                
                fixed_input = torch.randn(1, 3, 224, 224)
                torchscript_model = torch.jit.trace(detector, fixed_input)
                torchscript_model.eval()
                
                logger.info(f"✅ {model_type}模型TorchScript轉換完成")
                return torchscript_model, (1, 3, 224, 224)
                
        except Exception as e:
            logger.error(f"❌ {model_type}模型創建失敗: {e}")
            return None, None
    
    def upload_and_compile_model(self, model_type: str):
        """上傳並編譯模型"""
        logger.info(f"📤 處理{model_type}模型...")
        
        try:
            # 創建固定形狀模型
            torchscript_model, input_shape = self.create_fixed_shape_model(model_type)
            
            if torchscript_model is None:
                logger.error(f"❌ {model_type}模型創建失敗")
                return None
            
            # 上傳模型到QAI Hub
            logger.info(f"📤 上傳{model_type}模型到QAI Hub...")
            uploaded_model = hub.upload_model(torchscript_model)
            
            logger.info(f"✅ {model_type}模型上傳成功: {uploaded_model.model_id}")
            self.model_uploads[model_type] = {
                "model_id": uploaded_model.model_id,
                "input_shape": input_shape,
                "upload_time": time.time()
            }
            
            # 提交編譯Job
            if self.target_device:
                logger.info(f"🔄 提交{model_type}編譯Job...")
                
                # 準確的輸入規格
                input_specs = {"image": (input_shape, "float32")}
                
                compile_job = hub.submit_compile_job(
                    model=uploaded_model,
                    input_specs=input_specs,
                    device=self.target_device,
                )
                
                logger.info(f"✅ {model_type}編譯Job提交: {compile_job.job_id}")
                logger.info(f"🔗 Dashboard: https://app.aihub.qualcomm.com/jobs/{compile_job.job_id}")
                
                self.compile_jobs[model_type] = {
                    "job_id": compile_job.job_id,
                    "job_object": compile_job,
                    "dashboard_url": f"https://app.aihub.qualcomm.com/jobs/{compile_job.job_id}",
                    "submit_time": time.time()
                }
                
                return compile_job.job_id
            
        except Exception as e:
            logger.error(f"❌ {model_type}處理失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def check_job_status(self, model_type: str):
        """檢查編譯Job狀態"""
        if model_type not in self.compile_jobs:
            logger.warning(f"⚠️ {model_type}編譯Job不存在")
            return None
        
        try:
            job_info = self.compile_jobs[model_type]
            job = job_info["job_object"]
            
            status_info = {
                "model_type": model_type,
                "job_id": job_info["job_id"],
                "status": job.status,
                "dashboard_url": job_info["dashboard_url"],
                "submit_time": job_info["submit_time"],
                "elapsed_time": time.time() - job_info["submit_time"]
            }
            
            # 檢查是否完成
            if hasattr(job, 'success'):
                status_info["success"] = job.success
                if hasattr(job, 'failure_reason') and job.failure_reason:
                    status_info["failure_reason"] = job.failure_reason
            
            logger.info(f"📊 {model_type}狀態: {job.status}")
            
            return status_info
            
        except Exception as e:
            logger.error(f"❌ 檢查{model_type}狀態失敗: {e}")
            return {"error": str(e)}
    
    def run_comprehensive_test(self):
        """運行綜合測試"""
        logger.info("🚀 開始形狀修復綜合測試...")
        
        results = {
            "test_start_time": time.time(),
            "api_token_available": bool(self.api_token),
            "target_device": self.target_device.name if self.target_device else None,
            "model_uploads": {},
            "compile_jobs": {},
            "job_statuses": {}
        }
        
        # 測試三種模型
        model_types = ['face', 'pose', 'hand']
        
        for model_type in model_types:
            logger.info(f"\n🔄 測試{model_type}模型...")
            
            # 上傳並編譯
            job_id = self.upload_and_compile_model(model_type)
            
            if job_id:
                results["model_uploads"][model_type] = self.model_uploads.get(model_type, {})
                results["compile_jobs"][model_type] = self.compile_jobs.get(model_type, {})
                
                # 檢查初始狀態
                status = self.check_job_status(model_type)
                results["job_statuses"][model_type] = status
        
        # 保存結果
        results["test_end_time"] = time.time()
        results["total_test_time"] = results["test_end_time"] - results["test_start_time"]
        
        # 統計成功率
        successful_uploads = len([k for k, v in results["model_uploads"].items() if v.get("model_id")])
        successful_compiles = len([k for k, v in results["compile_jobs"].items() if v.get("job_id")])
        
        results["summary"] = {
            "total_models": len(model_types),
            "successful_uploads": successful_uploads,
            "successful_compiles": successful_compiles,
            "upload_success_rate": f"{successful_uploads}/{len(model_types)}",
            "compile_success_rate": f"{successful_compiles}/{len(model_types)}"
        }
        
        # 保存詳細結果
        with open('fixed_shape_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("📝 結果已保存: fixed_shape_test_results.json")
        
        return results

def main():
    """主測試函數"""
    print("🔧 QAI Hub形狀修復測試")
    print("=" * 50)
    
    try:
        # 初始化測試
        tester = FixedShapeQAIHubTest()
        
        # 運行綜合測試
        results = tester.run_comprehensive_test()
        
        # 顯示結果摘要
        print("\n📊 測試結果摘要:")
        print(f"   目標設備: {results.get('target_device', 'Unknown')}")
        print(f"   上傳成功率: {results['summary']['upload_success_rate']}")
        print(f"   編譯成功率: {results['summary']['compile_success_rate']}")
        print(f"   總測試時間: {results['summary'].get('total_test_time', 0):.2f}秒")
        
        # 顯示Dashboard鏈接
        print("\n🔗 QAI Hub Dashboard鏈接:")
        for model_type, job_info in results["compile_jobs"].items():
            if job_info.get("dashboard_url"):
                print(f"   {model_type}: {job_info['dashboard_url']}")
        
        print("\n✅ 形狀修復測試完成！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
