#!/usr/bin/env python3
"""
修復 TFLite 到 ONNX 轉換問題的主要腳本
"""
import sys
from pathlib import Path

# 添加模組路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.advanced_conversion import AdvancedModelConverter
from modules.preprocessor import get_model_preprocessor

def fix_conversion_issues():
    """修復轉換問題的主要函數"""
    print("🔧 開始修復 TFLite 到 ONNX 轉換問題")
    print("=" * 60)
    
    # 初始化轉換器
    converter = AdvancedModelConverter()
    preprocessor = get_model_preprocessor()
    
    # 檢查模型目錄
    models_dir = Path("/Users/andycyw/mvp_fall_detection_starter/src/models")
    raw_dir = models_dir / "raw"
    onnx_dir = models_dir / "onnx"
    
    if not raw_dir.exists():
        print(f"❌ raw 目錄不存在: {raw_dir}")
        return False
    
    if not onnx_dir.exists():
        print(f"📁 建立 onnx 目錄: {onnx_dir}")
        onnx_dir.mkdir(parents=True, exist_ok=True)
    
    # 獲取所有 TFLite 檔案
    tflite_files = list(raw_dir.glob("*.tflite"))
    
    if not tflite_files:
        print("❌ 沒有找到 TFLite 檔案")
        return False
    
    print(f"📁 找到 {len(tflite_files)} 個 TFLite 檔案:")
    for file in tflite_files:
        print(f"  - {file.name}")
    
    print("\n🔍 分析轉換問題...")
    
    # 檢查每個模型的轉換問題
    conversion_issues = []
    for tflite_path in tflite_files:
        print(f"\n📋 分析 {tflite_path.name}:")
        
        # 檢查模型
        check_result = converter.check_tflite_model(tflite_path)
        print(f"  檢查: {check_result['status']} - {check_result['message']}")
        
        # 檢查是否已經有 ONNX 檔案
        onnx_path = onnx_dir / f"{tflite_path.stem}.onnx"
        if onnx_path.exists():
            print(f"  ✅ ONNX 檔案已存在: {onnx_path.name}")
            continue
        
        # 嘗試轉換來識別問題
        test_result = converter.convert_tflite_to_onnx_fixed(tflite_path, onnx_dir)
        
        if test_result["status"] == "error":
            print(f"  ❌ 轉換問題: {test_result['message']}")
            conversion_issues.append({
                "file": tflite_path.name,
                "issue": test_result["message"],
                "stderr": test_result.get("stderr", "")
            })
        else:
            print(f"  ✅ 轉換成功或警告: {test_result['message']}")
    
    # 顯示問題報告
    if conversion_issues:
        print(f"\n⚠️  發現 {len(conversion_issues)} 個轉換問題:")
        for i, issue in enumerate(conversion_issues, 1):
            print(f"\n{i}. {issue['file']}:")
            print(f"   問題: {issue['issue']}")
            if issue['stderr']:
                print(f"   詳細錯誤: {issue['stderr'][:100]}...")
    else:
        print(f"\n✅ 沒有發現轉換問題!")
    
    # 提供解決方案建議
    print(f"\n💡 解決方案建議:")
    print("1. 對於 float16 問題: 使用 TensorFlow 將模型轉換為 float32 格式")
    print("2. 對於 DENSIFY 操作問題: 使用 tf2onnx 或其他轉換工具")
    print("3. 對於參數錯誤: 確保使用正確的 tflite2onnx 命令格式")
    print("4. 考慮使用預先轉換好的 ONNX 模型")
    
    return len(conversion_issues) == 0

def create_workaround_solution():
    """創建替代解決方案"""
    print(f"\n🛠️ 創建替代解決方案...")
    
    # 建立一個說明文件
    solution_file = Path(__file__).parent / "CONVERSION_SOLUTIONS.md"
    
    content = """# TFLite 到 ONNX 轉換問題解決方案

## 常見問題及解決方法

### 1. float16 資料類型不支援
**問題**: `Data type float16 not supported/tested yet`

**解決方案**:
- 使用 TensorFlow 將模型轉換為 float32 格式
- 在匯出 TFLite 時指定資料類型:
  ```python
  converter.optimizations = [tf.lite.Optimize.DEFAULT]
  converter.target_spec.supported_types = [tf.float32]
  ```

### 2. DENSIFY 操作不支援
**問題**: `Unsupported TFLite OP: 124 DENSIFY!`

**解決方案**:
- 使用 tf2onnx 工具進行轉換
- 在模型訓練時避免使用會產生 DENSIFY 操作的方法
- 使用預先轉換好的模型

### 3. 參數格式錯誤
**問題**: `unrecognized arguments: --tflite --onnx`

**解決方案**:
- 使用正確的命令格式: `tflite2onnx input.tflite output.onnx`
- 不要使用 `--tflite` 和 `--onnx` 參數

### 4. 其他轉換錯誤
**問題**: 各種索引錯誤、類型錯誤等

**解決方案**:
- 更新 tflite2onnx 到最新版本
- 嘗試不同的 tflite2onnx 版本
- 使用 ONNX Runtime 的 TFLite 支援

## 替代轉換方法

### 使用 tf2onnx
```bash
# 首先將 TFLite 轉換為 SavedModel
# 然後使用 tf2onnx
python -m tf2onnx.convert --saved-model saved_model_dir --output model.onnx
```

### 使用 ONNX Runtime
```python
import onnxruntime as ort

# ONNX Runtime 可以直接執行 TFLite 模型
# 不需要轉換
```

## 預先轉換的模型

如果轉換仍然失敗，可以考慮:
1. 使用預先轉換好的 ONNX 模型
2. 重新訓練模型並直接匯出為 ONNX 格式
3. 使用支援的模型架構

## 聯絡支援

如果問題持續存在，請:
1. 提供完整的錯誤訊息
2. 提供模型資訊
3. 提供使用的工具版本
"""
    
    with open(solution_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已建立解決方案文件: {solution_file}")
    return solution_file

if __name__ == "__main__":
    print("🚀 TFLite 到 ONNX 轉換問題修復工具")
    print("=" * 60)
    
    # 修復轉換問題
    success = fix_conversion_issues()
    
    # 創建解決方案文件
    solution_file = create_workaround_solution()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 轉換問題修復完成!")
    else:
        print("⚠️  發現轉換問題，請查看上面的解決方案建議")
    
    print(f"📋 詳細解決方案請參考: {solution_file}")
    print("\n💡 提示: 您可以執行以下命令測試轉換:")
    print("  python src/qaihub_optimize/test_advanced_conversion.py")
