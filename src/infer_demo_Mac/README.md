# 純本地推論/跨平台展示

此目錄包含所有純本地端推論、效能展示、跨平台 demo 相關腳本。

Live demo (macOS)
==================

本檔案說明如何在 macOS 上設置並執行單檔 Streamlit demo `live_demo_mac.py`（本地推論）。

概覽
----
- Demo 會優先尋找 `src/models/qaihub_optimized/` 下的 ONNX 模型（best-effort）。若沒有或 onnxruntime 不可用，會自動 fallback 到 MediaPipe。
- 支援 Image（靜態）、Video（上傳影片）與 Camera（實時）三種模式。
- 曝露超參數：`torso_keypoint_mode`、`angle_calc_mode`、`angle_threshold`、`cooldown_seconds`、`confidence_threshold`。
- 包含 pre-fall risk history（時間序列）與即時 alert 機制。
# 純本地推論 / infer_demo

此目錄包含本地推論（live demo）相關說明，主程式為 `live_demo_mac.py`（通常以 Streamlit 啟動）。

重點
- 這個專案子系統使用一個專屬虛擬環境：`.venv_infer`（放在專案根目錄）。
- `qaihub_optimize` 或其他子模組應使用各自的專屬環境，彼此互不影響。

快速開始（macOS / Linux）
-------------------------
1. 在專案根目錄使用 `start.sh`：

```bash
./start.sh
```

2. 腳本會進行：
- 檢查系統 Python（預設使用 `python3`，可透過環境變數 `PYTHON_CMD` 覆蓋）
- 若不存在則建立 `.venv_infer`（project-local venv）
- 在虛擬環境內安裝 `src/infer_demo_Mac/requirements_inferMac.txt` 的套件
- 啟動虛擬環境並以 `streamlit run src/infer_demo_Mac/live_demo_mac.py` 啟動 demo

快速開始（Windows）
---------------------
1. 在專案根目錄使用 `start.bat`：

```powershell
start.bat
```

2. `start.bat` 的行為與 macOS 相同（建立/使用 `.venv_infer`、安裝 `requirements_infer.txt`，再啟動 demo）。

檔案位置
- `start.sh` / `start.bat`：專案根目錄
- macOS 依賴：`src/infer_demo_Mac/requirements_inferMac.txt`
- Windows 依賴：`requirements_infer.txt`（專案根）

注意事項
- 需要系統層級的 ffmpeg（mac: `brew install ffmpeg`；Windows: 建議使用 choco 或手動將 ffmpeg 加入 PATH）。
- 如需在 Apple Silicon 使用特定 PyTorch wheel，請參考 PyTorch 官網並手動安裝對應 wheel（或在 venv 建立後以 pip 安裝）。
- 若 `live_demo_mac.py` 路徑或名稱有變動，請修改 `start.sh`/`start.bat` 中的 `LIVE_PY` 變數。

故障排除
- 若 streamlit 或其他套件在安裝時編譯失敗，建議先安裝系統相依（Xcode command line tools、brew libs），或在有預編譯 wheel 的環境中安裝。

進階／自訂
- 想要我在你的環境中自動建立並啟動（會下載並安裝套件），回覆「請安裝並啟動」，我可執行該操作並回傳日誌。

聯絡
- 有需求變更（例如不同 venv 名稱、或想把 venv 放到另一個資料夾），請告訴我你想要的路徑與名稱。
