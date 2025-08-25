"""
專門測試優化模型下載功能的簡化測試腳本
只測試下載功能，不包含用戶交互
"""
import sys
import os
import time
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.qaihub_optimize.modules.pipeline import get_pipeline
from src.qaihub_optimize.modules.job_monitor import get_job_monitor


class DownloadTester:
    """專門測試下載功能的測試器"""
    
    def __init__(self):
        self.pipeline = get_pipeline()
        self.job_monitor = get_job_monitor(self.pipeline.qaihub_client)
        self.test_start_time = None
    
    def setup_test_environment(self):
        """設置測試環境"""
        print("=" * 60)
        print("🔧 設置下載功能測試環境")
        print("=" * 60)
        
        # 確保測試模型存在
        test_model_path = project_root / 'src' / 'models' / 'raw' / 'test_simple_model_fixed.onnx'
        if not test_model_path.exists():
            print("❌ 測試模型不存在，請先創建測試模型")
            return False
        
        print(f"✅ 測試模型存在: {test_model_path}")
        
        # 確保優化模型目錄存在
        optimized_dir = project_root / 'src' / 'models' / 'qaihub_optimized'
        optimized_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 優化模型目錄: {optimized_dir}")
        
        return True
    
    def test_download_functionality(self):
        """測試下載功能"""
        print("\n" + "=" * 60)
        print("💾 測試優化模型下載功能")
        print("=" * 60)
        
        try:
            # 使用真實的任務來測試下載功能
            # 先提交一個真實的編譯任務，然後等待它完成
            print("1️⃣ 提交真實編譯任務...")
            
            # 載入模型到 QAI Hub 客戶端
            loaded = self.pipeline.qaihub_client.load_models('onnx', 'raw', '.onnx')
            if not loaded:
                print("❌ 載入模型失敗")
                return False
            
            # 上傳模型到 QAI Hub
            if not self.pipeline.qaihub_client.upload_models():
                print("❌ 上傳模型失敗")
                return False
            
            # 提交編譯任務
            if not self.pipeline.qaihub_client.submit_compilation_jobs():
                print("❌ 提交編譯任務失敗")
                return False
            
            # 獲取真實的 job_id
            model_name = "test_simple_model_fixed"
            qaihub_model = self.pipeline.qaihub_client.qai_hub_models.get(model_name, {})
            compile_job = qaihub_model.get('compile_job')
            
            if not compile_job or not hasattr(compile_job, 'job_id'):
                print("❌ 無法取得真實的 job_id")
                return False
            
            real_job_id = compile_job.job_id
            print(f"✅ 取得真實任務 ID: {real_job_id}")
            
            # 添加任務到監控器
            self.job_monitor.add_job(real_job_id, 'compile', model_name, timeout=300)
            
            # 檢查優化模型目錄中的檔案
            optimized_dir = project_root / 'src' / 'models' / 'qaihub_optimized'
            optimized_files_before = list(optimized_dir.glob('*'))
            print(f"📁 下載前檔案數量: {len(optimized_files_before)}")
            
            # 等待任務完成（這裡我們等待一段時間）
            print("⏳ 等待任務完成...")
            time.sleep(30)  # 等待30秒讓任務有時間完成
            
            # 手動觸發下載（模擬真實的下載流程）
            job_info = self.job_monitor.get_job_status(real_job_id)
            if job_info:
                print("🔄 手動觸發下載流程...")
                
                # 這裡我們直接調用 _download_optimized_model 方法
                if hasattr(self.job_monitor, '_download_optimized_model'):
                    try:
                        self.job_monitor._download_optimized_model(real_job_id, job_info)
                        print("✅ 下載方法調用成功")
                    except Exception as e:
                        print(f"❌ 下載方法執行失敗: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print("❌ job_monitor 沒有 _download_optimized_model 方法")
            
            # 檢查下載後的檔案
            time.sleep(5)  # 給下載一些時間
            optimized_files_after = list(optimized_dir.glob('*'))
            print(f"📁 下載後檔案數量: {len(optimized_files_after)}")
            
            if len(optimized_files_after) > len(optimized_files_before):
                print("✅ 下載功能測試成功 - 有新檔案下載")
                for file in optimized_files_after:
                    if file not in optimized_files_before:
                        print(f"   📄 新檔案: {file.name} ({file.stat().st_size} bytes)")
                return True
            else:
                print("❌ 下載功能測試失敗 - 沒有新檔案下載")
                return False
                
        except Exception as e:
            print(f"❌ 下載測試失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_real_download_scenario(self):
        """測試真實的下載場景"""
        print("\n" + "=" * 60)
        print("🚀 測試真實下載場景")
        print("=" * 60)
        
        try:
            # 掃描模型
            print("1️⃣ 掃描模型...")
            models = self.pipeline.scan_models()
            if not models or 'onnx' not in models or not models['onnx']:
                print("❌ 沒有找到 ONNX 模型檔案")
                return False
            
            print(f"✅ 找到 {len(models['onnx'])} 個 ONNX 模型")
            
            # 載入模型到 QAI Hub 客戶端
            print("2️⃣ 載入模型到 QAI Hub...")
            loaded = self.pipeline.qaihub_client.load_models('onnx', 'raw', '.onnx')
            if not loaded:
                print("❌ 載入模型失敗")
                return False
            
            # 上傳模型到 QAI Hub
            print("3️⃣ 上傳模型到 QAI Hub...")
            if not self.pipeline.qaihub_client.upload_models():
                print("❌ 上傳模型失敗")
                return False
            
            # 提交編譯任務
            print("4️⃣ 提交編譯任務...")
            if not self.pipeline.qaihub_client.submit_compilation_jobs():
                print("❌ 提交編譯任務失敗")
                return False
            
            print("✅ 任務提交成功")
            
            # 將任務添加到監控器中
            print("5️⃣ 添加任務到監控器...")
            for model_name, model_info in self.pipeline.qaihub_client.qai_hub_models.items():
                compile_job = model_info.get('compile_job')
                if compile_job and hasattr(compile_job, 'job_id'):
                    job_id = compile_job.job_id
                    self.job_monitor.add_job(job_id, 'compile', model_name, timeout=300)
                    print(f"✅ 添加任務到監控器: {model_name} -> {job_id}")
            
            # 啟動監控循環來觸發自動下載
            print("6️⃣ 啟動監控循環...")
            self.job_monitor.start_monitoring(interval=5)
            
            # 等待任務完成（使用智能等待，最多等待10分鐘）
            print("6️⃣ 等待任務完成和自動下載...")
            max_wait_time = 600  # 10分鐘
            wait_interval = 10   # 每10秒檢查一次
            waited = 0
            
            while waited < max_wait_time:
                # 檢查是否有任務完成
                completed = False
                for model_name, model_info in self.pipeline.qaihub_client.qai_hub_models.items():
                    if model_info.get('optimized_model_downloaded', False):
                        completed = True
                        break
                
                if completed:
                    print("✅ 檢測到優化模型已下載完成")
                    break
                
                # 打印當前狀態
                print(f"⏳ 等待中... ({waited}/{max_wait_time}秒)")
                time.sleep(wait_interval)
                waited += wait_interval
            
            # 停止監控
            print("7️⃣ 停止監控...")
            self.job_monitor.stop_monitoring()
            
            # 檢查下載狀態
            print("8️⃣ 檢查下載狀態...")
            
            # 檢查 qai_hub_models 中的狀態
            downloaded_count = 0
            for model_name, model_info in self.pipeline.qaihub_client.qai_hub_models.items():
                if model_info.get('optimized_model_downloaded', False):
                    downloaded_count += 1
                    model_path = model_info.get('optimized_model_path', '未知')
                    print(f"✅ 優化模型已下載: {model_name} -> {model_path}")
                    
                    # 檢查檔案是否存在
                    if Path(model_path).exists():
                        file_size = Path(model_path).stat().st_size
                        print(f"📊 檔案大小: {file_size} bytes")
                    else:
                        print(f"❌ 檔案不存在: {model_path}")
            
            # 同時檢查優化模型目錄中的實際檔案
            optimized_dir = project_root / 'src' / 'models' / 'qaihub_optimized'
            optimized_files = list(optimized_dir.glob('*'))
            print(f"📁 優化模型目錄中的檔案數量: {len(optimized_files)}")
            
            if downloaded_count > 0:
                print(f"✅ 總共下載了 {downloaded_count} 個優化模型")
                return True
            else:
                print("❌ 沒有優化模型被下載")
                # 提供調試信息
                print("💡 調試信息:")
                for model_name, model_info in self.pipeline.qaihub_client.qai_hub_models.items():
                    compile_job = model_info.get('compile_job')
                    if compile_job and hasattr(compile_job, 'job_id'):
                        job_id = compile_job.job_id
                        job_status = self.job_monitor.get_job_status(job_id)
                        if job_status:
                            print(f"   {model_name}: {job_status['status']} (進度: {job_status['progress']}%)")
                        else:
                            print(f"   {model_name}: 未在監控器中")
                return False
                
        except Exception as e:
            print(f"❌ 真實下載場景測試失敗: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主測試函數"""
    print("🤖 QAI Hub 優化模型下載功能測試")
    
    tester = DownloadTester()
    
    # 設置測試環境
    if not tester.setup_test_environment():
        return
    
    # 測試下載功能
    download_test_passed = tester.test_download_functionality()
    
    if download_test_passed:
        print("\n🎉 下載功能測試通過！")
    else:
        print("\n⚠️  下載功能測試失敗")
    
    # 詢問是否測試真實場景
    response = input("\n是否要測試真實下載場景（將實際提交任務到 QAI Hub）？(y/n): ").strip().lower()
    if response == 'y':
        real_test_passed = tester.test_real_download_scenario()
        if real_test_passed:
            print("\n🎉 真實下載場景測試通過！")
        else:
            print("\n⚠️  真實下載場景測試失敗")
    else:
        print("⏭️ 跳過真實下載場景測試")


if __name__ == "__main__":
    main()
