# Dragon X 跌倒檢測系統 - Windows 使用指南

## 系統概述

Dragon X 跌倒檢測系統是一個使用計算機視覺技術來檢測人體跌倒的系統。該系統能夠處理圖像或視頻輸入，並分析人體姿態以確定是否發生了跌倒。此外，還可以結合音頻分析來檢測求救關鍵詞，進一步提高警報準確性。

## 在 Windows 上啟動系統

### 快速啟動方法

我們為 Windows 用戶提供了專用的啟動腳本，您可以按照以下步驟操作：

1. 打開 Windows 檔案總管，瀏覽到 Dragon X 系統目錄（`dragon_x_core` 文件夾）
2. 雙擊 `start_windows.bat` 檔案
3. 系統將自動檢查環境並安裝必要的依賴項
4. 按照提示選擇要運行的系統版本（建議選擇「2」運行 Windows 版本）

> **注意**：首次運行時，系統需要下載並安裝所有依賴，這可能需要幾分鐘時間。

### 前提條件

1. Windows 10 或更高版本
2. Python 3.8 或更高版本（推薦 Python 3.10）
3. 必要的 Python 庫 (通過啟動腳本自動安裝):
   - opencv-python
   - mediapipe
   - numpy
   - sounddevice (用於音頻分析)
   - openai-whisper (用於關鍵詞檢測)

### 基本操作

1. **自動啟動 (推薦)**:
   - 雙擊 `start_windows.bat`
   - 選擇選項 2 (Windows 版)

2. **手動啟動**:
   - 打開命令提示符（CMD）或 PowerShell
   - 導航到 Dragon X 系統目錄：
   
     ```cmd
     cd 路徑\到\dragon_x_core
     ```
   
   - 創建虛擬環境（如果尚未創建）：
   
     ```cmd
     python -m venv venv
     ```
   
   - 激活虛擬環境：
   
     ```cmd
     venv\Scripts\activate
     ```
   
   - 安裝依賴：
   
     ```cmd
     pip install -r requirements_windows.txt
     ```
   
   - 運行 Windows 版本：
   
     ```cmd
     python main_windows.py
     ```

3. **高級啟動選項**:
   通過命令行參數自定義系統行為：
   - `--camera_id INT`: 指定攝像頭 ID（預設為 1，Windows 通常使用 0 或 1）
   - `--resolution WIDTHxHEIGHT`: 設置視頻分辨率（預設為 640x480）
   - `--no-display`: 無圖形界面模式運行
   - `--hardware_acceleration`: 啟用硬件加速（如果可用）

   例如：
   
   ```cmd
   python main_windows.py --camera_id=0 --resolution=1280x720 --hardware_acceleration
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

```cmd
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

## 跨平台兼容版

Dragon X 跌倒檢測系統也提供了一個跨平台兼容版本，它不依賴於 MediaPipe（某些環境中可能難以安裝），而是使用 OpenCV 進行姿態檢測。

### 使用跨平台兼容版

1. 如果您之前嘗試運行跨平台兼容版遇到了錯誤，請先運行修復腳本：
   
   在 Windows 上：
   
   ```cmd
   fix_compatible.bat
   ```
   
   在 Mac/Unix 上：
   
   ```bash
   ./fix_compatible.sh
   ```

2. 然後使用啟動腳本並選擇選項 3（跨平台兼容版）：
   
   在 Windows 上：
   
   ```cmd
   start_windows.bat
   ```
   
   然後選擇選項 3。

### 跨平台兼容版特點

- 不需要 MediaPipe，使用 OpenCV 進行姿態分析
- 更低的資源消耗，適合較舊的電腦
- 簡化的音頻分析（基於音量檢測而非關鍵詞識別）
- 在任何支持 Python 和 OpenCV 的平台上運行

## 故障排除

如果您在 Windows 上運行時遇到問題，請嘗試以下解決方案：

### 攝像頭問題

1. **找不到攝像頭或無法開啟攝像頭**:
   - 嘗試不同的攝像頭 ID：
   
     ```cmd
     python main_windows.py --camera_id=0
     ```
     
     或
     
     ```cmd
     python main_windows.py --camera_id=1
     ```
   
   - 確保沒有其他應用程序正在使用攝像頭
   - 檢查 Windows 隱私設置，確保允許應用程序訪問攝像頭

### 依賴安裝問題

1. **安裝 whisper 或 sounddevice 時出錯**:
   - 確保已安裝最新版本的 pip:
   
     ```cmd
     python -m pip install --upgrade pip
     ```
   
   - 手動安裝這些包:
   
     ```cmd
     pip install sounddevice>=0.4.4
     pip install openai-whisper>=20230918
     ```
   
   - 如果仍然失敗，系統會自動降級為僅使用視覺檢測

2. **MediaPipe 安裝問題**:
   - 確保已安裝 Microsoft Visual C++ Redistributable
   - 嘗試安裝特定版本:
   
     ```cmd
     pip install mediapipe==0.10.0
     ```

### 運行時問題

1. **系統性能緩慢**:
   - 降低分辨率:
   
     ```cmd
     python main_windows.py --resolution=320x240
     ```
   
   - 使用硬件加速（如果支持）:
   
     ```cmd
     python main_windows.py --hardware_acceleration
     ```

2. **虛擬環境激活錯誤**:
   - 如果在啟動虛擬環境時遇到問題，可能是因為 PowerShell 的執行策略設置。請嘗試以管理員身份運行 PowerShell 並執行：
   
     ```powershell
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
     ```

## 聯繫支持

如果您遇到未在此文檔中列出的問題，請聯繫系統開發者獲取支持。
