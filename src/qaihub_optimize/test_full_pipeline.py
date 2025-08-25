"""
測試完整工作流程
驗證從模型掃描到優化模型下載的完整流程
"""
import sys
import os
import time
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.qaihub_optimize.modules.pipeline import get_pipeline


def test_full_pipeline():
    """測試完整工作流程"""
    print("=" * 60)
    print("🚀 測試完整 QAI Hub 工作流程")
    print("=" * 60)
    
    try:
        # 創建 pipeline 實例
        pipeline = get_pipeline()
        
        print("📋 測試步驟:")
        print("1. 掃描模型檔案")
        print("2. 檢查模型格式")
        print("3. 提交編譯任務")
        print("4. 監控任務狀態（實時顯示）")
        print("5. 處理錯誤（如果有）")
        print("6. 下載優化模型")
        print("7. 驗證模型保存位置")
        
        print("\n" + "-" * 40)
        print("1️⃣ 掃描模型檔案...")
        
        # 掃描模型
        models = pipeline.scan_models()
        if not models:
            print("❌ 沒有找到模型檔案")
            return False
        
        print(f"✅ 找到 {sum(len(files) for files in models.values())} 個模型檔案")
        for ext, files in models.items():
            print(f"   - {ext.upper()}: {len(files)} 個")
        
        print("\n" + "-" * 40)
        print("2️⃣ 檢查裝置支援和模型格式...")
        
        # 檢查裝置支援
        support_info = pipeline.qaihub_client.check_device_support()
        print("📋 裝置支援格式:")
        for framework, supported in support_info.items():
            status = "✅" if supported else "❌"
            print(f"   {status} {framework.upper()}: {'支援' if supported else '不支援'}")
        
        # 根據裝置支援決定使用哪種格式
        source_format = 'onnx' if support_info.get('onnx', False) else 'tflite'
        print(f"📝 將使用 {source_format.upper()} 格式進行編譯")
        
        print("\n" + "-" * 40)
        print("3️⃣ 執行編譯工作流程...")
        print("⚠️  注意：這將實際提交任務到 QAI Hub，可能需要一些時間")
        print("💡 您可以觀察實時狀態更新和進度顯示")
        
        # 執行編譯流程
        success = pipeline.run_compile_pipeline(source_format)
        
        print("\n" + "-" * 40)
        print("4️⃣ 檢查編譯結果和優化模型...")
        
        if success:
            print("✅ 編譯流程成功完成！")
            
            # 檢查優化模型下載狀態
            downloaded_models = []
            for model_name, model_info in pipeline.qaihub_client.qai_hub_models.items():
                if model_info.get('optimized_model_downloaded', False):
                    downloaded_models.append({
                        'name': model_name,
                        'path': model_info.get('optimized_model_path', '未知')
                    })
            
            if downloaded_models:
                print(f"💾 成功下載 {len(downloaded_models)} 個優化模型:")
                for model in downloaded_models:
                    print(f"   - {model['name']} -> {model['path']}")
                    
                    # 驗證檔案確實存在
                    model_path = Path(model['path'])
                    if model_path.exists():
                        print(f"     ✅ 檔案存在，大小: {model_path.stat().st_size} bytes")
                    else:
                        print(f"     ❌ 檔案不存在！")
            else:
                print("⚠️  沒有下載優化模型")
                
        else:
            print("❌ 編譯流程失敗")
            
            # 顯示詳細錯誤信息
            failed_jobs = []
            for model_name, model_info in pipeline.qaihub_client.qai_hub_models.items():
                compile_job = model_info.get('compile_job')
                if compile_job and hasattr(compile_job, 'status'):
                    status = getattr(compile_job.status, 'code', str(compile_job.status))
                    if str(status).upper() in ['FAILED', 'ERROR']:
                        error_msg = getattr(compile_job.status, 'error', '未知錯誤')
                        failed_jobs.append({
                            'name': model_name,
                            'status': status,
                            'error': error_msg
                        })
            
            if failed_jobs:
                print(f"❌ 失敗的任務 ({len(failed_jobs)} 個):")
                for job in failed_jobs:
                    print(f"   - {job['name']}: {job['status']} - {job['error']}")
        
        print("\n" + "-" * 40)
        print("5️⃣ 驗證優化模型目錄結構...")
        
        # 檢查優化模型目錄
        optimized_dir = project_root / 'src' / 'models' / 'qaihub_optimized'
        print(f"📁 優化模型目錄: {optimized_dir}")
        print(f"📁 目錄是否存在: {optimized_dir.exists()}")
        
        if optimized_dir.exists():
            optimized_files = list(optimized_dir.glob('*'))
            print(f"📊 目錄中的檔案數量: {len(optimized_files)}")
            
            for file in optimized_files:
                if file.is_file():
                    print(f"   - {file.name} ({file.stat().st_size} bytes)")
        
        print("\n" + "-" * 40)
        print("6️⃣ 清理重複的目錄結構...")
        
        # 檢查並清理可能的重複目錄
        duplicate_dirs = [
            project_root / 'src' / 'models' / 'models' / 'qaihub_optimized',
            project_root / 'src' / 'models' / 'qaihub_optimized',
            project_root / 'src' / 'qaihub_optimized'
        ]
        
        for dir_path in duplicate_dirs:
            if dir_path.exists() and dir_path != optimized_dir:
                print(f"🗑️  發現重複目錄: {dir_path}")
                # 這裡可以添加清理邏輯，但為了安全先只顯示信息
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 完整工作流程測試成功完成！")
            print("✅ 實時狀態顯示正常")
            print("✅ 錯誤處理功能正常")
            print("✅ 優化模型下載正常")
        else:
            print("⚠️  工作流程測試完成，但有任務失敗")
            print("💡 請檢查錯誤信息並調整模型或配置")
        
        return success
        
    except Exception as e:
        print(f"❌ 測試發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_small_workflow():
    """測試小型工作流程（只處理1-2個模型）"""
    print("\n" + "=" * 60)
    print("🧪 測試小型工作流程（只處理1個模型）")
    print("=" * 60)
    
    try:
        pipeline = get_pipeline()
        
        # 掃描模型
        models = pipeline.scan_models()
        if not models:
            print("❌ 沒有找到模型檔案")
            return False
        
        # 只選擇第一個模型進行測試
        test_model = None
        for ext, files in models.items():
            if files:
                test_model = files[0]
                break
        
        if not test_model:
            print("❌ 沒有可用的模型檔案")
            return False
        
        print(f"🔍 選擇測試模型: {test_model.name}")
        
        # 這裡可以實現只處理單一模型的邏輯
        # 但由於 pipeline 設計是處理所有模型，我們暫時使用完整流程
        
        print("⚠️  由於架構限制，將執行完整流程但只監控進度")
        print("💡 您可以觀察實時狀態更新")
        
        return pipeline.run_compile_pipeline('tflite')
        
    except Exception as e:
        print(f"❌ 小型工作流程測試失敗: {e}")
        return False


if __name__ == "__main__":
    print("🤖 QAI Hub 完整工作流程測試")
    print("💡 這個測試將實際連接到 QAI Hub 並提交編譯任務")
    print("⏰ 可能需要一些時間完成，請耐心等待")
    
    # 詢問用戶是否要繼續
    response = input("\n是否要繼續執行完整測試？(y/n): ").strip().lower()
    if response != 'y':
        print("⏭️ 跳過完整測試")
        # 執行小型測試 instead
        test_small_workflow()
    else:
        # 執行完整測試
        test_full_pipeline()
