"""
測試編譯功能與已完成任務的處理
專門測試 compile 函數是否會因為 "Results Ready" 狀態而卡住
"""
import sys
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch

# 添加模組路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.qaihub_client import QAIHubClient
from modules.job_monitor import QAIHubJobMonitor, get_job_monitor
from practical_qai_hub_onnx import PracticalQAIHubONNX

def create_mock_job(job_id, status="Results Ready"):
    """創建模擬的 QAI Hub Job 物件"""
    mock_job = Mock()
    mock_job.job_id = job_id
    mock_job.status = status
    mock_job.refresh = Mock()  # 模擬 refresh 方法
    return mock_job

def test_compile_with_completed_jobs():
    """測試編譯功能與已完成任務"""
    print("🧪 測試編譯功能與已完成任務處理")
    print("=" * 60)
    
    # 創建模擬的已完成任務
    completed_job_ids = [
        'jpr2wo405',  # face_detection_full_range.onnx
        'jgnmko9kp',  # face_detection_short_range.onnx  
        'j5m68owdg',  # iris_landmark.onnx
        'jpx6x373p',  # hand_recrop.onnx
        'jp4d3mx8p'   # hand_landmark.onnx
    ]
    
    # 創建模擬的 QAI Hub 模型資料
    mock_models = {}
    for job_id in completed_job_ids:
        model_name = f"model_{job_id}"
        mock_job = create_mock_job(job_id, "Results Ready")
        
        mock_models[model_name] = {
            'loaded': True,
            'compile_job': mock_job,
            'compile_job_id': job_id
        }
    
    # 創建 QAIHubClient 實例
    qaihub_client = QAIHubClient()
    
    # 使用 patch 來模擬 qai_hub_models
    with patch.object(qaihub_client, 'qai_hub_models', mock_models):
        # 創建 JobMonitor
        job_monitor = QAIHubJobMonitor(qaihub_client)
        
        # 添加所有已完成任務到監控器
        for job_id in completed_job_ids:
            model_name = f"model_{job_id}"
            job_monitor.add_job(job_id, 'compile', model_name, timeout=300)
        
        print("✅ 已添加所有已完成任務到監控器")
        
        # 測試等待完成功能（應該立即完成）
        print("\n⏳ 測試 wait_for_compile_jobs (應該立即完成):")
        start_time = time.time()
        
        # 使用較短的超時時間進行測試
        result = job_monitor.wait_for_compile_jobs(mock_models, timeout_minutes=1)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        print(f"等待完成耗時: {elapsed_time:.2f} 秒")
        print(f"等待完成結果: {result}")
        
        # 檢查是否所有任務都被正確識別為已完成
        all_completed = True
        for job in job_monitor.get_all_jobs().values():
            status_upper = str(job['status']).upper()
            completed_upper = [s.upper() for s in job_monitor.COMPLETED_STATUS]
            
            if status_upper not in completed_upper:
                all_completed = False
                print(f"❌ 任務 {job['job_id']} 狀態: {job['status']} 未被識別為完成")
        
        print(f"\n所有任務完成檢查: {all_completed}")
        
        # 檢查是否在合理時間內完成（不應該卡住）
        # 正常情況下應該在幾秒內完成，如果超過10秒可能表示有問題
        time_acceptable = elapsed_time < 10.0
        print(f"完成時間檢查 (<10秒): {time_acceptable}")
        
        return result and all_completed and time_acceptable

