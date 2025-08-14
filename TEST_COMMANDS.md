# 🧪 Dragon X 測試命令集

## ✅ 問題修復摘要
1. **INVALID_PROTOBUF 錯誤** - 改善 DLC 檔案處理，自動切換到原始 ONNX
2. **日誌重複輸出** - 移除每幀的重複姿態檢測日誌
3. **新增離線模式** - 可在無 QAI Hub 連線時測試程式流程

## 🚀 建議測試命令

### 1. 離線模式測試 (本地快速驗證)
```bash
python dragon_x_fall_detection_system.py --offline
```
- 跳過 QAI Hub 連線
- 測試程式邏輯與流程
- 適合語法驗證

### 2. 即時推論測試 (修復版)
```bash
python dragon_x_fall_detection_system.py --realtime --camera-index 0 --max-frames 30
```
- 自動隔離無效 DLC 檔案
- 自動切換到原始 ONNX
- 減少日誌重複輸出

### 3. 純 ONNX 編譯測試 (避免 DLC 問題)
```bash
python dragon_x_fall_detection_system.py --no-qnn-dlc --export-local-onnx --wait-compile --download-compiled
```
- 編譯時不使用 `--target_runtime qnn_dlc`
- 產出標準 ONNX 格式
- 避免 INVALID_PROTOBUF 錯誤

### 4. Edge 模式測試 (使用現有模型)
```bash
python dragon_x_fall_detection_system.py --edge-only --export-local-onnx --realtime --max-frames 50
```
- 不重新提交編譯
- 匯出原始 ONNX 作為備用
- 測試本地推論

## 🔧 除錯選項

### 檢查編譯狀態
```bash
python dragon_x_fall_detection_system.py --wait-compile --export-status
```

### 完整 Pipeline 測試
```bash
python dragon_x_fall_detection_system.py --full-pipeline --wait --export-status
```

## 📋 期望改善效果
- ✅ 無 INVALID_PROTOBUF 錯誤重複
- ✅ 日誌輸出簡潔清晰
- ✅ 自動 fallback 到可用 ONNX
- ✅ 離線模式支援本地測試
