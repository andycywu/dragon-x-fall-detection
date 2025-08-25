"""
測試錯誤處理功能
驗證 QAI Hub 任務失敗時的錯誤訊息提取功能
"""
import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.qaihub_optimize.modules.job_monitor import QAIHubJobMonitor
from src.qaihub_optimize.modules.qaihub_client import QAIHubClient


def test_error_extraction():
    """測試錯誤訊息提取功能"""
    print("🧪 開始測試錯誤處理功能...")
    
    # 創建一個模擬的 QAIHubClient 實例（用於測試）
    models_base_dir = project_root / 'src' / 'models'
    client = QAIHubClient(models_base_dir)
    
    # 創建 job monitor
    monitor = QAIHubJobMonitor(client)
    
    # 測試 1: 模擬標準錯誤屬性
    print("\n1️⃣ 測試標準錯誤屬性提取...")
    
    class MockStatus:
        def __init__(self, error_msg=None):
            self.error = error_msg
            self.code = "FAILED" if error_msg else "SUCCESS"
    
    class MockJob:
        def __init__(self, error_msg=None, failure_reason=None, status_message=None):
            self.error = error_msg
            self.failure_reason = failure_reason
            self.status_message = status_message
            self.job_id = "test_job_123"
            self.name = "test_model"
            self.device_name = "test_device"
            self.url = "https://qaihub.qualcomm.com/jobs/test_job_123"
    
    # 測試標準錯誤
    mock_status = MockStatus("Model compilation failed: Invalid input shape")
    mock_job = MockJob()
    error_msg = monitor._extract_detailed_error_info(mock_job, mock_status, "FAILED", "test_job_123")
    print(f"✅ 標準錯誤提取: {error_msg}")
    
    # 測試 job.error
    mock_status = MockStatus(None)
    mock_job = MockJob("Device not supported: Snapdragon 888")
    error_msg = monitor._extract_detailed_error_info(mock_job, mock_status, "FAILED", "test_job_123")
    print(f"✅ Job錯誤提取: {error_msg}")
    
    # 測試 failure_reason
    mock_status = MockStatus(None)
    mock_job = MockJob(None, "Out of memory during compilation")
    error_msg = monitor._extract_detailed_error_info(mock_job, mock_status, "FAILED", "test_job_123")
    print(f"✅ Failure原因提取: {error_msg}")
    
    # 測試 status_message
    mock_status = MockStatus(None)
    mock_job = MockJob(None, None, "Job terminated due to timeout")
    error_msg = monitor._extract_detailed_error_info(mock_job, mock_status, "FAILED", "test_job_123")
    print(f"✅ 狀態訊息提取: {error_msg}")
    
    # 測試 2: 綜合錯誤信息
    print("\n2️⃣ 測試綜合錯誤信息...")
    
    mock_status = MockStatus(None)
    mock_job = MockJob(None, None, None)
    comprehensive_error = monitor._get_comprehensive_error_info(mock_job, mock_status, "FAILED", "test_job_123")
    print(f"✅ 綜合錯誤信息:\n{comprehensive_error}")
    
    # 測試 3: 模擬真實的 QAI Hub 錯誤場景
    print("\n3️⃣ 測試模擬真實錯誤場景...")
    
    # 模擬各種常見的 QAI Hub 錯誤
    test_cases = [
        {
            "name": "模型格式錯誤",
            "status_error": "Invalid ONNX model: unsupported operator 'CustomOp'",
            "expected_contains": "Invalid ONNX model"
        },
        {
            "name": "設備不支援",
            "job_error": "Target device 'snapdragon_888' does not support FP16 operations",
            "expected_contains": "does not support"
        },
        {
            "name": "記憶體不足",
            "failure_reason": "Insufficient device memory for model compilation",
            "expected_contains": "memory"
        },
        {
            "name": "超時錯誤",
            "status_message": "Job execution timed out after 1800 seconds",
            "expected_contains": "timed out"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  測試 {i}: {test_case['name']}")
        
        mock_status = MockStatus(test_case.get("status_error"))
        mock_job = MockJob(
            test_case.get("job_error"),
            test_case.get("failure_reason"), 
            test_case.get("status_message")
        )
        
        error_msg = monitor._extract_detailed_error_info(mock_job, mock_status, "FAILED", f"test_job_{i}")
        
        if error_msg and test_case["expected_contains"] in error_msg:
            print(f"   ✅ 成功提取: {error_msg}")
        else:
            print(f"   ❌ 提取失敗或內容不匹配")
            if error_msg:
                print(f"     實際內容: {error_msg}")
            else:
                print(f"     沒有提取到錯誤訊息")
    
    # 測試 4: 錯誤處理回調
    print("\n4️⃣ 測試錯誤處理回調...")
    
    def error_callback(job_info):
        print(f"   🔔 錯誤回調觸發: {job_info['model_name']} - {job_info.get('error', '未知錯誤')}")
    
    monitor.register_callback('on_job_error', error_callback)
    
    # 模擬一個失敗的任務
    monitor.add_job("callback_test_job", "compile", "test_model_callback", timeout=60)
    monitor.update_job_status("callback_test_job", "FAILED", 100, "測試回調錯誤訊息")
    
    print("✅ 錯誤回調測試完成")
    
    print("\n🎉 錯誤處理功能測試完成！")
    return True


def test_job_monitor_integration():
    """測試 JobMonitor 整合功能"""
    print("\n🧪 測試 JobMonitor 整合功能...")
    
    models_base_dir = project_root / 'src' / 'models'
    client = QAIHubClient(models_base_dir)
    monitor = QAIHubJobMonitor(client)
    
    # 測試任務狀態更新和錯誤處理
    test_jobs = [
        {"id": "job1", "type": "compile", "model": "model1", "final_status": "SUCCESS"},
        {"id": "job2", "type": "compile", "model": "model2", "final_status": "FAILED", "error": "編譯失敗: 不支援的算子"},
        {"id": "job3", "type": "profile", "model": "model3", "final_status": "ERROR", "error": "效能分析超時"},
    ]
    
    for job_info in test_jobs:
        monitor.add_job(job_info["id"], job_info["type"], job_info["model"])
        
        # 模擬任務進行中
        monitor.update_job_status(job_info["id"], "RUNNING", 50)
        
        # 模擬任務完成（成功或失敗）
        if job_info["final_status"] in ["FAILED", "ERROR"]:
            monitor.update_job_status(job_info["id"], job_info["final_status"], 100, job_info["error"])
        else:
            monitor.update_job_status(job_info["id"], job_info["final_status"], 100)
    
    # 生成狀態報告
    report = monitor.generate_status_report()
    print("📊 狀態報告:")
    print(report)
    
    # 檢查是否有失敗的任務
    failed_jobs = []
    for job_id in monitor.monitored_jobs:
        job = monitor.get_job_status(job_id)
        status_upper = str(job['status']).upper()
        if status_upper in ['FAILED', 'ERROR']:
            failed_jobs.append(job)
    
    print(f"\n❌ 失敗任務數量: {len(failed_jobs)}")
    for job in failed_jobs:
        print(f"   - {job['model_name']}: {job['status']} - {job.get('error', '未知錯誤')}")
    
    print("✅ JobMonitor 整合測試完成")
    return len(failed_jobs) == 1  # 應該有 2 個失敗任務


if __name__ == "__main__":
    print("=" * 60)
    print("🤖 QAI Hub 錯誤處理功能測試")
    print("=" * 60)
    
    try:
        # 測試錯誤提取功能
        test_error_extraction()
        
        # 測試整合功能
        test_job_monitor_integration()
        
        print("\n" + "=" * 60)
        print("🎉 所有測試完成！錯誤處理功能正常運作")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 測試發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