def test_job_monitor_with_realistic_scenario():
    """測試更真實的場景"""
    print("\n🧪 測試真實場景模擬:")
    print("=" * 40)
    
    # 創建混合狀態的任務
    mixed_job_ids = [
        ('jpr2wo405', 'Results Ready'),      # 已完成
        ('jgnmko9kp', 'RUNNING'),            # 進行中
        ('j5m68owdg', 'Results Ready'),      # 已完成
        ('jpx6x373p', 'QUEUED'),             # 排隊中
        ('jp4d3mx8p', 'Results Ready')       # 已完成
    ]
    
    # 創建模擬的 QAI Hub 模型資料
    mock_models = {}
    for job_id, status in mixed_job_ids:
        model_name = f"model_{job_id}"
        mock_job = create_mock_job(job_id, status)
        
        mock_models[model_name] = {
            'loaded': True,
            'compile_job': mock_job,
            'compile_job_id': job_id
        }
    
    # 創建 QAIHubClient 實例
    qaihub_client = QAIHubClient()
    
    with patch.object(qaihub_client, 'qai_hub_models', mock_models):
        job_monitor = QAIHubJobMonitor(qaihub_client)
        
        # 添加所有任務到監控器
        for job_id, status in mixed_job_ids:
            model_name = f"model_{job_id}"
            job_monitor.add_job(job_id, 'compile', model_name, timeout=60)  # 1分鐘超時
        
        print("✅ 已添加混合狀態任務到監控器")
        
        # 模擬狀態更新（模擬 QAI Hub 狀態變化）
        def simulate_status_updates():
            """模擬狀態更新"""
            time.sleep(2)  # 等待2秒後更新狀態
            
            # 更新進行中和排隊中的任務為已完成
            for job_id, original_status in mixed_job_ids:
                if original_status in ['RUNNING', 'QUEUED']:
                    # 找到對應的 job 並更新狀態
                    for model_name, model_info in mock_models.items():
                        if model_info['compile_job_id'] == job_id:
                            model_info['compile_job'].status = 'Results Ready'
                            break
        
        # 啟動狀態更新模擬（在背景執行）
        import threading
        update_thread = threading.Thread(target=simulate_status_updates, daemon=True)
        update_thread.start()
        
        # 測試等待完成功能
        print("\n⏳ 測試混合狀態任務的等待完成:")
        start_time = time.time()
        result = job_monitor.wait_for_compile_jobs(mock_models, timeout_minutes=1)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        print(f"等待完成耗時: {elapsed_time:.2f} 秒")
        print(f"等待完成結果: {result}")
        
        # 檢查最終狀態
        completed_count = 0
        for job in job_monitor.get_all_jobs().values():
            status_upper = str(job['status']).upper()
            completed_upper = [s.upper() for s in job_monitor.COMPLETED_STATUS]
            
            if status_upper in completed_upper:
                completed_count += 1
                print(f"✅ 任務 {job['job_id']}: {job['status']}")
            else:
                print(f"❌ 任務 {job['job_id']}: {job['status']} (未完成)")
        
        print(f"\n完成任務數量: {completed_count}/{len(mixed_job_ids)}")
        
        return result and (completed_count == len(mixed_job_ids))

def main():
    """主測試函數"""
    print("🚀 開始編譯功能與已完成任務處理測試")
    print("=" * 60)
    
    try:
        # 測試已完成任務的處理
        test1_passed = test_compile_with_completed_jobs()
        
        # 測試混合狀態場景
        test2_passed = test_job_monitor_with_realistic_scenario()
        
        print("\n" + "=" * 60)
        print("🎯 測試結果總結:")
        print("-" * 20)
        print(f"已完成任務處理測試: {'✅ 通過' if test1_passed else '❌ 失敗'}")
        print(f"混合狀態場景測試: {'✅ 通過' if test2_passed else '❌ 失敗'}")
        
        overall_result = test1_passed and test2_passed
        print(f"\n總體結果: {'✅ 所有測試通過!' if overall_result else '❌ 有測試失敗!'}")
        
        if overall_result:
            print("\n🎉 編譯功能已正確處理 'Results Ready' 狀態!")
            print("   編譯函數應該不再會因為狀態識別問題而卡住。")
        else:
            print("\n⚠️  需要進一步檢查編譯功能的狀態處理邏輯。")
            
        return overall_result
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
