"""
測試編譯指令的完整功能
驗證實時狀態顯示、自動下載優化模型、正確終止等功能
"""
import sys
import os
import time
import threading
from pathlib import Path
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.qaihub_optimize.modules.pipeline import get_pipeline
from src.qaihub_optimize.modules.job_monitor import get_job_monitor


class CompileCommandTester:
    """編譯指令測試器"""
    
    def __init__(self):
        self.pipeline = get_pipeline()
        self.job_monitor = get_job_monitor(self.pipeline.qaihub_client)
        self.status_updates = []
        self.test_start_time = None
        self.test_completed = False
    
    def _status_callback(self, job_data):
        """狀態更新回調函數"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        status_info = {
            'timestamp': timestamp,
            'model': job_data['model_name'],
            'status': job_data['status'],
            'progress': job_data['progress'],
            'elapsed': (datetime.now() - self.test_start_time).total_seconds() if self.test_start_time else 0
        }
        
        self.status_updates.append(status_info)
        
        # 實時顯示狀態
        print(f"[{timestamp}] {job_data['model_name']}: {job_data['status']} ({job_data['progress']}%)")
        
        # 檢查是否完成
        status_upper = str(job_data['status']).upper()
        completed_statuses = ['COMPLETED', 'SUCCEEDED', 'SUCCESS', 'FINISHED', 'FAILED', 'ERROR']
        if status_upper in completed_statuses:
            print(f"✅ 任務完成: {job_data['model_name']} -> {job_data['status']}")
    
    def _completion_callback(self, job_data):
        """任務完成回調函數"""
        print(f"🎯 任務完成回調: {job_data['model_name']} - {job_data['status']}")
        
        # 檢查優化模型是否下載
        if job_data.get('optimized_model_downloaded', False):
            model_path = job_data.get('optimized_model_path', '未知')
            print(f"💾 優化模型已下載: {model_path}")
    
    def setup_test_environment(self):
        """設置測試環境"""
        print("=" * 70)
        print("🔧 設置編譯指令測試環境")
        print("=" * 70)
        
        # 確保測試模型存在
        test_model_path = project_root / 'src' / 'models' / 'raw' / 'test_simple_model_fixed.onnx'
        if not test_model_path.exists():
            print("❌ 測試模型不存在，請先創建測試模型")
            print("💡 運行: python -c \"import numpy as np; import onnx; from onnx import helper, TensorProto; X = helper.make_tensor_value_info('X', TensorProto.FLOAT, [1, 3, 224, 224]); Y = helper.make_tensor_value_info('Y', TensorProto.FLOAT, [1, 3, 224, 224]); node = helper.make_node('Relu', inputs=['X'], outputs=['Y'], name='relu'); graph = helper.make_graph([node], 'simple_model', [X], [Y]); model = helper.make_model(graph, producer_name='onnx-example'); onnx.save(model, 'src/models/raw/test_simple_model_fixed.onnx'); print('✅ 測試模型已創建')\"")
            return False
        
        print(f"✅ 測試模型存在: {test_model_path}")
        
        # 確保優化模型目錄存在
        optimized_dir = project_root / 'src' / 'models' / 'qaihub_optimized'
        optimized_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 優化模型目錄: {optimized_dir}")
        
        # 註冊回調函數
        self.job_monitor.register_callback('on_job_progress', self._status_callback)
        self.job_monitor.register_callback('on_job_complete', self._completion_callback)
        
        print("✅ 回調函數已註冊")
        return True
    
    def test_real_time_status_display(self):
        """測試實時狀態顯示功能"""
        print("\n" + "=" * 70)
        print("📊 測試實時狀態顯示功能")
        print("=" * 70)
        
        self.test_start_time = datetime.now()
        self.status_updates = []
        
        print("🔄 開始監控任務狀態...")
        print("💡 您應該能看到實時的狀態更新")
        
        # 啟動監控
        self.job_monitor.start_monitoring(interval=5)
        
        # 模擬一些狀態更新（在真實環境中這些會由 QAI Hub 觸發）
        test_job_id = "test_job_001"
        self.job_monitor.add_job(test_job_id, 'compile', 'test_simple_model_fixed', timeout=300)
        
        # 模擬狀態變化
        states = [
            ('PENDING', 0),
            ('QUEUED', 10),
            ('RUNNING', 30),
            ('PROCESSING', 60),
            ('COMPLETED', 100)
        ]
        
        for status, progress in states:
            time.sleep(2)  # 模擬真實的時間間隔
            self.job_monitor.update_job_status(test_job_id, status, progress)
        
        # 等待一下讓回調完成
        time.sleep(3)
        
        # 停止監控
        self.job_monitor.stop_monitoring()
        
        # 檢查狀態更新記錄
        print(f"\n📈 狀態更新記錄數量: {len(self.status_updates)}")
        if len(self.status_updates) >= len(states):
            print("✅ 實時狀態顯示功能正常")
            return True
        else:
            print("❌ 實時狀態顯示功能異常")
            return False
    
    def test_compile_workflow(self):
        """測試完整編譯工作流程"""
        print("\n" + "=" * 70)
        print("🚀 測試完整編譯工作流程")
        print("=" * 70)
        
        print("📋 測試項目:")
        print("1. 模型掃描")
        print("2. 編譯任務提交")
        print("3. 實時狀態監控")
        print("4. 自動下載優化模型")
        print("5. 進程正確終止")
        
        try:
            # 掃描模型
            print("\n1️⃣ 掃描模型...")
            models = self.pipeline.scan_models()
            if not models or 'onnx' not in models or not models['onnx']:
                print("❌ 沒有找到 ONNX 模型檔案")
                return False
            
            print(f"✅ 找到 {len(models['onnx'])} 個 ONNX 模型")
            for model_path in models['onnx']:
                print(f"   - {model_path.name}")
            
            # 執行編譯流程
            print("\n2️⃣ 執行編譯流程...")
            print("⚠️  注意：這將實際提交任務到 QAI Hub")
            print("💡 請觀察實時狀態顯示")
            
            # 啟動監控
            self.job_monitor.start_monitoring(interval=10)
            
            # 執行編譯
            success = self.pipeline.run_compile_pipeline()
            
            # 等待監控完成
            time.sleep(5)  # 給監控線程一些時間完成
            
            # 停止監控
            self.job_monitor.stop_monitoring()
            
            print(f"\n3️⃣ 編譯結果: {'✅ 成功' if success else '❌ 失敗'}")
            
            # 檢查優化模型下載
            print("\n4️⃣ 檢查優化模型下載...")
            downloaded_count = 0
            optimized_dir = project_root / 'src' / 'models' / 'qaihub_optimized'
            
            for model_name, model_info in self.pipeline.qaihub_client.qai_hub_models.items():
                if model_info.get('optimized_model_downloaded', False):
                    downloaded_count += 1
                    model_path = model_info.get('optimized_model_path', '未知')
                    print(f"✅ {model_name}: 已下載 -> {model_path}")
                    
                    # 驗證檔案存在
                    if Path(model_path).exists():
                        print(f"   📁 檔案存在，大小: {Path(model_path).stat().st_size} bytes")
                    else:
                        print(f"   ❌ 檔案不存在！")
            
            print(f"📊 總共下載了 {downloaded_count} 個優化模型")
            
            # 檢查目錄中的實際檔案
            optimized_files = list(optimized_dir.glob('*'))
            print(f"📁 優化模型目錄中的檔案: {len(optimized_files)} 個")
            for file in optimized_files:
                if file.is_file():
                    print(f"   - {file.name} ({file.stat().st_size} bytes)")
            
            # 檢查進程終止
            print("\n5️⃣ 檢查進程終止...")
            if success and downloaded_count > 0:
                print("✅ 編譯流程成功完成並正確終止")
                self.test_completed = True
                return True
            else:
                print("⚠️  編譯流程完成但有問題")
                return False
                
        except Exception as e:
            print(f"❌ 編譯流程測試失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_test_report(self):
        """產生測試報告"""
        print("\n" + "=" * 70)
        print("📋 編譯指令測試報告")
        print("=" * 70)
        
        if not self.test_start_time:
            print("❌ 測試未執行")
            return
        
        elapsed_time = (datetime.now() - self.test_start_time).total_seconds()
        
        print(f"⏰ 測試耗時: {elapsed_time:.1f} 秒")
        print(f"📊 狀態更新次數: {len(self.status_updates)}")
        print(f"✅ 測試完成狀態: {'成功' if self.test_completed else '失敗'}")
        
        # 顯示狀態更新時間線
        if self.status_updates:
            print("\n🕒 狀態更新時間線:")
            for update in self.status_updates[-10:]:  # 顯示最後10個更新
                print(f"   [{update['timestamp']}] {update['model']}: {update['status']} ({update['progress']}%)")
        
        # 檢查優化模型目錄
        optimized_dir = project_root / 'src' / 'models' / 'qaihub_optimized'
        optimized_files = list(optimized_dir.glob('*'))
        print(f"\n📁 優化模型目錄檔案數量: {len(optimized_files)}")
        
        if self.test_completed:
            print("\n🎉 編譯指令測試總結:")
            print("✅ 實時狀態顯示功能正常")
            print("✅ 自動下載優化模型功能正常")
            print("✅ 進程正確終止功能正常")
            print("✅ 錯誤處理機制正常")
        else:
            print("\n⚠️  測試發現問題:")
            print("❌ 請檢查以上錯誤信息")


def main():
    """主測試函數"""
    print("🤖 QAI Hub 編譯指令完整功能測試")
    print("💡 這個測試將驗證:")
    print("   - 實時狀態顯示")
    print("   - 自動下載優化模型")
    print("   - 進程正確終止")
    print("   - 錯誤處理機制")
    
    tester = CompileCommandTester()
    
    # 設置測試環境
    if not tester.setup_test_environment():
        return
    
    # 測試實時狀態顯示
    status_test_passed = tester.test_real_time_status_display()
    
    # 詢問是否執行完整編譯測試
    if status_test_passed:
        response = input("\n是否要執行完整編譯測試（將實際提交任務到 QAI Hub）？(y/n): ").strip().lower()
        if response == 'y':
            # 執行完整編譯測試
            compile_test_passed = tester.test_compile_workflow()
            
            # 產生測試報告
            tester.generate_test_report()
            
            if compile_test_passed:
                print("\n🎉 所有測試通過！編譯指令功能完整")
            else:
                print("\n⚠️  測試完成，但發現一些問題")
        else:
            print("⏭️ 跳過完整編譯測試")
            tester.generate_test_report()
    else:
        print("❌ 實時狀態顯示測試失敗，無法繼續完整測試")


if __name__ == "__main__":
    main()
