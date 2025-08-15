# 🐉 Dragon X Fall Detection System
**跨平台AI老人跌倒檢測系統 - Qualcomm Snapdragon X Elite優化版**

## 🔄 2025年8月11日更新: Windows Device Cloud相容性改進與QAI Hub配置更新

- ✅ 新增Windows相容版本主程式 `main_windows.py`
- ⚡ 優化了Snapdragon X Elite處理器的硬體加速
- 🛠️ 改進了備用檢測器，確保在不支援MediaPipe的環境中也能運作
- 🔌 添加了QAI Hub相容性和適當的錯誤處理機制
- 📦 新增Windows專用安裝需求文件 `requirements_windows.txt`
- 🔧 **新增**: QAI Hub API URL配置修復工具 - 解決新舊API網址切換問題
  - 執行 `python fix_qai_hub_api_url.py` 自動檢測並修復QAI Hub配置
  - 在Windows上可以直接雙擊 `fix_qai_hub_api_url.bat` 運行修復工具

## 🏆 黑客松項目亮點
- ✅ **9個AI模型**成功部署到Snapdragon X Elite CRD  
- ⚡ **37%性能提升** (Mac 45ms → Snapdragon 30ms)
- 💾 **33%記憶體節省** (Mac 235MB → Snapdragon 156MB)  
- 🌐 **真正跨平台**：Mac開發 → Snapdragon部署
- ☁️ **QAI Hub集成**：雲端編譯 + 邊緣推理

A real-time fall detection system that combines pose analysis using MediaPipe BlazePose and voice keyword detection using OpenAI Whisper, optimized for Qualcomm Snapdragon X Elite platform.

## Features

- **Real-time Pose Detection**: Uses MediaPipe BlazePose to analyze body posture and detect potential falls
- **Voice Keyword Detection**: Uses OpenAI Whisper to detect help keywords ("help", "救命") from audio input
- **Fusion Alert System**: Combines both detection methods with configurable cooldown periods
- **Real-time Monitoring**: Live webcam and microphone processing with OpenCV display
- **Web Dashboard**: Streamlit-based UI for testing and monitoring
- **Alert History**: Tracks and visualizes detection events

## Installation

1. Clone or download this repository

2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Windows Device Cloud環境安裝

如果您要在Qualcomm Device Cloud (Windows)上執行系統，請使用以下命令安裝相容依賴：

```bash
pip install -r requirements_windows.txt
```

部署到Device Cloud (如有需要)：

```bash
python deploy_to_device_cloud.py
```

## Usage

### Real-time Detection (Main Application)

在Mac環境運行主應用程式：

```bash
python main.py
```

**Controls:**
- Press 'q' to quit
- Press 'c' to clear alert history
- Press 's' to show recent alerts

### Windows Device Cloud環境運行

在Windows Device Cloud環境運行相容版本：

```bash
python main_windows.py --camera_id 1
```

**選項:**
- `--camera_id 1`: 使用攝像頭ID 1 (Device Cloud通常需要)
- `--resolution 640x480`: 設置特定解析度
- `--no-display`: 不顯示視窗 (無頭模式)
- `--hardware_acceleration`: 啟用硬體加速 (如可用)

### 高級演示應用程式 (Device Cloud)

```bash
# 即時攝像頭演示
python snapdragon_realtime_demo_windows.py

# 視頻檔案處理
python snapdragon_video_demo_windows.py --video path/to/video.mp4

# 性能基準測試
python snapdragon_performance_benchmark_windows.py
```

### 攝像頭測試工具

```bash
# 列出可用攝像頭
python aws_virtual_camera_test_windows.py --list

# 測試特定攝像頭
python aws_virtual_camera_test_windows.py --camera_id 1
```

The system will:
- Open your webcam for pose detection
- Start microphone monitoring for voice detection
- Display live video feed with pose landmarks
- Show alerts when falls or help keywords are detected

### Web Dashboard

Launch the Streamlit dashboard for testing and monitoring:

```bash
streamlit run ui_dashboard.py
```

**Features:**
- Upload images for pose analysis testing
- Upload audio files for keyword detection testing
- View alert history and statistics
- Configure detection parameters
- Monitor system status

## System Components

### Core Components (Cross-Platform)

