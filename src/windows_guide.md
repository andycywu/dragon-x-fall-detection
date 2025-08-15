# Dragon X 跌倒檢測系統 - Windows 使用指南

## 系統概述

Dragon X 跌倒檢測系統是一個使用計算機視覺技術來檢測人體跌倒的系統。該系統能夠處理圖像或視頻輸入，並分析人體姿態以確定是否發生了跌倒。

## 在 Windows 上運行系統

在 Windows 上運行 Dragon X 跌倒檢測系統需要遵循以下步驟：

### 前提條件

1. Python 3.x 已安裝
2. 必要的 Python 庫已安裝:
   - opencv-python
   - mediapipe
   - numpy

### 基本操作

1. **初始化檢測器**:
   ```python
   from fall_detector import FallDetector
   detector = FallDetector()
   ```

2. **處理單個圖像**:
   ```python
   import cv2
   image = cv2.imread('test_image.jpg')
   result = detector.detect_fall_from_frame(image)
   if result is not None:
       is_falling, confidence = result
       print(f"跌倒狀態: {'是' if is_falling else '否'}, 置信度: {confidence}")
   ```

### 運行演示腳本

我們提供了幾個演示腳本來展示系統功能：

1. **簡化版演示** (`simplified_demo.py`):
   - 基本的圖像處理功能
   - 使用一張測試圖像

2. **增強版演示** (`enhanced_demo.py`):
   - 處理多張圖像
   - 添加視覺化效果

3. **最終版演示** (`fixed_final_demo.py`):
   - 處理所有測試圖像
   - 提供詳細的結果分析
   - 創建可視化結果

運行方式:
```
python fixed_final_demo.py
```

### 已知問題

1. 在 Windows 命令提示符中可能會出現 Unicode 編碼問題。我們的演示腳本已經優化以避免這個問題。
2. QAI Hub 集成需要額外的 API 令牌配置。
3. 某些圖像可能無法正確檢測到人體姿態，在這種情況下，系統會返回"無姿態檢測"。

### 系統配置

如果需要配置 QAI Hub API 令牌，請創建 `.qai_hub` 目錄並設置適當的配置文件，或通過環境變量設置令牌。

## 結果解釋

系統返回兩個主要數值：
1. **跌倒狀態** (布爾值): 表示是否檢測到跌倒
2. **置信度** (浮點數): 表示檢測結果的可信度，值越低表示越可能是跌倒狀態

在我們的測試中，置信度低於 1.5 的結果可能表示跌倒或接近跌倒的姿態。

## 技術細節

該系統使用 MediaPipe 作為主要的姿態檢測引擎，並結合了自定義的角度計算算法來確定跌倒狀態。系統還支持 ONNX 運行時和 QAI Hub 集成（需要額外配置）。

