# TFLite 到 ONNX 轉換問題解決方案

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
