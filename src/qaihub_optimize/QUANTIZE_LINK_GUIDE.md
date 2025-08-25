# QAI Hub Quantize 和 Link 功能指南

## 概述

本指南介紹如何在 QAI Hub Optimize 工具中使用 Quantize（量化）和 Link（模型串接）功能。

## Quantize 功能

### 量化選項

- **int8**: INT8 整數量化和校準
- **fp16**: FP16 浮點數量化  
- **none**: 不進行量化（預設）

### 使用方法

#### 方法 1: 在編譯時直接指定量化

```python
# 在程式碼中啟用量化
pipeline.run_compile_pipeline(quantize="int8")
```

#### 方法 2: 透過 JSON 配置檔（進階）

```json
{
  "model": "./model.onnx",
  "framework": "onnx", 
  "device": "Snapdragon X Elite CRD",
  "quantization": {
    "scheme": "int8",
    "calibration_data": "./calib_data"
  }
}
```

### 整合到現有流程

量化功能已無縫整合到現有的編譯流程中：

```python
# 啟用 INT8 量化的編譯流程
pipeline.run_compile_pipeline(quantize="int8")

# 啟用 FP16 量化的編譯流程  
pipeline.run_compile_pipeline(quantize="fp16")

# 不進行量化（預設行為）
pipeline.run_compile_pipeline(quantize="none")
```

## Link 功能

### 模型串接

Link 功能用於將多個已編譯的模型組合成 pipeline。

### 使用方法

#### 提交串接任務

```python
# 獲取已編譯的模型物件列表
compiled_models = [model1, model2, model3]

# 提交串接任務
link_job = client.submit_link_job(compiled_models, "my_pipeline")
```

#### 透過 CLI 執行

```bash
# 執行模型串接
python qai_hub_optimize_full.py link
```

### 串接配置

Link 功能需要實際的模型物件，而不是配置字典。模型物件可以從以下來源獲取：

1. 已上傳到 QAI Hub 的模型
2. 已編譯完成的目標模型
3. 透過 `qai_hub_models` 字典取得的模型

## Compile+Profile+Quantize 整合

### 一次完成所有操作

```python
# 執行完整的編譯+分析+量化流程
pipeline.run_compile_profile_pipeline(do_infer=True)
# 量化選項會自動傳遞到編譯階段
```

### 批次處理多模型

```python
# 批次處理多個模型並啟用量化
pipeline.run_compile_profile_pipeline(do_infer=False)
```

## 錯誤處理

### 量化錯誤處理

- 無效的量化選項會自動過濾
- 量化過程中的異常會被捕獲並記錄
- 支援 fallback 到無量化模式

### 串接錯誤處理  

- 空的模型列表會被拒絕
- 無效的模型物件會導致任務失敗
- 多種 API 呼叫方式以兼容不同 SDK 版本

## 使用範例

### 基本量化範例

```python
from modules.pipeline import QAIHubPipeline

# 初始化管道
pipeline = QAIHubPipeline()

# 執行 INT8 量化的編譯流程
success = pipeline.run_compile_pipeline(quantize="int8")

if success:
    print("✅ 量化編譯成功完成")
else:
    print("❌ 量化編譯失敗")
```

### 完整工作流程範例

```python
from modules.pipeline import QAIHubPipeline

# 初始化並執行完整流程
pipeline = QAIHubPipeline()

# 1. 編譯並量化模型
compile_success = pipeline.run_compile_pipeline(quantize="int8")

if compile_success:
    # 2. 分析模型效能
    profile_success = pipeline.run_profile_pipeline()
    
    # 3. 取得編譯後的模型進行串接
    compiled_models = list(pipeline.qaihub_client.qai_hub_models.values())
    
    # 4. 提交串接任務
    link_job = pipeline.qaihub_client.submit_link_job(
        [m['qai_hub_model'] for m in compiled_models if 'qai_hub_model' in m],
        "fall_detection_pipeline"
    )
```

## 注意事項

1. **量化需求**: 需要目標裝置支援對應的量化格式
2. **模型相容性**: 不是所有模型都適合所有量化方式
3. **校準數據**: INT8 量化可能需要提供校準數據集
4. **效能權衡**: 量化可能會影響模型精度，需根據應用場景選擇

## 疑難排解

### 常見問題

1. **量化失敗**: 檢查目標裝置是否支援該量化格式
2. **串接失敗**: 確認模型已成功編譯並上傳到 QAI Hub
3. **API 變更**: QAI Hub SDK 版本更新可能會影響參數格式

### 取得幫助

如有問題，請參考：
- QAI Hub 官方文件
- 專案中的 `doc/` 目錄
- 執行測試腳本: `python test_quantize_link.py`

## 版本資訊

- **初始版本**: 2025-08-25
- **功能**: Quantize 支援、Link 功能、錯誤處理
- **相容性**: 與現有 QAI Hub Optimize 工具完全相容
