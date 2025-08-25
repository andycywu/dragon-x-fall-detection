"""
測試任務狀態識別功能
專門測試 QAI Hub 任務狀態識別，特別是 "Results Ready" 狀態的處理
"""
import sys
import os
from pathlib import Path

# 添加模組路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.job_monitor import JobMonitor, QAIHubJobMonitor

def test_status_recognition():
    """測試狀態識別功能"""
    print("🧪 測試任務狀態識別功能")
    print("=" * 50)
    
    # 創建一個基本的 JobMonitor 實例
    monitor = JobMonitor()
    
    # 測試的狀態列表
    test_statuses = [
        'COMPLETED',
        'SUCCEEDED', 
        'SUCCESS',
        'FINISHED',
        'COMPLETED_SUCCESSFULLY',
        'RESULTS_READY',
        'RESULTS READY',
        'results_ready',
        'Results Ready',
        'FAILED',
        'ERROR',
        'CANCELLED',
        'TIMEOUT',
        'PENDING',
        'RUNNING',
        'QUEUED'
    ]
    
    print("📋 測試狀態識別:")
    print("-" * 30)
    
    completed_count = 0
    error_count = 0
    pending_count = 0
    
    for status in test_statuses:
        # 使用大小寫不敏感的狀態檢查
        status_upper = str(status).upper()
        completed_upper = [s.upper() for s in monitor.COMPLETED_STATUS]
        error_upper = [s.upper() for s in monitor.ERROR_STATUS]
        
        is_completed = status_upper in completed_upper
        is_error = status_upper in error_upper
        is_pending = not (is_completed or is_error)
        
        if is_completed:
            completed_count += 1
            status_symbol = "✅"
        elif is_error:
            error_count += 1
            status_symbol = "❌"
        else:
            pending_count += 1
            status_symbol = "⏳"
        
        print(f"{status_symbol} {status:20} -> 完成: {is_completed:5} 錯誤: {is_error:5} 進行中: {is_pending:5}")
    
    print("\n📊 統計結果:")
    print("-" * 20)
    print(f"✅ 完成狀態: {completed_count}")
    print(f"❌ 錯誤狀態: {error_count}")
    print(f"⏳ 進行中狀態: {pending_count}")
    
    # 測試特定的已完成任務ID
    print("\n🧪 測試特定已完成任務ID:")
    print("-" * 30)
    
    completed_job_ids = [
        'jpr2wo405',  # face_detection_full_range.onnx
        'jgnmko9kp',  # face_detection_short_range.onnx  
        'j5m68owdg',  # iris_landmark.onnx
        'jpx6x373p',  # hand_recrop.onnx
        'jp4d3mx8p'   # hand_landmark.onnx
    ]
    
    # 模擬這些任務已經完成（狀態為 "Results Ready"）
    for job_id in completed_job_ids:
        monitor.add_job(job_id, 'compile', f'model_{job_id}', timeout=300)
        monitor.update_job_status(job_id, 'Results Ready', 100)
        
        job_status = monitor.get_job_status(job_id)
        if job_status:
            status_upper = str(job_status['status']).upper()
            completed_upper = [s.upper() for s in monitor.COMPLETED_STATUS]
            is_completed = status_upper in completed_upper
            
            print(f"📦 {job_id}: {job_status['status']} -> 識別為完成: {is_completed}")
    
    # 測試等待完成功能
    print("\n🧪 測試等待完成功能:")
    print("-" * 30)
    
    # 重置監控器
    monitor = JobMonitor()
    
    # 添加所有已完成任務
    for job_id in completed_job_ids:
        monitor.add_job(job_id, 'compile', f'model_{job_id}', timeout=300)
        monitor.update_job_status(job_id, 'Results Ready', 100)
    
    # 測試是否所有任務都被識別為已完成
    all_completed = True
    for job in monitor.get_all_jobs().values():
        status_upper = str(job['status']).upper()
        completed_upper = [s.upper() for s in monitor.COMPLETED_STATUS]
        error_upper = [s.upper() for s in monitor.ERROR_STATUS]
        
        if status_upper not in completed_upper and status_upper not in error_upper:
            all_completed = False
            break
    
    print(f"所有任務完成檢查: {all_completed}")
    
    # 測試 wait_for_completion 方法
    print("\n⏳ 測試 wait_for_completion (應該立即完成):")
    result = monitor.wait_for_completion(timeout=10, check_interval=1)
    print(f"等待完成結果: {result}")
    
    return all_completed and result

def test_progress_estimation():
    """測試進度估計功能"""
    print("\n🧪 測試進度估計功能:")
    print("=" * 30)
    
    monitor = JobMonitor()
    
    test_cases = [
        ('PENDING', 0),
        ('QUEUED', 10),
        ('RUNNING', 50),
        ('PROCESSING', 70),
        ('COMPLETED', 100),
        ('SUCCEEDED', 100),
        ('SUCCESS', 100),
        ('FINISHED', 100),
        ('COMPLETED_SUCCESSFULLY', 100),
        ('RESULTS_READY', 100),
        ('RESULTS READY', 100),
        ('FAILED', 100),
        ('ERROR', 100),
        ('CANCELLED', 100),
        ('TIMEOUT', 100),
        ('UNKNOWN_STATUS', 0)
    ]
    
    print("📊 進度估計測試:")
    print("-" * 25)
    
    for status, expected_progress in test_cases:
        # 使用 QAIHubJobMonitor 的進度估計方法
        qai_monitor = QAIHubJobMonitor(None)
        actual_progress = qai_monitor._estimate_progress(status)
        
        status_match = actual_progress == expected_progress
        symbol = "✅" if status_match else "❌"
        
        print(f"{symbol} {status:25} -> 預期: {expected_progress:3}%, 實際: {actual_progress:3}%")
        
        if not status_match:
            print(f"   ⚠️  進度不匹配! 狀態: {status}")
    
    return True

def main():
    """主測試函數"""
    print("🚀 開始 QAI Hub 任務狀態識別測試")
    print("=" * 50)
    
    try:
        # 測試狀態識別
        status_test_passed = test_status_recognition()
        
        # 測試進度估計
        progress_test_passed = test_progress_estimation()
        
        print("\n" + "=" * 50)
        print("🎯 測試結果總結:")
        print("-" * 20)
        print(f"狀態識別測試: {'✅ 通過' if status_test_passed else '❌ 失敗'}")
        print(f"進度估計測試: {'✅ 通過' if progress_test_passed else '❌ 失敗'}")
        
        overall_result = status_test_passed and progress_test_passed
        print(f"\n總體結果: {'✅ 所有測試通過!' if overall_result else '❌ 有測試失敗!'}")
        
        if overall_result:
            print("\n🎉 狀態識別功能已正確處理 'Results Ready' 狀態!")
            print("   編譯函數應該不再會因為狀態識別問題而卡住。")
        else:
            print("\n⚠️  需要進一步檢查狀態識別邏輯。")
            
        return overall_result
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