1. **Fall Detector (`fall_detector.py` & `fall_detector_opencv.py`)**
   - 主要檢測器: 使用MediaPipe BlazePose進行姿態估計
   - 備用檢測器: 使用OpenCV進行動態分析 (當MediaPipe不可用時)
   - 計算身體角度偵測跌倒狀態

2. **Whisper Detector (`whisper_infer.py`)**
   - 使用OpenAI Whisper進行語音辨識
   - 偵測多語言求救關鍵字 ("help", "救命")
   - 實時處理音頻數據

3. **Fusion Trigger (`fusion_trigger.py`)**
   - 結合視覺和語音檢測結果
   - 實現警報冷卻以防止頻繁觸發
   - 追蹤警報歷史記錄

### Mac環境專用組件

1. **Main Application (`main.py`)**
   - 整合所有組件進行實時處理
   - 處理網絡攝像頭和麥克風輸入
   - 顯示實時視頻與疊加層

2. **UI Dashboard (`ui_dashboard.py`)**
   - Streamlit網頁界面用於測試
   - 圖像和音頻文件上傳功能
   - 警報可視化和統計

### Windows Device Cloud相容組件

1. **Windows主程式 (`main_windows.py`)**
   - Windows相容主應用程式
   - 內置環境檢測和適配
   - 自動啟用備用組件
   - 處理Device Cloud特定問題

2. **統一AI檢測器 (`unified_ai_detector_windows.py`)**
   - 純ASCII版本 (無Unicode字符)
   - 跨平台AI檢測器
   - QAI Hub備用機制

3. **Snapdragon演示應用**
   - `snapdragon_realtime_demo_windows.py`: 即時攝像頭演示
   - `snapdragon_video_demo_windows.py`: 視頻文件處理
   - `snapdragon_performance_benchmark_windows.py`: 性能基準測試
   - `aws_virtual_camera_test_windows.py`: 攝像頭測試工具

## Configuration

### Detection Parameters
- **Fall angle threshold**: Adjust sensitivity of fall detection (60-120°)
- **Alert cooldown**: Minimum time between alerts (1-10 seconds)
- **Audio buffer**: Duration of audio processed for keyword detection

### Supported Audio Formats
- WAV, MP3, M4A for file upload
- Real-time microphone input (16kHz mono)

### Help Keywords
- English: "help", "HELP", "Help"
- Chinese: "救命", "救命啊"

## Hardware Requirements

- **Camera**: USB webcam or built-in camera
- **Microphone**: Any audio input device
- **CPU**: Sufficient for real-time video processing
- **Memory**: At least 4GB RAM recommended

## Performance Tips

1. **Camera Resolution**: Lower resolution (640x480) for better performance
2. **Audio Buffer**: Smaller buffers for lower latency, larger for better accuracy
3. **Model Selection**: Use Whisper "tiny" model for fastest processing
4. **Background Processing**: Audio processing runs in separate thread

## Troubleshooting

### Common Issues

1. **Camera not opening**:
   - Check camera permissions
   - Try different camera index (Mac: 0, Windows Device Cloud: 1)
   - Ensure camera is not used by other applications

2. **Audio input errors**:
   - Check microphone permissions
   - Verify audio device is working
   - Try different sample rates

3. **Model loading errors**:
   - Ensure internet connection for initial Whisper model download
   - Check available disk space
   - Verify Python environment has required packages

4. **Performance issues**:
   - Close other applications using camera/microphone
   - Reduce video resolution
   - Use smaller Whisper model ("tiny" vs "base")

### Windows Device Cloud特定問題

1. **攝像頭未找到**:
   ```bash
   # 列出可用的攝像頭
   python aws_virtual_camera_test_windows.py --list
   
   # 通常使用ID 1而非ID 0
   python main_windows.py --camera_id 1
   ```

2. **Unicode編碼錯誤**:
   - 使用純ASCII版本的檔案 (無中文或表情符號)
   - 檢查檔案編碼是否為UTF-8

3. **QAI Hub集成問題**:
   - 檢查API令牌環境變量:
   ```bash
   export QAI_HUB_API_TOKEN="your_token_here"
   ```
   - 修復QAI Hub API URL問題:
   ```bash
   # 自動修復QAI Hub配置問題
   python fix_qai_hub_api_url.py
   # 或在Windows上雙擊執行
   # fix_qai_hub_api_url.bat
   ```
   - 查看 `QAI_HUB_CONFIG_FIX.md` 獲取詳細說明
   - 如果QAI Hub不可用，系統會自動回退到CPU執行

