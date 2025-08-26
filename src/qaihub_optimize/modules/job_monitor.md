# Job Monitor 模組開發說明

簡短目標

- 說明 `src/qaihub_optimize/modules/job_monitor.py` 的設計動機、主要改動、API 使用範例、已解決問題與後續建議。

概覽

- 模組目的：統一追蹤、正規化並報告 QAI Hub / 編譯 / 其它 pipeline 任務的狀態，避免外部 SDK 回傳多樣字串導致計數錯誤。
- 主要受益者：`qai_hub_optimize_full.py`、`practical_qai_hub_onnx.py` 以及整個 pipeline 的監控邏輯。

變更重點（已實作）

- 狀態正規化：把外部 SDK 或 API 回傳的狀態字串做 case-insensitive 與 group-mapping，將變形的成功/失敗/進行中等狀態統一為內部分組（例如 `succeeded`、`completed`、`results_ready` -> `COMPLETE`）。
- 安全的計數/查詢 API：新增或改造 `get_jobs_by_status`, `get_jobs_by_type`, `generate_status_report` 等方法，讓上層統計時不會受到字串差異影響。
- 事件回呼/等待函式：提供 `wait_for_compile_jobs` （或等價函式）能夠在必要時等待 compile/remote job 完成。
- 日誌與偵錯：在關鍵位置加入 logging 呼叫以便回溯（例如狀態轉換、未識別狀態、重試次數等）。

主要 API 與範例

- 常見函式（依實際 `job_monitor.py` 實現而定）：

  - `add_job(job_id, job_type, meta=None)` — 註冊新工作。
  - `update_job_status(job_id, status, info=None)` — 更新工作狀態並做正規化處理。
  - `get_jobs_by_status(status_group)` — 以正規化分組（例如 `PENDING`, `RUNNING`, `COMPLETE`, `ERROR`）查詢工作。
  - `generate_status_report()` — 回傳整體工作統計摘要（counts per group、未完成清單等）。

Python 範例：

```python
# 範例：匯入與基本操作
from qaihub_optimize.modules import job_monitor

# 新增工作
job_monitor.add_job('job-123', 'compile', meta={'model':'x.onnx'})

# 更新狀態（外部 SDK 回傳字串也會被正規化）
job_monitor.update_job_status('job-123', 'SUCCEEDED')

# 取得已完成的編譯工作
completed = job_monitor.get_jobs_by_status('COMPLETE')
print('complete jobs:', len(completed))

# 列印報表
print(job_monitor.generate_status_report())
```

已解決的問題（背景）

- 原本 pipeline 觀察到 compile/job 統計為 0 的情況，原因是 SDK 回傳的狀態字串有許多變體（例如 `Results Ready`, `SUCCEEDED`, `completed`, `Succeeded`），導致嚴格相等比較失敗。模組現在做了正規化與分組，統計數字已回復正確。

故障排除與注意事項

- 當使用不同 Provider/SDK（或不同 onnxruntime provider）時，job state 字串可能仍會出現新變體，若出現新的未識別狀態，會在日誌中列出並以 `UNKNOWN` 分組；建議把新狀態加入 mapping。
- 測試化建議：建立單元測試（模擬多種 SDK 回傳字串）驗證 `update_job_status` 能正確分組。

後續改進建議

- 增加自動化測試：針對常見字串（多語系/大小寫/前綴後綴）做 data-driven unit tests。
- 支援持久化：若希望跨過程追蹤 job（process crash / reboot），可選擇把 job 狀態序列化到輕量 DB（SQLite / tinydb）或 JSON file。
- Dashboard 整合：將 `generate_status_report` 的輸出格式轉為 JSON API，便於 web UI 或監控系統取用。

對應產物與位置

- 參考檔案：`src/qaihub_optimize/modules/job_monitor.py`（實際程式碼）
- 文檔（本檔）：`src/qaihub_optimize/modules/job_monitor.md`

需求覆蓋檢核（簡短）

- 正規化 job 狀態以避免計數誤差 — 已完成。
- 提供查詢/回報函式以供 pipeline 使用 — 已完成。
- 日誌與未識別狀態提示 — 已完成。

若要我接著做

- (A) 新增對常見 SDK 狀態字串的 unit tests 並執行測試。 
- (B) 把 `generate_status_report` 換成 JSON API 並新增一個簡單的 HTTP endpoint（Flask / FastAPI）供 Dashboard 使用。
- (C) 將 job 狀態寫入 SQLite 以支援 process 重啟後的持久化。 

請回覆要接續哪一項（A/B/C）或只保留本檔案並結束。
