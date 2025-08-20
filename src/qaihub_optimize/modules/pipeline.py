"""
工作流程管道模組
負責管理完整的 QAI Hub 最佳化工作流程
"""
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import sys

from .scanner import ModelScanner
from .conversion import ModelConverter
from .format_check import FormatChecker
from .qaihub_client import QAIHubClient


class QAIHubPipeline:
    """QAI Hub 工作流程管道管理類別"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        初始化工作流程管道
        
        Args:
            base_dir: 基礎目錄路徑
        """
        self.base_dir = base_dir or Path.cwd()
        # 確保基礎目錄指向正確的 models 目錄
        models_base_dir = self.base_dir / 'models' if (self.base_dir / 'models').exists() else self.base_dir
        self.scanner = ModelScanner(models_base_dir)
        self.converter = ModelConverter()
        self.format_checker = FormatChecker(models_base_dir)
        self.qaihub_client = QAIHubClient(models_base_dir)
        self.current_models = {}
    
    def scan_models(self) -> Dict[str, List[Path]]:
        """
        掃描模型檔案
        
        Returns:
            掃描到的模型檔案字典
        """
        print("🔍 開始掃描模型檔案...")
        try:
            models = self.scanner.scan_org_directory()
            self.current_models = models
            return models
        except FileNotFoundError as e:
            print(f"❌ {e}")
            return {}
        except Exception as e:
            print(f"❌ 掃描模型失敗: {e}")
            return {}
    
    def convert_tflite_models(self, ask_user: bool = True) -> bool:
        """
        轉換 TFLite 模型到 ONNX
        
        Args:
            ask_user: 是否詢問使用者
            
        Returns:
            轉換是否成功
        """
        tflite_files = self.current_models.get('tflite', [])
        if not tflite_files:
            print("ℹ️ 沒有找到 TFLite 模型需要轉換")
            return True
        
        print(f"🔄 發現 {len(tflite_files)} 個 TFLite 模型需要轉換")
        
        if ask_user:
            response = input(f"是否要將 {len(tflite_files)} 個 TFLite 模型轉換為 ONNX？(y/n): ").strip().lower()
            if response != 'y':
                print("⏭️ 跳過 TFLite 轉換")
                return True
        
        success_count = 0
        failed_files = []
        
        for tflite_path in tflite_files:
            try:
                result = self.converter.convert_tflite_to_onnx(tflite_path, self.base_dir / 'models' / 'onnx')
                if result['status'] == 'ok':
                    success_count += 1
                    print(f"✅ 轉換成功: {tflite_path.name}")
                else:
                    failed_files.append(tflite_path.name)
                    print(f"❌ 轉換失敗: {tflite_path.name} - {result.get('error', '未知錯誤')}")
            except Exception as e:
                failed_files.append(tflite_path.name)
                print(f"❌ 轉換異常: {tflite_path.name} - {e}")
        
        print(f"\n📊 TFLite 轉換結果: {success_count} 成功, {len(failed_files)} 失敗")
        if failed_files:
            print("❌ 轉換失敗的檔案:")
            for filename in failed_files:
                print(f"   - {filename}")
        
        return len(failed_files) == 0
    
    def check_and_fix_onnx_models(self) -> bool:
        """
        檢查並修復 ONNX 模型格式
        
        Returns:
            檢查修復是否成功
        """
        onnx_files = self.current_models.get('onnx', [])
        if not onnx_files:
            print("ℹ️ 沒有找到 ONNX 模型需要檢查")
            return True
        
        print(f"🔧 檢查 {len(onnx_files)} 個 ONNX 模型格式...")
        
        invalid_models = []
        fixed_count = 0
        
        for onnx_path in onnx_files:
            try:
                # 檢查模型格式
                is_valid, error = self.format_checker.check_onnx_model(onnx_path)
                if not is_valid:
                    print(f"⚠️ 格式異常: {onnx_path.name} - {error}")
                    invalid_models.append((onnx_path.name, error))
                    
                    # 嘗試修復 value_info
                    if "value_info" in str(error).lower():
                        fixed = self.format_checker.fix_onnx_value_info(onnx_path)
                        if fixed:
                            fixed_count += 1
                            print(f"✅ 修復成功: {onnx_path.name}")
                        else:
                            print(f"❌ 修復失敗: {onnx_path.name}")
                else:
                    print(f"✅ 格式正常: {onnx_path.name}")
                    
            except Exception as e:
                print(f"❌ 檢查異常: {onnx_path.name} - {e}")
                invalid_models.append((onnx_path.name, str(e)))
        
        print(f"\n📊 ONNX 檢查結果: {fixed_count} 個修復, {len(invalid_models)} 個異常")
        
        if invalid_models:
            print("❌ 格式異常的模型:")
            for filename, error in invalid_models:
                print(f"   - {filename}: {error}")
            return False
        
        return True
    
    def run_compile_pipeline(self, source: str = 'onnx') -> bool:
        """
        執行編譯工作流程
        
        Args:
            source: 模型來源類型
            
        Returns:
            流程是否成功
        """
        print(f"\n🚀 開始編譯工作流程 (source: {source})")
        
        # 掃描模型
        models = self.scan_models()
        if not models:
            print("❌ 沒有找到可用的模型檔案")
            return False
        
        # 根據來源類型處理模型
        if source == 'tflite':
            if not self.convert_tflite_models(ask_user=True):
                print("❌ TFLite 轉換失敗，流程中止")
                return False
            source = 'onnx'  # 轉換後使用 ONNX
        
        # 檢查 ONNX 模型格式
        if source == 'onnx':
            if not self.check_and_fix_onnx_models():
                print("❌ ONNX 格式檢查失敗，流程中止")
                return False
        
        # 載入模型到 QAI Hub 客戶端
        ext_map = {
            'onnx': '.onnx',
            'tflite': '.tflite', 
            'dlc': '.dlc'
        }
        
        if source not in ext_map:
            print(f"❌ 不支援的來源類型: {source}")
            return False
        
        loaded = self.qaihub_client.load_models(source, 'org', ext_map[source])
        if not loaded:
            print("❌ 載入模型失敗")
            return False
        
        # 上傳模型到 QAI Hub
        if not self.qaihub_client.upload_models():
            print("❌ 上傳模型失敗")
            return False
        
        # 提交編譯任務
        if not self.qaihub_client.submit_compilation_jobs():
            print("❌ 提交編譯任務失敗")
            return False
        
        # 等待編譯完成
        final_statuses = self.qaihub_client.wait_for_jobs_completion('compile')
        
        # 產生報告
        report_file = self.qaihub_client.generate_html_report('compile')
        
        # 檢查最終狀態
        success_count = sum(1 for status in final_statuses.values() 
                          if str(status).upper() in ['COMPLETED', 'SUCCEEDED', 'SUCCESS'])
        
        print(f"\n🎯 編譯流程完成: {success_count}/{len(final_statuses)} 個任務成功")
        print(f"📊 詳細報告: {report_file}")
        
        return success_count > 0
    
    def run_profile_pipeline(self) -> bool:
        """
        執行效能分析工作流程
        
        Returns:
            流程是否成功
        """
        print(f"\n🚀 開始效能分析工作流程")
        
        # 掃描模型
        models = self.scan_models()
        if not models:
            print("❌ 沒有找到可用的模型檔案")
            return False
        
        # 檢查裝置支援
        support_info = self.qaihub_client.check_device_support()
        
        # 根據裝置支援過濾模型
        models_to_process = []
        for ext, files in models.items():
            if ext == 'onnx' and support_info.get('onnx', False):
                models_to_process.extend(files)
            elif ext == 'tflite' and support_info.get('tflite', False):
                models_to_process.extend(files)
            elif ext == 'dlc' and support_info.get('dlc', False):
                models_to_process.extend(files)
            else:
                print(f"⏭️ 跳過 {ext.upper()} 格式，裝置不支援")
        
        if not models_to_process:
            print("❌ 沒有裝置支援的模型格式")
            return False
        
        print(f"✅ 將處理 {len(models_to_process)} 個裝置支援的模型")
        
        # 載入所有支援的模型
        loaded_count = 0
        for ext in ['onnx', 'tflite', 'dlc']:
            if support_info.get(ext, False):
                loaded = self.qaihub_client.load_models(ext, 'org', f'.{ext}')
                if loaded:
                    loaded_count += len(loaded)
        
        if loaded_count == 0:
            print("❌ 載入模型失敗")
            return False
        
        # 上傳模型到 QAI Hub
        if not self.qaihub_client.upload_models():
            print("❌ 上傳模型失敗")
            return False
        
        # 提交分析任務
        if not self.qaihub_client.submit_profile_jobs():
            print("❌ 提交分析任務失敗")
            return False
        
        # 等待分析完成
        final_statuses = self.qaihub_client.wait_for_jobs_completion('profile')
        
        # 產生報告
        report_file = self.qaihub_client.generate_html_report('profile')
        
        # 檢查最終狀態
        success_count = sum(1 for status in final_statuses.values() 
                          if str(status).upper() in ['COMPLETED', 'SUCCEEDED', 'SUCCESS'])
        
        print(f"\n🎯 分析流程完成: {success_count}/{len(final_statuses)} 個任務成功")
        print(f"📊 詳細報告: {report_file}")
        
        return success_count > 0
    
    def run_full_pipeline(self, do_profile: bool = True, do_infer: bool = False) -> bool:
        """
        執行完整工作流程 (編譯 + 分析 + 推論)
        
        Args:
            do_profile: 是否執行效能分析
            do_infer: 是否執行推論測試
            
        Returns:
            流程是否成功
        """
        print(f"\n🚀 開始完整工作流程 (Profile: {do_profile}, Infer: {do_infer})")
        
        # 執行編譯流程
        compile_success = self.run_compile_pipeline('onnx')
        if not compile_success:
            print("❌ 編譯流程失敗，完整流程中止")
            return False
        
        # 執行分析流程
        profile_success = True
        if do_profile:
            profile_success = self.run_profile_pipeline()
            if not profile_success:
                print("⚠️ 分析流程失敗，繼續後續流程")
        
        # 執行推論測試 (placeholder)
        if do_infer:
            print("\n🤖 開始推論測試...")
            # 這裡可以整合推論測試功能
            print("✅ 推論測試完成 (placeholder)")
        
        print(f"\n🎉 完整工作流程完成!")
        print(f"   - 編譯: {'✅' if compile_success else '❌'}")
        print(f"   - 分析: {'✅' if profile_success else '❌'}")
        print(f"   - 推論: {'✅' if do_infer else '⏭️'}")
        
        return compile_success and (not do_profile or profile_success)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        取得當前模型資訊
        
        Returns:
            模型資訊字典
        """
        return {
            'scanned_models': self.current_models,
            'qaihub_models': self.qaihub_client.qai_hub_models,
            'device': self.qaihub_client.target_device.name if self.qaihub_client.target_device else None
        }
    
    def run_compile_profile_pipeline(self, do_infer: bool = False) -> bool:
        """
        執行編譯+分析工作流程
        
        Args:
            do_infer: 是否執行推論測試
            
        Returns:
            流程是否成功
        """
        print(f"\n🚀 開始編譯+分析工作流程 (Infer: {do_infer})")
        
        # 執行編譯流程
        compile_success = self.run_compile_pipeline('onnx')
        if not compile_success:
            print("❌ 編譯流程失敗，完整流程中止")
            return False
        
        # 執行分析流程
        profile_success = self.run_profile_pipeline()
        if not profile_success:
            print("⚠️ 分析流程失敗，繼續後續流程")
        
        # 執行推論測試 (placeholder)
        if do_infer:
            print("\n🤖 開始推論測試...")
            # 這裡可以整合推論測試功能
            print("✅ 推論測試完成 (placeholder)")
        
        print(f"\n🎉 編譯+分析工作流程完成!")
        print(f"   - 編譯: {'✅' if compile_success else '❌'}")
        print(f"   - 分析: {'✅' if profile_success else '❌'}")
        print(f"   - 推論: {'✅' if do_infer else '⏭️'}")
        
        return compile_success and profile_success


# 單例模式實例
_pipeline_instance = None

def get_pipeline(base_dir: Optional[Path] = None) -> QAIHubPipeline:
    """
    取得工作流程管道實例（單例模式）
    
    Args:
        base_dir: 基礎目錄路徑
        
    Returns:
        QAIHubPipeline 實例
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = QAIHubPipeline(base_dir)
    return _pipeline_instance