4. **部署問題**:
   - 驗證SSH連接和部署
   ```bash
   python deploy_to_device_cloud.py --test-connection
   ```

### Error Messages

- `Could not open camera`: Camera access issue
- `Audio callback status`: Microphone input problem
- `Error in keyword detection`: Whisper processing issue
- `No pose detected`: Person not visible in frame
- `ONNX Runtime not available`: Missing dependency
- `QAI Hub not available`: QAI integration issue

## Development

### Project Structure

```
├── main.py                              # Mac主程式
├── main_windows.py                      # Windows相容版本主程式 (新增!)
├── fall_detector.py                     # MediaPipe姿態檢測器
├── fall_detector_opencv.py              # OpenCV備用檢測器
├── whisper_infer.py                     # 語音關鍵字檢測
├── fusion_trigger.py                    # 警報融合邏輯
├── ui_dashboard.py                      # 網頁儀表板
├── unified_ai_detector.py               # Mac版AI檢測器
├── unified_ai_detector_windows.py       # Windows相容AI檢測器
├── requirements.txt                     # Mac依賴
├── requirements_windows.txt             # Windows相容依賴 (新增!)
├── deploy_to_device_cloud.py            # Device Cloud部署工具
├── fix_qai_hub_api_url.py               # QAI Hub API URL修復工具 (新增!)
├── fix_qai_hub_api_url.bat              # Windows版QAI Hub修復工具 (新增!)
├── QAI_HUB_CONFIG_FIX.md                # QAI Hub配置修復說明 (新增!)
├── snapdragon_realtime_demo_windows.py  # Device Cloud即時演示
├── snapdragon_video_demo_windows.py     # Device Cloud視頻處理演示
├── aws_virtual_camera_test_windows.py   # 攝像頭測試工具
├── DEVICE_CLOUD_DEMO_GUIDE.md           # Device Cloud演示指南
├── MAC_TO_WINDOWS_MIGRATION_GUIDE.md    # 遷移指南
└── README.md                            # 本文件
```

### Adding New Features

1. **New Keywords**: Edit `help_keywords` list in `WhisperKeywordDetector`
2. **Detection Logic**: Modify angle calculations in `FallDetector`
3. **Alert Types**: Extend `AlertEvent` class in `fusion_trigger.py`
4. **UI Components**: Add new pages/components to `ui_dashboard.py`

## License

This project is for educational and research purposes. Please ensure proper attribution when using the code.

## Acknowledgments

   - MediaPipe for pose detection
   - OpenAI Whisper for speech recognition
   - OpenCV for computer vision
   - Streamlit for web interface

---

## qnn_sample_apps 子專案目錄結構


## 目前專案目錄結構


```
mvp_fall_detection_starter/
├─ src/                        # 所有核心程式、模組、啟動腳本、依賴檔案
│  ├─ main.py
│  ├─ ...（其他核心模組/腳本）
│  ├─ models/                  # AI 模型檔案
│  │   ├─ job_*.tflite/.dlc/.onnx.zip
│  ├─ qdc_package/             # QDC 安裝包與模組
├─ elderly_data/               # 資料
│  ├─ elderly_behavior.db
│  └─ face_encodings.json
├─ test_images/                # 測試圖像
│  ├─ andy.jpg
│  └─ official_test_image.jpg
├─ assets/                     # 靜態資源
├─ Old_Data/                   # 備份或舊版內容
├─ README.md
├─ requirements.txt            # 全域依賴
├─ requirements_demo.txt
├─ requirements_windows.txt
├─ CLEANUP_INSTRUCTIONS.md
├─ DEPLOYMENT_GUIDE.md
├─ ENVIRONMENT_SETUP_COMPLETE.md
├─ PROJECT_SUMMARY.md
├─ FINAL_REPORT.md
├─ ...（其他必要說明文件）
```

### 說明
- `src/`：所有核心功能、模組、依賴、啟動腳本
- `elderly_data/`：資料庫與人臉特徵等資料
- `test_images/`：測試圖像
- `assets/`：靜態資源
- `Old_Data/`：備份或舊版內容
- 其他根目錄僅保留必要說明文件與全域依賴
