# Dragon X 跌倒檢測系統 (精簡版)

此專案是 Dragon X 跌倒檢測系統的精簡版本，保留了所有核心功能，移除了測試和開發過程中產生的非必要檔案。

## 主要功能

- **跌倒檢測**：使用 MediaPipe 進行姿態估計並分析跌倒動作
- **語音辨識**：使用 Whisper 模型偵測「救命」等關鍵詞
- **警報觸發**：結合視覺和聲音線索進行警報決策
- **跨平台支援**：支援 Mac 和 Windows 環境
- **Qualcomm Device Cloud 整合**：支援部署到 Qualcomm 裝置雲

## 目錄結構

- **detectors/** - 檢測器模組 (跌倒、語音)
- **integration/** - QAI Hub 整合
- **utils/** - 工具函數
- **demos/** - 演示應用程式
- **deployment/** - 部署工具

## 使用方法

1. 安裝依賴：
   ```
   pip install -r requirements.txt
   ```
   
2. 運行即時檢測：
   ```
   python main.py
   ```
   
3. Windows 環境下運行：
   ```
   python main_windows.py
   ```

## Qualcomm Device Cloud 部署

使用簡化的部署工具進行快速部署：
```
python deployment/simple_deploy_to_device_cloud.py
```

更多細節請參考 `DEPLOYMENT_GUIDE.md`。

## 授權協議

© 2025 Dragon X 團隊 - 保留所有權利
