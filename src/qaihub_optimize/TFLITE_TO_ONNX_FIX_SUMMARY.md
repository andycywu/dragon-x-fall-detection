# TFLite 到 ONNX 轉換問題解決總結

## 問題分析

從錯誤日誌分析，主要遇到以下轉換問題：

### 1. float16 資料類型不支援 (主要問題)
**受影響模型**:
- hand_detector.tflite
- pose_landmarks_detector.tflite  
- face_landmarks_detector.tflite
- pose_detector.tflite

**錯誤訊息**: `Data type float16 not supported/tested yet`

### 2. 類型錯誤和操作不支援
**受影響模型**:
- face_blendshapes.tflite (類型錯誤)
- 某些模型可能包含 DENSIFY 操作

### 3. 參數格式錯誤
**問題**: 使用了錯誤的參數格式 `--tflite --onnx`

## 已實施的解決方案

### 1. 創建進階轉換模組 (`advanced_conversion.py`)
- ✅ 修復參數傳遞錯誤
- ✅ 添加友好的錯誤訊息分析
- ✅ 提供詳細的錯誤診斷
- ✅ 支援批次轉換和報告生成

### 2. 更新預處理器 (`preprocessor.py`)
- ✅ 整合新的進階轉換器
- ✅ 改進錯誤處理和狀態回報
- ✅ 支援警告狀態處理

### 3. 提供完整的解決方案文件
- ✅ `CONVERSION_SOLUTIONS.md` - 詳細的解決方案指南
- ✅ `fix_conversion_issues.py` - 自動問題診斷工具
- ✅ `test_advanced_conversion.py` - 測試驗證工具

## 當前轉換狀態

### 成功轉換的模型 (2個)
- ✅ hand_landmarks_detector.tflite → hand_landmarks_detector.onnx
- ✅ face_detector.tflite → face_detector.onnx

### 需要進一步處理的模型 (5個)
- ❌ hand_detector.tflite (float16 問題)
- ❌ face_blendshapes.tflite (類型錯誤)
- ❌ pose_landmarks_detector.tflite (float16 問題)
- ❌ face_landmarks_detector.tflite (float16 問題)
- ❌ pose_detector.tflite (float16 問題)

## 推薦的下一步行動

### 短期解決方案 (立即實施)
1. **使用預先轉換的 ONNX 模型**
   - 對於無法轉換的模型，尋找預先轉換好的版本
   - 檢查現有的 onnx 目錄中是否有可用的模型

2. **模型替代**
   - 考慮使用其他支援的模型架構
   - 使用已經成功轉換的模型

### 中期解決方案 (建議實施)
1. **模型重新訓練和匯出**
   - 使用 TensorFlow 將問題模型重新匯出為 float32 格式
   - 避免使用會產生 DENSIFY 操作的方法

2. **使用替代轉換工具**
   - 嘗試 tf2onnx 工具
   - 使用 ONNX Runtime 的 TFLite 直接支援

### 長期解決方案 (架構優化)
1. **統一模型格式**
   - 標準化使用 ONNX 格式
   - 建立模型轉換流水線

2. **版本相容性管理**
   - 固定工具版本
   - 建立測試套件確保轉換相容性

## 技術細節

### 已修復的問題
- **參數格式錯誤**: 從 `tflite2onnx --tflite input.tflite --onnx output.onnx` 改為正確的 `tflite2onnx input.tflite output.onnx`
- **錯誤處理**: 提供詳細的錯誤分析和友好的錯誤訊息
- **模型檢查**: 改進模型驗證機制

### 仍然存在的限制
- tflite2onnx 工具對 float16 的固有限制
- 某些 TFLite 操作的不支援 (如 DENSIFY)
- 工具版本相容性問題

## 使用指南

### 測試轉換功能
```bash
python src/qaihub_optimize/test_advanced_conversion.py
```

### 診斷轉換問題
```bash
python src/qaihub_optimize/fix_conversion_issues.py
```

### 執行完整預處理
```bash
python src/qaihub_optimize/qai_hub_optimize_full.py compile
```

## 結論

轉換問題已得到顯著改善，現在能夠：
1. ✅ 正確識別和診斷轉換問題
2. ✅ 提供具體的解決方案建議
3. ✅ 成功轉換部分模型
4. ✅ 生成詳細的轉換報告

對於無法轉換的模型，建議採用預先轉換的 ONNX 模型或重新訓練匯出為相容格式。

**轉換成功率**: 2/7 (28.6%) → 透過解決方案可達到 100% (使用預轉換模型)
