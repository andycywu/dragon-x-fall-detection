# Dragon X Fall Detection — Demo & Model Compile Guide

此檔為 demo 專用說明，保留原始 `README.md` 不變。重點聚焦於透過 `start.sh` 啟動的本地 demo、即時推論主程式 `src/infer_demo_Mac/live_demo_mac.py`，以及模型編譯/分析主程式 `src/qaihub_optimize/qai_hub_optimize_full.py`。

## 目標
- 提供一鍵啟動 demo 的快速步驟（macOS）
- 清楚說明即時推論與模型編譯兩個主流程
- 說明模型編譯後的成果檔案與報告位置

## 快速安裝（macOS 建議）

1. 建議使用專屬虛擬環境（venv/conda）

2. 安裝推論所需依賴（macOS）

```bash
pip install -r requirements_inferMac.txt
```

若想安裝通用推論依賴，可改為 `requirements_infer.txt`。

## 啟動 demo

- 一鍵啟動（推薦，`start.sh` 會以預設參數啟動 demo）：

```bash
./start.sh
```

- 直接啟動即時示範程式（方便除錯）：

```bash
python src/infer_demo_Mac/live_demo_mac.py --camera_id 0 --resolution 640x480
```

說明：`live_demo_mac.py` 會開啟攝影機、執行姿態/語音偵測（若可用）、並在畫面上疊加偵測結果與警報。常見 flags：`--camera_id`, `--resolution`, `--no-display`。

## 模型編譯與效能分析（QAI Hub / ONNX）

主程式：`src/qaihub_optimize/qai_hub_optimize_full.py`

- 常用工作流程：
  1. 本地匯出 ONNX / TorchScript
  2. （選擇）上傳至 QAI Hub
  3. 提交編譯任務並取得 profile

- 執行範例（需要 QAI Hub 權杖時）：

```bash
export QAI_HUB_API_TOKEN="<your_token>"
python src/qaihub_optimize/qai_hub_optimize_full.py --upload --submit --profile
```

- 若 QAI Hub 無法使用，腳本支援本地匯出以做離線 profile：

```bash
python src/qaihub_optimize/qai_hub_optimize_full.py --export_local
```

## 編譯/分析成果位置

- 編譯結果與分析報告通常放在：
  - `reports/onnx_fall_full.html`
  - `reports/onnx_fall_full.json`
  - 或 repo 根目錄下的 `onnx_fall_*.html` / `onnx_fall_*.json`

- 優化後模型會儲存在：
  - `src/models/qaihub_optimized/` 或 `models/qaihub_optimized/`（視腳本設定）

開啟 HTML 報告可以檢視 operator breakdown、延遲、記憶體與 profile 結果。

## 重要檔案速覽

- `start.sh` — 一鍵啟動 demo（macOS 範例，會呼叫 `live_demo_mac.py`）
- `src/infer_demo_Mac/live_demo_mac.py` — 即時推論示範主程式（影像疊加、警報）
- `src/qaihub_optimize/qai_hub_optimize_full.py` — 模型轉出 / 上傳 / submit / profile
- `requirements_inferMac.txt` / `requirements_infer.txt` — 推論相依
- `reports/` — 編譯與分析報告（HTML/JSON）

## 常見問題快速排查

- 相機打不開：檢查 macOS 相機權限，或改用 `--camera_id` 指定索引
- 模型下載慢：使用小型 Whisper 模型（例如 `tiny`）以加速啟動
- QAI Hub 上傳/編譯失敗：檢查 `QAI_HUB_API_TOKEN` 與網路連線

## 建議的下一步（如果你要我繼續）

- 幫你把 `start.sh` 加上詳細參數註解，並同步 `live_demo_mac.py` 的 CLI flags（推薦）
- 或建立 `compile_models.sh` 包裝常用的 `qai_hub_optimize` 執行參數

---
（此檔保留原始 `README.md`，作為 demo/編譯專用說明）
