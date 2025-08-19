# Copilot Instructions for Dragon X Fall Detection System

## 專案架構與核心元件
- **多平台支援**：本專案針對 Mac、Windows Device Cloud、Snapdragon X Elite 進行優化，主程式分別為 `main.py`、`main_windows.py`、`snapdragon_*.py`。
- **偵測模組**：
  - `fall_detector.py`/`fall_detector_opencv.py`：姿態偵測（MediaPipe/備用OpenCV）
  - `whisper_infer.py`：語音關鍵字偵測（Whisper）
  - `fusion_trigger.py`：多模態融合與冷卻機制
- **Web UI**：`ui_dashboard.py`（Streamlit）提供上傳測試、參數調整、歷史紀錄等功能。
- **QAI Hub 整合**：`src/qaihub_optimize/` 內含模型最佳化、雲端量化、API URL 修復工具。

## 關鍵開發流程
- **安裝依賴**：
  - Mac: `pip install -r requirements.txt`
  - Windows: `pip install -r requirements_windows.txt`
- **執行主程式**：
  - Mac: `python main.py`
  - Windows: `python main_windows.py --camera_id 1`
  - Snapdragon: `python snapdragon_realtime_demo_windows.py`
- **Web UI 啟動**：`streamlit run ui_dashboard.py`
- **QAI Hub API 修復**：`python fix_qai_hub_api_url.py`（或執行 .bat 檔）

## 重要慣例與模式
- **相依管理**：不同平台有獨立 requirements 檔案，勿混用。
- **相機/麥克風 index**：Mac 預設 0，Windows/Device Cloud 預設 1。
- **冷卻機制**：`fusion_trigger.py` 控制警報觸發頻率，避免重複警報。
- **多語系關鍵字**：`WhisperKeywordDetector` 內 `help_keywords` 支援中英文。
- **備援策略**：MediaPipe 不可用時自動切換 OpenCV。
- **QAI Hub 整合失敗時自動 fallback 至 CPU。**

## 常見開發/除錯指令
- 列出可用相機：`python aws_virtual_camera_test_windows.py --list`
- 測試部署連線：`python deploy_to_device_cloud.py --test-connection`
- 啟動最佳化腳本：`python src/qaihub_optimize/qai_hub_optimize_full.py`

## 重要檔案/目錄
- `src/`：核心程式碼
- `doc/`：部署、優化、QAI Hub、平台遷移等技術文件
- `elderly_data/`：行為資料與臉部特徵
- `test_images/`：測試用影像

## 新功能擴充建議
- 新增語音關鍵字：編輯 `help_keywords`
- 改進偵測邏輯：調整 `FallDetector` 角度計算
- 新增警報型態：擴充 `AlertEvent`（fusion_trigger.py）
- UI 新頁面：於 `ui_dashboard.py` 增加元件

---
如遇特殊平台或 QAI Hub 整合問題，請優先參考 `doc/` 內相關指南。
