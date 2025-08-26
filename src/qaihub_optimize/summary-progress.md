## summary-progress: `qai_hub_optimize_full.py`

檔案位置: `src/qaihub_optimize/qai_hub_optimize_full.py`

目的：整理並摘要該檔案目前所有已實作內容、行為、副作用、相依、以及可驗證步驟，供開發追蹤與下一步規劃使用。

---

## 高階摘要

- 功能：提供一個 all-in-one 的 CLI 工具，整合 QAI Hub 相關流程（compile、profile、quantize、infer、demo、official、test、link、compile_profile(-jobs)）。
- 架構：模組化，藉由 `modules/*` 與多個 detector/system 類別（例如 `PracticalQAIHubONNX`, `QAIHubUnifiedDetector`）完成實際作業。
- 行為：以環境變數驅動模型目錄，並呼叫 `QAIHubPipeline` 及 `QAIHubClient` 等模組執行工作；部分動作會呼叫外部腳本（`tools/run_onnx_fall_detection.py`）或執行 TFLite->ONNX 轉換。

## 主要相依與匯入

- Python 標準庫：argparse, sys, os, time, pathlib.Path, subprocess, shutil, re, logging, json
- 第三方：python-dotenv (`load_dotenv`)（需在環境中安裝）
- 專案內模組（相對匯入）：
  - `modules.scanner.ModelScanner`
  - `modules.conversion.ModelConverter`
  - `modules.advanced_conversion.AdvancedModelConverter`, `get_advanced_converter`
  - `modules.format_check.FormatChecker`
  - `modules.qaihub_client.QAIHubClient`
  - `modules.pipeline.QAIHubPipeline`
  - `modules.job_monitor.QAIHubJobMonitor`, `get_job_monitor`
- 其他系統/偵測類：`PracticalQAIHubONNX`, `FinalQAIHubONNXSystem`, `QAIHubUnifiedDetector`, `OfficialQAIHubDetector`（需在 repo 中存在）

## 環境變數與常數

- 讀取 `.env` 並使用：
  - `MODELS_BASE_DIR`（必須）
  - `ONNX_MODEL_DIR`
  - `MODEL_SOURCE_DIR`
  - `OPTIMIZED_MODEL_DIR`
- `get_models_dir()` 提供 fallback（若未設定 MODELS_BASE_DIR，會回到 repo 的 `models/` 目錄）。

如果任何必要 env 變數未設定，程式在 import 階段會印出錯誤並 `sys.exit(1)`。

## 函式/命令摘要

- ensure_directory_exists(directory)
  - 功能：確保指定目錄存在，若不存在則建立。
  - 錯誤處理：建立失敗會印出錯誤並 exit。

- find_executable_in_venv(exe_name)
  - 功能：嘗試在 `src/qaihub_optimize/.venv/bin` 與系統 PATH 中尋找可執行檔。

- convert_tflite_to_onnx_advanced(tflite_path, onnx_path)
  - 功能：透過 `get_advanced_converter()` 提供的 advanced converter 執行轉換，回傳 (success: bool, message: str)。
  - 行為：會記錄 logger 資訊與例外。

- convert_tflite_to_onnx(tflite_path, onnx_path)
  - 功能：建立輸出目錄並呼叫 advanced converter；若失敗會將錯誤寫入 `conversion_errors.log`。

- run_compile()
  - 功能：建立 `QAIHubPipeline` 並呼叫 `run_compile_pipeline(source='onnx')`。
  - 成功時會列出 pipeline 中標記為已下載的優化模型路徑。

- run_profile()
  - 功能：建立 `QAIHubPipeline` 並呼叫 `run_profile_pipeline()`。

- run_infer()
  - 功能：示範性載入 `PracticalQAIHubONNX` 並呼叫 `load_mediapipe_models()`，目前僅提示支援現有模型推論。

- run_demo()
  - 功能：嘗試執行 `demo_qai_hub_detection()`（若可用），接著以 `tools/run_onnx_fall_detection.py` 執行 quick demo（quick_n=20）。
  - 行為：優先嘗試在虛擬環境中找 python 可執行檔，使用 `subprocess.run()` 執行外部 runner。

- run_official()
  - 功能：執行官方 demo（`demo_official_qai_hub_detection()`）並執行 full ONNX runner（不帶 --quick_n）。

- run_test()
  - 功能：呼叫 `test_live_detection()`。

- run_compile_profile_jobs() / run_compile_profile()
  - 功能：以 `QAIHubPipeline` 執行 compile+profile 流程，分別為批次 (jobs) 或單一模型（且可選是否做 infer）。

- run_link()
  - 功能：提供一個 link 設定範例並提示使用者輸入是否使用；若使用會呼叫 `pipeline.qaihub_client.submit_link_job(link_config, "fall_detection_pipeline")`。
  - 互動式：會使用 `input()` 詢問是否執行。

- main()
  - 功能：解析 CLI 參數並 dispatch 到上面對應的 run_* 函式，包含 `quantize` 子命令會呼叫 `pipeline.run_quantize_pipeline(...)`。

- __main__ 行為
  - 在啟動時會把 `MODELS_BASE_DIR` 展開為絕對路徑，並確保所有必要目錄存在。
  - 會執行一個測試轉換：嘗試將 `RAW_MODEL_DIR/face_detector.tflite` 轉換到 `ONNX_MODEL_DIR/face_detector.onnx`（使用 `convert_tflite_to_onnx`）。
  - 最後呼叫 `main()` 並捕捉例外。

## 副作用與注意事項

- 在 import/頂層會檢查 `.env` 並在某些情況下直接 `sys.exit(1)`。這會使得檔案難以被單元測試或在沒有配置 env 的情況下 import。
- 使用 `input()` 與 `subprocess.run()` 等會使得 CLI 在非互動環境下需要特別處理。
- 假設 repo 中有一組模組（`modules/*`、`PracticalQAIHubONNX` 等），若缺少會導致 ImportError。

## 建議的改善/待辦 (small, low-risk)

1. 將 `.env` 必要變數檢查延後到 `main()` 或啟動序，以便在 import 時不會直接 exit，利於測試。
2. 將互動式 `input()` 用旗標或 CLI 參數替代，方便自動化執行。
3. 把 `convert_tflite_to_onnx` 的測試轉換行為包成可選參數（例如 `--run_conversion_test`），避免每次啟動都嘗試轉換。
4. 新增 `--dry-run` 或 `--yes` 選項，用於 CI/自動化工作流程。

## 驗證（How to smoke-test）

1. 確保 `.env` 設定（或建立一個簡單的測試 `.env`）：
   - MODELS_BASE_DIR、ONNX_MODEL_DIR、MODEL_SOURCE_DIR、OPTIMIZED_MODEL_DIR
2. 呼叫 CLI 幫助訊息：
   - python src/qaihub_optimize/qai_hub_optimize_full.py --help
3. 嘗試非破壞模式的 demo/help：
   - python src/qaihub_optimize/qai_hub_optimize_full.py demo

## 目前變更檔案

- 新增： `src/qaihub_optimize/summary-progress.md`（本檔） — 目的：摘要與進度追蹤

---

## Requirements coverage

- 使用者需求：整理 `qai_hub_optimize_full.py` 的所有實作並產出 `summary-progress.md` → Done

---

作者備註：如需我把檔案內容轉為更結構化的 TODO list（例如每個函式再拆成 task），或直接將上面建議逐項實作，我可以接著一項項修改與 PR。
