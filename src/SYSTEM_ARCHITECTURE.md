# Dragon X 跌倒檢測系統 - 系統架構文檔

本文檔詳細說明 Dragon X 跌倒檢測系統的系統架構、元件關係和技術流程。

## 系統概述

Dragon X 跌倒檢測系統是一個整合視覺和聲音分析的跌倒檢測解決方案，能夠檢測使用者的跌倒姿態並辨識求救關鍵詞，適用於老年人照護和居家安全監控。

## 系統架構

系統由以下核心元件組成：

```
                       +--------------------+
                       |  主應用程式層       |
                       | (main.py/         |
                       |  main_windows.py) |
                       +--------+-----------+
                                |
                +---------------+----------------+
                |                                |
    +-----------v-----------+      +-------------v----------+
    |    視覺檢測子系統      |      |    語音檢測子系統       |
    | (fall_detector.py/   |      | (whisper_infer.py)     |
    |  fall_detector_      |      +-------------+----------+
    |  opencv.py)          |                    |
    +-----------+-----------+                   |
                |                               |
                |           +-------------------v----+
                +---------->|    決策融合層          |
                            | (fusion_trigger.py)   |
                            +----------------------+
```

## 元件說明

### 1. 主應用程式層

- **main.py**: Mac/Unix 平台的主要應用程式入口
- **main_windows.py**: Windows 平台的相容版本
- **main_compatible.py**: 通用跨平台版本

主應用程式負責：
- 初始化各子系統
- 管理視訊和音訊輸入
- 處理使用者介面和顯示
- 協調子系統間的互動

### 2. 視覺檢測子系統

- **fall_detector.py**: 使用 MediaPipe 的姿態估計檢測跌倒
- **fall_detector_opencv.py**: 當 MediaPipe 不可用時的 OpenCV 備用解決方案

視覺檢測功能：
- 實時姿態關鍵點檢測
- 計算軀幹角度和姿態分析
- 基於姿態變化識別跌倒事件

### 3. 語音檢測子系統

- **whisper_infer.py**: 使用 OpenAI Whisper 進行語音關鍵詞辨識

語音檢測功能：
- 實時音訊處理
- 識別「救命」等求救關鍵詞
- 多語言支援（中文、英文）

### 4. 決策融合層

- **fusion_trigger.py**: 結合視覺和語音證據做出警報決策

決策融合功能：
- 整合多模態檢測結果
- 基於可信度評分觸發警報
- 維護警報歷史記錄
- 防止警報洪水（冷卻機制）

## 技術流程

1. **初始化階段**:
   - 啟動視訊捕獲
   - 初始化音訊處理
   - 準備檢測模型

2. **持續檢測循環**:
   - 視訊幀處理
     - 姿態關鍵點檢測
     - 跌倒姿態分析
   - 音訊緩衝處理
     - 關鍵詞識別
     - 信心度評估

3. **融合決策**:
   - 評估視覺證據
   - 評估聲音證據
   - 綜合評分和警報生成

4. **響應和通知**:
   - 視覺警報顯示
   - 警報記錄保存

## QAI Hub 整合

系統通過 `integration/` 目錄中的模組與 Qualcomm AI Hub 整合，提供硬體加速和優化。

- **qai_hub_integration.py**: QAI Hub API 整合
- **setup_qai_token.py**: 配置 QAI Hub 訪問權限
- **qai_hub_job_monitor.py**: 監控 QAI Hub 任務狀態

## 部署流程

系統支援部署到 Qualcomm Device Cloud:

1. 準備部署包:
   ```
   python deployment/simple_deploy_to_device_cloud.py --prepare
   ```

2. 執行部署:
   ```
   python deployment/simple_deploy_to_device_cloud.py --deploy
   ```

詳細部署流程請參考 `DEPLOYMENT_GUIDE.md`。

## 擴展和自定義

系統設計為模組化架構，可以通過以下方式進行擴展：

1. 替換檢測器: 實現相同介面的自定義檢測器
2. 添加新融合邏輯: 修改 fusion_trigger.py 中的決策邏輯
3. 更換 UI: 自定義 draw_overlay 方法
4. 添加通知機制: 在警報觸發時添加外部通知

## 故障排除

常見問題:

1. MediaPipe 加載失敗 - 系統會自動使用 OpenCV 備用方案
2. 音訊裝置無法訪問 - 只使用視覺檢測
3. QAI Hub 連接問題 - 參考 QAI_HUB_SETUP_GUIDE.md
4. 效能問題 - 調整影像分辨率或幀率
