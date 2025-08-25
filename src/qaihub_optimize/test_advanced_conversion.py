#!/usr/bin/env python3
"""
測試進階轉換功能
"""
import sys
from pathlib import Path

# 添加模組路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.advanced_conversion import AdvancedModelConverter

def test_single_conversion():
    """測試單個模型轉換"""
    print("🧪 測試單個模型轉換...")
    
    converter = AdvancedModelConverter()
    
    # 測試檔案路徑
    test_tflite = Path("/Users/andycyw/mvp_fall_detection_starter/src/models/raw/face_detector.tflite")
    test_output = Path("/Users/andycyw/mvp_fall_detection_starter/src/models/onnx_test")
    
    if not test_tflite.exists():
        print(f"❌ 測試檔案不存在: {test_tflite}")
        return False
    
    # 確保輸出目錄存在
    test_output.mkdir(exist_ok=True)
    
    print(f"📁 輸入檔案: {test_tflite}")
    print(f"📁 輸出目錄: {test_output}")
    
    # 測試模型檢查
    print("\n🔍 測試模型檢查...")
    check_result = converter.check_tflite_model(test_tflite)
    print(f"檢查結果: {check_result['status']} - {check_result['message']}")
    
    # 測試轉換
    print("\n🔄 測試轉換...")
    result = converter.convert_tflite_to_onnx_fixed(test_tflite, test_output)
    
    print(f"轉換結果: {result['status']}")
    print(f"訊息: {result['message']}")
    
    if result["status"] == "ok":
        print(f"✅ 轉換成功! ONNX 檔案: {result['onnx_path']}")
        return True
    else:
        print(f"❌ 轉換失敗: {result['message']}")
        return False

def test_batch_conversion():
    """測試批次轉換"""
    print("\n🧪 測試批次轉換...")
    
    converter = AdvancedModelConverter()
    
    # 獲取所有 TFLite 檔案
    models_dir = Path("/Users/andycyw/mvp_fall_detection_starter/src/models")
    raw_dir = models_dir / "raw"
    output_dir = models_dir / "onnx_test"
    
    if not raw_dir.exists():
        print(f"❌ raw 目錄不存在: {raw_dir}")
        return False
    
    # 獲取所有 TFLite 檔案
    tflite_files = list(raw_dir.glob("*.tflite"))
    
    if not tflite_files:
        print("❌ 沒有找到 TFLite 檔案")
        return False
    
    print(f"📁 找到 {len(tflite_files)} 個 TFLite 檔案:")
    for file in tflite_files:
        print(f"  - {file.name}")
    
    # 確保輸出目錄存在
    output_dir.mkdir(exist_ok=True)
    
    # 執行批次轉換
    results, failed_files = converter.batch_convert_with_fallback(tflite_files, output_dir)
    
    # 生成報告
    report = converter.generate_conversion_report(results, failed_files)
    print(f"\n{report}")
    
    return len(failed_files) == 0

def test_error_analysis():
    """測試錯誤分析功能"""
    print("\n🧪 測試錯誤分析...")
    
    converter = AdvancedModelConverter()
    
    # 測試各種錯誤訊息的分析
    test_errors = [
        "Data type float16 not supported/tested yet",
        "Unsupported TFLite OP: 124 DENSIFY!",
        "IndexError: list index out of range",
        "TypeError: object of type 'int' has no len()",
        "unrecognized arguments: --tflite --onnx",
        "Some other random error message"
    ]
    
    for error in test_errors:
        analysis = converter.analyze_conversion_error(error, "test_model.tflite")
        print(f"錯誤: {error[:50]}...")
        print(f"分析: {analysis}")
        print("-" * 80)

if __name__ == "__main__":
    print("🚀 開始測試進階轉換功能")
    print("=" * 60)
    
    # 測試錯誤分析
    test_error_analysis()
    
    # 測試單個轉換
    success1 = test_single_conversion()
    
    # 測試批次轉換
    success2 = test_batch_conversion()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ 所有測試通過!")
    else:
        print("❌ 部分測試失敗!")
    
    print("測試完成!")
