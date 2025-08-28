跌倒判定邏輯與 Sidebar 參數說明

本專案的跌倒判定混合了姿態/角度計算與模型（ONNX 或 MediaPipe-derived keypoints）的機率估計，最後由 `FusionTrigger` 以簡單融合邏輯判定是否要產生警報（並受 cooldown 控制以避免重複警報）。下列說明會幫助你理解側欄參數如何影響偵測。

判定流程（簡述）
1. 每一幀影像會由 ONNX 模型（若已載入）嘗試推論，若模型輸出 keypoints 或 scalar prob 則優先使用；否則使用 MediaPipe 取得 pose_landmarks。
2. 從 keypoints 或 pose_landmarks 計算軀幹（torso）角度（以肩膀與臀部中點向量與垂直向量間的夾角表示）。
3. 計算 frame-level 的置信度（confidence）：當 keypoints 含 confidence 欄位時會使用平均 confidence，否則以 1.0 當作保守值。
4. 以角度與 confidence 合成一個 risk score（範例：risk = (angle / 180) * confidence），若模型回傳 scalar prob 則會使用該 prob 當作 risk score 的主要來源。
5. Sway（擺動）是基於最近 N 幀角度的標準差（std），會經過 normalization（see 下方）後作為另一個指標。
6. 最後由 `FusionTrigger.should_trigger_alert`（目前簡單判斷：若 fall_detected 或 help_detected 且不在 cooldown 期間則回傳 true）來決定是否觸發警報；`fall_detected` 是基於目前 frame 的 risk 與角度阈值計算而來。

側欄參數（解釋）
- Sway window (frames)
  - 說明：在計算擺動（Sway）分數時會使用最近多少幀的角度資料。預設 8 表示使用最近 8 幀。
  - 影響：較大的視窗會使得 Sway 評估更加平滑（對短暫抖動不敏感），但也增加反應延遲。較小視窗則更敏感。

- Sway normalization (deg)
  - 說明：用來把角度標準差（degree）轉換為 0..1 的尺度。計算方式為 std(angle_window) / Sway normalization，然後 clamp 到 [0,1]。
  - 影響：越大的 normalization 會讓相同角度變化對 Sway 分數的影響越小。

- Sway alert threshold (0..1)
  - 說明：當 Sway 分數（經 normalization）超過此閾值時，系統會認為該情況具有更高風險（可作為輔助條件或融合條件）。
  - 影響：提高閾值會減少基於擺動的誤報；降低閾值會更容易把短暫大幅擺動視為高風險。

- Chart metric
  - 選項：'Risk score'、'Sway score'、'Both'
  - 說明：決定右側圖表顯示的數據；Risk score 是模型/角度合成的危險度，Sway score 是角度擺動標準差的 normalized 值。

- Chart history (points)
  - 說明：圖表中顯示的歷史點數（最多 N 個），影響圖表橫軸長度。

影像/模型原始輸出（debug）
- 在 Streamlit demo 中，可透過側欄勾選「Show raw model outputs (debug)」來顯示模型 raw 輸出（ONNX raw）與 adapter summary。預設為隱藏以避免干擾畫面。

進階說明
- 如果需要將 model prob、angle-based risk 與 sway 做更精細的融合，可把 `FusionTrigger` 擴充為接受權重參數（例如 w_model, w_angle, w_sway），我可以協助把該參數加入 sidebar 並替換目前的簡單判斷邏輯。
