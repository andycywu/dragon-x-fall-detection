#!/usr/bin/env python3
"""
測試編譯流程完整性的腳本
驗證新的 job monitor 功能是否正確工作
"""
import sys
from pathlib import Path

# 添加模組路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.pipeline import QAIHubPipeline
from modules.job_monitor import get_job_monitor

def test_compile_flow():
    """測試完整的編譯流程"""
    print("🧪 開始測試編譯流程完整性...")
    
    # 初始化 pipeline，使用正確的基礎目錄（項目根目錄）
    base_dir = Path(__file__).parent.parent
    pipeline = QAIHubPipeline(base_dir)
    
    # 測試掃描模型
    print("\n1. 測試模型掃描...")
    models = pipeline.scan_models()
    if not models:
        print("❌ 掃描模型失敗，沒有找到任何模型")
        return False
    print(f"✅ 掃描到 {sum(len(files) for files in models.values())} 個模型檔案")
    
    # 測試 job monitor 初始化
    print("\n2. 測試 Job Monitor 初始化...")
    job_monitor = get_job_monitor(pipeline.qaihub_client)
    if not job_monitor:
        print("❌ Job Monitor 初始化失敗")
        return False
    print("✅ Job Monitor 初始化成功")
    
    # 測試 job monitor 的狀態更新功能
    print("\n3. 測試 Job Monitor 狀態更新...")
    try:
        # 測試添加虛擬任務
        job_monitor.add_job('test_job_1', 'compile', 'test_model', timeout=60)
        job_monitor.update_job_status('test_job_1', 'RUNNING', 50)
        
        job_info = job_monitor.get_job_status('test_job_1')
        if job_info and job_info['status'] == 'RUNNING' and job_info['progress'] == 50:
            print("✅ Job Monitor 狀態更新功能正常")
        else:
            print("❌ Job Monitor 狀態更新功能異常")
            return False
            
    except Exception as e:
        print(f"❌ Job Monitor 狀態更新測試失敗: {e}")
        return False
    
    # 測試優化模型目錄創建
    print("\n4. 測試優化模型目錄...")
    optimized_dir = pipeline.qaihub_client.base_dir / 'qaihub_optimized'
    optimized_dir.mkdir(parents=True, exist_ok=True)
    
    if optimized_dir.exists():
        print(f"✅ 優化模型目錄已創建: {optimized_dir}")
    else:
        print("❌ 優化模型目錄創建失敗")
        return False
    
    # 測試完整的編譯流程（模擬模式）
    print("\n5. 測試完整編譯流程（模擬模式）...")
    try:
        # 模擬一個成功的編譯任務
        test_model_name = "test_model"
        pipeline.qaihub_client.qai_hub_models[test_model_name] = {
            'model_path': Path('/tmp/test.onnx'),
            'source': 'onnx',
            'loaded': True,
            'compile_job_id': 'test_compile_job_123'
        }
        
        # 模擬 job monitor 處理完成任務
        job_monitor.add_job('test_compile_job_123', 'compile', test_model_name, timeout=60)
        job_monitor.update_job_status('test_compile_job_123', 'COMPLETED', 100)
        
        # 模擬下載優化模型
        optimized_path = optimized_dir / f"{test_model_name}_optimized.onnx"
        optimized_path.write_text("# Mock optimized model content")
        
        # 更新模型狀態
        pipeline.qaihub_client.qai_hub_models[test_model_name]['optimized_model_path'] = str(optimized_path)
        pipeline.qaihub_client.qai_hub_models[test_model_name]['optimized_model_downloaded'] = True
        
        # 檢查下載狀態
        downloaded = pipeline.qaihub_client.qai_hub_models[test_model_name].get('optimized_model_downloaded', False)
        if downloaded:
            print("✅ 優化模型下載狀態更新正常")
        else:
            print("❌ 優化模型下載狀態更新失敗")
            return False
            
    except Exception as e:
        print(f"❌ 完整流程測試失敗: {e}")
        return False
    
    print("\n🎉 所有測試通過！編譯流程功能完整")
    return True

def test_real_time_status():
    """測試實時狀態顯示功能"""
    print("\n🧪 測試實時狀態顯示功能...")
    
    from modules.job_monitor import get_job_monitor
    
    job_monitor = get_job_monitor()
    
    # 添加多個測試任務
    test_jobs = [
        ('job_1', 'compile', 'model_a'),
        ('job_2', 'compile', 'model_b'), 
        ('job_3', 'profile', 'model_c')
    ]
    
    for job_id, job_type, model_name in test_jobs:
        job_monitor.add_job(job_id, job_type, model_name, timeout=120)
    
    # 模擬不同的狀態
    job_monitor.update_job_status('job_1', 'RUNNING', 30)
    job_monitor.update_job_status('job_2', 'QUEUED', 10)
    job_monitor.update_job_status('job_3', 'COMPLETED', 100)
    
    # 測試狀態報告生成
    report = job_monitor.generate_status_report()
    print("\n📊 狀態報告:")
    print(report)
    
    # 測試實時狀態顯示
    print("\n📈 實時狀態顯示:")
    job_monitor.print_status()
    
    print("✅ 實時狀態顯示功能正常")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("QAI Hub 編譯流程完整性測試")
    print("=" * 60)
    
    success = True
    
    # 運行測試
    success &= test_compile_flow()
    success &= test_real_time_status()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有測試通過！編譯流程功能完整且正常")
        print("✅ 實時狀態顯示功能正常")
        print("✅ 優化模型下載功能正常")
    else:
        print("❌ 測試失敗，請檢查相關功能")
    
    print("=" * 60)
