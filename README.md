# Dragon X Fall Detection — Demo & Model Compile Guide

此檔為 demo 專用說明，保留原始 `README_OLD.md` 不變。重點聚焦於透過 `start.sh` 啟動的本地 demo、即時推論主程式 `src/infer_demo_Mac/live_demo_mac.py`，以及模型編譯/分析主程式 `src/qaihub_optimize/qai_hub_optimize_full.py`。

## 主要重點
- 以 `start.sh` 啟動的 demo 為本地測試主流程（方便一次性啟動攝影機與音訊處理）
- 即時推論示範主程式：`src/infer_demo_Mac/live_demo_mac.py`（展示即時攝影機推論、姿態疊加與警報）
- 模型編譯 / 分析主程式：`src/qaihub_optimize/qai_hub_optimize_full.py`（包含模型轉出、上傳、編譯 submit 與 profile）

## 快速開始（macOS）

1) 安裝 Python 相依（建議 macOS 專用檔案）

```bash
pip install -r requirements_inferMac.txt
```

2) 啟動 demo（透過 start.sh，會啟動 live demo）

```bash
./start.sh
# 或直接
python src/infer_demo_Mac/live_demo_mac.py
```

3) 若要只執行即時示範程式（方便 debug）：

```bash
python src/infer_demo_Mac/live_demo_mac.py --camera_id 0 --resolution 640x480
```

說明：`start.sh` 會根據專案預設參數啟動程式、設定環境變數（例如模型路徑）、並將輸出紀錄到 `reports/` 或 `output/`（視設定）。

## 模型編譯與分析（QAI Hub / ONNX）

主程式：`src/qaihub_optimize/qai_hub_optimize_full.py`

- 功能：載入本地模型（或 MediapPipe 相關子模型）、轉出至 ONNX/TorchScript、上傳至 QAI Hub、提交編譯任務、取得 profile 與編譯報告。
- 常用執行方式：

```bash
# 設定 QAI Hub API token 後執行（若需要上傳/編譯）
export QAI_HUB_API_TOKEN="<your_token>"
python src/qaihub_optimize/qai_hub_optimize_full.py --upload --submit --profile
```

- 輸出成果位置（常見）：
   - 編譯/分析報告：`reports/onnx_fall_full.html`, `reports/onnx_fall_full.json`（或 repo 根目錄下類似 `onnx_fall_full.html`）
   - 儲存的優化模型：`src/models/qaihub_optimized/` 或 `models/qaihub_optimized/`

提示：若 QAI Hub 不可用，腳本會支援本地匯出（ONNX/TorchScript）以便離線分析。

## 專案目錄（重點說明）

以下列出專案中重要位置，並標明本 README 關注的 demo 與編譯流程：

```
mvp_fall_detection_starter/
├── start.sh                       # 一鍵啟動 demo（macOS 範例）
├── src/
│   ├── infer_demo_Mac/
│   │   └── live_demo_mac.py       # 即時推論展示主程式（顯示影像、姿態、警報）
│   ├── qaihub_optimize/
│   │   └── qai_hub_optimize_full.py# 模型轉出、上傳、submit 與 profile
│   ├── detectors/                  # 偵測器實作（如 fall_detector, fall_detector_opencv）
│   └── ...                         # 其他核心模組
├── reports/                        # 編譯與分析報告（HTML/JSON）
├── models/                         # 原始與優化模型
├── requirements_inferMac.txt       # macOS 推論相依（推薦）
├── requirements_infer.txt          # 通用推論相依
└── README.md
```

## 成果查看：模型編譯與效能報告

- 編譯後的報告通常以 HTML/JSON 存放於 `reports/` 或 repo 根目錄，例如：
   - `reports/onnx_fall_full.html` 或 `onnx_fall_full.html`
   - `reports/onnx_fall_full.json` 或 `onnx_fall_full.json`

開啟 HTML 檔即可在瀏覽器查看 operator breakdown、latency、memory 與 profile 結果。

## 常用參數與環境變數

- QAI Hub Token（需上傳/編譯時）：`QAI_HUB_API_TOKEN`
- 常見 script flags：`--upload`, `--submit`, `--profile`, `--camera_id`, `--resolution`

## Troubleshooting（快速）

- 相機無法開啟：檢查相機權限與索引（macOS 預設為 0）
- Whisper 模型載入慢：使用 `tiny` 版本以加快啟動
- QAI Hub 上傳失敗：確認 `QAI_HUB_API_TOKEN` 與網路連線

## 小提示（開發者）

- 若你要新增測試或展示頁面，優先修改 `src/infer_demo_Mac/live_demo_mac.py` 與 `start.sh` 的參數，確保 demo 能在單一命令下啟動。
- 當進行模型優化流程時，先在本地匯出 ONNX，再進行 QAI Hub 提交，這樣可以快速重現/比對不同版本的效能。

## Requirements coverage（你要求的事項）

- 將 README 以 `start.sh` demo 為主線重寫：Done
- 強調 `src/infer_demo_Mac/live_demo_mac.py` 為即時推論示範主程式：Done
- 強調 `src/qaihub_optimize/qai_hub_optimize_full.py` 為模型編譯/profile 主程式：Done
- 加入安裝與模型編譯成果位置說明：Done

若需要，我可以：
- 把 `start.sh` 內的參數註解化並自動生成一份簡短的 `USAGE.md`（方便新手）
- 或幫你把 `live_demo_mac.py` 的 CLI 與 `start.sh` 參數統一成同一套 flags，並加上範例 unit test。

## 可選相依（Optional dependencies）

專案部分功能（例如本地 TTS 播放、whisper 語音轉文字、傳統 face_recognition 備援、以及 Streamlit 互動圖表）為可選套件。
這些套件不會阻止程式啟動，但若要啟用完整功能，請在乾淨的 virtual environment 中安裝 `requirements_optional.txt`。

安裝建議（使用 virtualenv，避免修改系統 Python）：

```bash
# 建立並啟用 venv（macOS / Linux）
python3 -m venv .venv_optional
source .venv_optional/bin/activate

# 安裝可選套件
pip install -r requirements_optional.txt
```

或使用專用腳本（專案提供 `install_optional.sh`）：

```bash
./install_optional.sh
```

常見可選套件：
- `face_recognition`（dlib-backed）: 傳統人臉編碼備援
- `pyttsx3`: 本地 TTS 引擎（Windows/macOS/Linux）
- `SpeechRecognition`: 音訊收錄/辨識介面
- `whisper`: OpenAI Whisper（轉錄，會佔用大量磁碟與記憶體）
- `plotly`: Streamlit 互動圖表

備註：若你在 macOS 使用系統受管理的 Python（Homebrew 管理），請使用 virtualenv 或 pipx 來安裝可選套件；直接對系統 Python 安裝可能被系統阻止。

---
