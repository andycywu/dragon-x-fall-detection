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
from .job_monitor import get_job_monitor
from .preprocessor import get_model_preprocessor, preprocess_models

# 配置常數 - 從環境變數讀取
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

MODEL_SOURCE_DIR = os.getenv('MODEL_SOURCE_DIR', 'raw')  # 原始模型目錄名稱
OPTIMIZED_MODEL_DIR = os.getenv('OPTIMIZED_MODEL_DIR', 'qaihub_optimized')  # 優化模型目錄名稱
ONNX_MODEL_DIR = os.getenv('ONNX_MODEL_DIR', 'onnx')  # ONNX 模型目錄名稱


class QAIHubPipeline:
    """QAI Hub 工作流程管道管理類別"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        初始化工作流程管道
        
        Args:
            base_dir: 基礎目錄路徑
        """
        self.base_dir = base_dir or Path.cwd()
        
        # 使用環境變數中的路徑配置
        models_base_dir_env = os.getenv('MODELS_BASE_DIR')
        if models_base_dir_env:
            models_base_dir = Path(models_base_dir_env)
            print(f"📁 使用環境變數中的模型基礎目錄: {models_base_dir}")
        else:
            # 使用動態路徑，從當前工作目錄向上找到項目根目錄
            current_path = Path.cwd()
            project_root = current_path
            # 如果當前目錄是 src/qaihub_optimize/modules，則向上找到項目根目錄
            if 'src' in current_path.parts and 'qaihub_optimize' in current_path.parts:
                project_root = current_path.parent.parent.parent
            models_base_dir = project_root / 'src' / 'models'
            print(f"📁 使用動態計算的模型基礎目錄: {models_base_dir}")
        
        print(f"📁 項目根目錄: {project_root if 'project_root' in locals() else 'N/A'}")
        print(f"📁 models 目錄: {models_base_dir}")
        print(f"📁 models 目錄是否存在: {models_base_dir.exists()}")
        
        # 確保目錄存在
        models_base_dir.mkdir(parents=True, exist_ok=True)
        
        self.scanner = ModelScanner(models_base_dir)
        self.converter = ModelConverter()
        self.format_checker = FormatChecker(models_base_dir)
        self.qaihub_client = QAIHubClient(models_base_dir)
        self.job_monitor = get_job_monitor(self.qaihub_client)
        self.current_models = {}
    
    def scan_models(self) -> Dict[str, List[Path]]:
        """
        掃描模型檔案
        
        Returns:
            掃描到的模型檔案字典
        """
        print("🔍 開始掃描模型檔案...")
        try:
            models = self.scanner.scan_model_directory(MODEL_SOURCE_DIR)
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
                result = self.converter.convert_tflite_to_onnx(tflite_path, self.base_dir / 'models' / ONNX_MODEL_DIR)
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
                error = self.format_checker.check_onnx_model(onnx_path)
                if error:
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
        執行編譯工作流程（自動根據目標裝置支援決定來源類型）
        
        Args:
            source: 模型來源類型 ('onnx', 'tflite', 'dlc')
            
        Returns:
            流程是否成功
        """
        print(f"\n🚀 開始編譯工作流程 (來源: {source})")
        
        # 執行模型預處理（自動轉換和移動到 onnx 目錄）
        preprocess_result = preprocess_models()
        if not preprocess_result:
            print("❌ 模型預處理失敗")
            return False
        
        # 掃描 onnx 目錄中的模型
        onnx_models = self.scanner.scan_model_directory(ONNX_MODEL_DIR)
        if not onnx_models.get('onnx'):
            print("❌ 沒有找到可用的 ONNX 模型檔案")
            return False
        
        self.current_models = onnx_models
        print(f"✅ 找到 {len(onnx_models['onnx'])} 個 ONNX 模型檔案")
        
        # 檢查裝置支援的格式
        support_info = self.qaihub_client.check_device_support()
        print(f"\n📋 裝置支援格式檢查:")
        for framework, supported in support_info.items():
            status = "✅" if supported else "❌"
            print(f"   {status} {framework.upper()}: {'支援' if supported else '不支援'}")
        
        # 現在只使用 ONNX 格式（經過預處理後所有模型都在 onnx 目錄中）
        source = 'onnx'
        print("✅ 使用 ONNX 格式（經過預處理後所有模型都在 onnx 目錄中）")
        
        print(f"📋 模型來源: {source}")
        
        # 檢查 ONNX 模型格式（如果使用 ONNX）
        if source == 'onnx':
            if not self.check_and_fix_onnx_models():
                print("❌ ONNX 格式檢查失敗，流程中止")
                return False
        
        # 在載入模型前再次檢查並修復 value_info 問題
        print("🔧 載入前再次檢查並修復 ONNX 模型 value_info 問題...")
        onnx_files = self.current_models.get('onnx', [])
        for onnx_path in onnx_files:
            error = self.format_checker.check_onnx_model(onnx_path)
            if error and "value_info" in str(error).lower():
                print(f"⚠️  發現 value_info 問題: {onnx_path.name}")
                fixed = self.format_checker.fix_onnx_value_info(onnx_path)
                if fixed:
                    print(f"✅ 修復成功: {onnx_path.name}")
                else:
                    print(f"❌ 修復失敗: {onnx_path.name}")
        
        # 載入模型到 QAI Hub 客戶端
        ext_map = {
            'onnx': '.onnx',
            'tflite': '.tflite', 
            'dlc': '.dlc'
        }
        
        if source not in ext_map:
            print(f"❌ 不支援的來源類型: {source}")
            return False
        
        loaded = self.qaihub_client.load_models(source, ONNX_MODEL_DIR, ext_map[source])
        if not loaded:
            print("❌ 載入模型失敗")
            return False
        
        # 上傳模型到 QAI Hub
        if not self.qaihub_client.upload_models():
            print("❌ 上傳模型失敗")
            return False
        
        # 提交編譯任務（不傳遞量化選項）
        if not self.qaihub_client.submit_compilation_jobs():
            print("❌ 提交編譯任務失敗")
            return False
        
        # 使用新的 job monitor 等待編譯完成（實時顯示狀態並自動下載優化模型）
        print("\n🔍 開始監控編譯任務狀態...")
        compile_success = self.job_monitor.wait_for_compile_jobs(
            self.qaihub_client.qai_hub_models, 
            timeout_minutes=30
        )
        
        # 產生報告
        report_file = self.qaihub_client.generate_html_report('compile')
        
        # 檢查優化模型下載狀態
        downloaded_models = []
        for model_name, model_info in self.qaihub_client.qai_hub_models.items():
            if model_info.get('optimized_model_downloaded', False):
                downloaded_models.append(model_name)
        
        print(f"\n🎯 編譯流程完成: {'成功' if compile_success else '失敗'}")
        print(f"📊 詳細報告: {report_file}")
        
        if downloaded_models:
            print(f"💾 已下載優化模型 ({len(downloaded_models)} 個):")
            for model_name in downloaded_models:
                model_path = self.qaihub_client.qai_hub_models[model_name].get('optimized_model_path', '未知路徑')
                quantize_info = f" (量化: {model_info.get('quantize', '無')})" if model_info.get('quantize') else ""
                print(f"   - {model_name} -> {model_path}{quantize_info}")
        else:
            print("⚠️  沒有下載優化模型")
        
        return compile_success
    
    def run_profile_pipeline(self) -> bool:
        """
        執行效能分析工作流程
        
        Returns:
            流程是否成功
        """
        print(f"\n🚀 開始效能分析工作流程")
        
        # 執行模型預處理（自動轉換和移動到 onnx 目錄）
        preprocess_result = preprocess_models()
        if not preprocess_result:
            print("❌ 模型預處理失敗")
            return False
        
        # 掃描 onnx 目錄中的模型
        onnx_models = self.scanner.scan_model_directory(ONNX_MODEL_DIR)
        if not onnx_models.get('onnx'):
            print("❌ 沒有找到可用的 ONNX 模型檔案")
            return False
        
        self.current_models = onnx_models
        print(f"✅ 找到 {len(onnx_models['onnx'])} 個 ONNX 模型檔案")
        
        # 檢查裝置支援的格式
        support_info = self.qaihub_client.check_device_support()
        print(f"\n📋 裝置支援格式檢查:")
        for framework, supported in support_info.items():
            status = "✅" if supported else "❌"
            print(f"   {status} {framework.upper()}: {'支援' if supported else '不支援'}")
        
        # 現在只使用 ONNX 格式（經過預處理後所有模型都在 onnx 目錄中）
        source = 'onnx'
        print("✅ 使用 ONNX 格式（經過預處理後所有模型都在 onnx 目錄中）")
        
        print(f"📋 模型來源: {source}")
        
        # 檢查 ONNX 模型格式
        if not self.check_and_fix_onnx_models():
            print("❌ ONNX 格式檢查失敗，流程中止")
            return False
        
        # 在載入模型前再次檢查並修復 value_info 問題
        print("🔧 載入前再次檢查並修復 ONNX 模型 value_info 問題...")
        onnx_files = self.current_models.get('onnx', [])
        for onnx_path in onnx_files:
            error = self.format_checker.check_onnx_model(onnx_path)
            if error and "value_info" in str(error).lower():
                print(f"⚠️  發現 value_info 問題: {onnx_path.name}")
                fixed = self.format_checker.fix_onnx_value_info(onnx_path)
                if fixed:
                    print(f"✅ 修復成功: {onnx_path.name}")
                else:
                    print(f"❌ 修復失敗: {onnx_path.name}")
        
        # 載入模型到 QAI Hub 客戶端
        loaded = self.qaihub_client.load_models(source, ONNX_MODEL_DIR, '.onnx')
        if not loaded:
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
        
        # 使用新的 job monitor 等待分析完成（實時顯示狀態）
        print("\n🔍 開始監控分析任務狀態...")
        profile_success = self.job_monitor.wait_for_profile_jobs(
            self.qaihub_client.qai_hub_models, 
            timeout_minutes=30
        )
        
        # 產生報告
        report_file = self.qaihub_client.generate_html_report('profile')
        
        print(f"\n🎯 分析流程完成: {'成功' if profile_success else '失敗'}")
        print(f"📊 詳細報告: {report_file}")
        
        return profile_success
    
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
        compile_success = self.run_compile_pipeline()
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
        compile_success = self.run_compile_pipeline()
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
