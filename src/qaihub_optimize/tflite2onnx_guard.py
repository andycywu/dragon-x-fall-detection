import os
import re
import sys
import json
import csv
import subprocess
from pathlib import Path
from typing import Dict, List

# -----------------------------
# [A] TFLite 基本分析（無外部依賴版）
# -----------------------------
def _read_bytes(path: Path) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def analyze_tflite(path: str) -> Dict:
    """
    啟發式分析：偵測是否 fp16、是否含 Select TF Ops / Flex / 自訂 op。
    若環境有 tflite-support 或 flatbuffers schema，可擴充為更精準解析。
    """
    p = Path(path)
    data = _read_bytes(p)

    def contains_any(markers: List[bytes]) -> bool:
        return any(m in data for m in markers)

    is_fp16 = contains_any([b"Float16", b"FLOAT16"])
    has_flex = contains_any([b"Flex", b"FLEX"])
    has_select_tf_ops = contains_any([b"SELECT_TF_OPS", b"SelectTensorFlowOps"])
    has_delegate_or_custom = contains_any([b"DELEGATE", b"Custom", b"custom", b"XNNPACK", b"GPUDelegate"])

    flags = []
    if is_fp16:
        flags.append("fp16")
    if has_select_tf_ops:
        flags.append("select_tf_ops")
    if has_flex:
        flags.append("flex_ops")
    if has_delegate_or_custom:
        flags.append("custom_or_delegate")

    return {
        "path": str(p),
        "is_fp16": is_fp16,
        "has_select_tf_ops": has_select_tf_ops,
        "has_flex": has_flex,
        "has_delegate_or_custom": has_delegate_or_custom,
        "flags": flags
    }

# -----------------------------
# [B] 轉換執行封裝（預設用 tflite2onnx）
# -----------------------------
def _run_tflite2onnx(tflite_path: str, onnx_path: str, timeout_sec: int = 600):
    cmd = [
        sys.executable, "-m", "tflite2onnx",
        "--tflite_path", tflite_path,
        "--onnx_path", onnx_path
    ]
    cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
    ok = (cp.returncode == 0) and Path(onnx_path).exists()
    return ok, (cp.stdout or "") + "\n" + (cp.stderr or "")

# -----------------------------
# [C] 錯誤歸因（把雜亂訊息 → 清楚根因 + 建議）
# -----------------------------
_ERROR_RULES = [
    {
        "name": "fp16_dtype_not_supported",
        "pattern": r"(?i)(float16|fp16).*(not\s+supported|unsupported|cannot|fail)",
        "root_cause": "模型包含 float16，轉換器/某些算子對 fp16 支援不足。",
        "suggestions": [
            "先將 TFLite 從 float16 上拋為 float32（fp16→fp32 再轉 ONNX）。",
            "或改走能直接吃 TFLite 的部署路徑（如 QNN/AI Hub）。"
        ],
        "severity": "high"
    },
    {
        "name": "select_tf_ops_or_flex",
        "pattern": r"(?i)(select[_ ]?tf[_ ]?ops|flex).*?(not\s+supported|unsupported|cannot|fail)",
        "root_cause": "模型含 Select TF Ops / Flex 自訂算子，ONNX 映射缺失。",
        "suggestions": [
            "嘗試 onnxruntime-extensions 或手寫對應的自訂 kernel。",
            "調整前後處理/改寫子圖以避開該算子。",
            "或優先在能吃 TFLite 的引擎上部署。"
        ],
        "severity": "high"
    },
    {
        "name": "resize_or_shape_inference",
        "pattern": r"(?i)(resize|nearest|bilinear|shape inference|dim).*(fail|error|mismatch)",
        "root_cause": "圖像 resize/shape 推導不一致（常與精度或子圖重寫相關）。",
        "suggestions": [
            "在轉換前固定輸入尺寸，或將動態維度改為靜態。",
            "將該子圖替換為可被 ONNX 正確推導的等價實現。"
        ],
        "severity": "medium"
    },
    {
        "name": "unknown_custom_op",
        "pattern": r"(?i)(custom op|unknown op|unsupported op|delegate)",
        "root_cause": "出現轉換器不識別的自訂/委派算子。",
        "suggestions": [
            "檢查該算子是否有對應的 ONNX 等價子圖或 extensions。",
            "調整前處理/後處理以避開該算子。",
            "尋找社群已 patch 的對應 ONNX 模型。"
        ],
        "severity": "high"
    },
]

def _classify_error(stderr_stdout: str, pre_analysis_flags: List[str]) -> Dict:
    text = stderr_stdout or ""
    for rule in _ERROR_RULES:
        if re.search(rule["pattern"], text):
            return {
                "root_cause": rule["root_cause"],
                "suggestions": rule["suggestions"],
                "matched_rule": rule["name"]
            }
    if "fp16" in pre_analysis_flags:
        return {
            "root_cause": "模型為 float16，且轉換器訊息未明確指出原因，但 fp16 常為主因。",
            "suggestions": [
                "嘗試先將模型上拋為 float32 再轉換。",
                "若仍失敗，檢查是否還有 Select TF Ops / Flex / 自訂算子。"
            ],
            "matched_rule": "heuristic_fp16"
        }
    if any(f in pre_analysis_flags for f in ["select_tf_ops", "flex_ops", "custom_or_delegate"]):
        return {
            "root_cause": "模型包含 Select TF Ops / Flex 或其他自訂/委派算子，ONNX 映射缺失的機率高。",
            "suggestions": [
                "嘗試 onnxruntime-extensions 或改寫子圖。",
                "或尋找社群已有的 ONNX patch 版本。"
            ],
            "matched_rule": "heuristic_custom"
        }
    return {
        "root_cause": "轉換器回報一般性錯誤，需人工檢視日誌與模型結構。",
        "suggestions": [
            "檢查轉換日誌、逐步縮小子圖定位問題算子。",
            "若模型來自 MediaPipe，優先嘗試 TFLite 原生部署（QNN/AI Hub）避開轉換。"
        ],
        "matched_rule": "unknown"
    }

# -----------------------------
# [D] 封裝主入口
# -----------------------------
def convert_with_diagnostics(
    tflite_path: str,
    onnx_out_dir: str,
    timeout_sec: int = 600,
    force_overwrite: bool = False
) -> Dict:
    tflite_path = str(tflite_path)
    onnx_out_dir = Path(onnx_out_dir)
    onnx_out_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = onnx_out_dir / (Path(tflite_path).stem + ".onnx")

    pre = analyze_tflite(tflite_path)
    detected_flags = pre["flags"][:]

    if onnx_path.exists() and not force_overwrite:
        return {
            "status": "ok",
            "onnx_path": str(onnx_path),
            "detected_flags": detected_flags,
            "note": "已存在同名 ONNX，跳過轉換（force_overwrite=False）。"
        }

    ok, log = _run_tflite2onnx(tflite_path, str(onnx_path), timeout_sec=timeout_sec)

    if ok:
        return {
            "status": "ok",
            "onnx_path": str(onnx_path),
            "detected_flags": detected_flags,
            "note": "轉換成功"
        }

    cause = _classify_error(log, detected_flags)
    human_message = _format_human_message(Path(tflite_path).name, detected_flags, cause, log)

    return {
        "status": "fail",
        "detected_flags": detected_flags,
        "root_cause": cause["root_cause"],
        "suggestions": cause["suggestions"],
        "matched_rule": cause["matched_rule"],
        "converter_log_tail": _tail(log, 1200),
        "human_message": human_message
    }

# -----------------------------
# [E] UI 友善字串
# -----------------------------
def _format_human_message(model_name: str, flags: List[str], cause: Dict, log: str) -> str:
    flag_map = {
        "fp16": "模型為 float16",
        "select_tf_ops": "含 Select TF Ops",
        "flex_ops": "含 Flex 算子",
        "custom_or_delegate": "含自訂/委派算子"
    }
    readable_flags = [flag_map.get(f, f) for f in flags]
    parts = []
    parts.append(f"模型：{model_name}")
    if readable_flags:
        parts.append("偵測到的風險：" + "、".join(readable_flags))
    parts.append("關鍵問題：" + cause["root_cause"])
    parts.append("建議：")
    for s in cause["suggestions"]:
        parts.append(f" - {s}")
    return "\n".join(parts)

def _tail(s: str, n: int) -> str:
    s = s or ""
    if len(s) <= n:
        return s
    return s[-n:]

# -----------------------------
# [F]（可選）批次處理 + 報表
# -----------------------------
def batch_convert(
    in_dir: str,
    out_dir: str,
    report_csv: str = "convert_report.csv",
    fail_csv: str = "fail_list.csv",
    timeout_sec: int = 600
):
    in_dir = Path(in_dir)
    out_dir = Path(out_dir)
    rows = []
    fails = []

    for p in sorted(in_dir.rglob("*.tflite")):
        r = convert_with_diagnostics(str(p), str(out_dir), timeout_sec=timeout_sec)
        if r["status"] == "ok":
            rows.append([str(p), ";".join(r.get("detected_flags", [])), "ok", r.get("onnx_path", ""), r.get("note", "")])
        else:
            rows.append([str(p), ";".join(r.get("detected_flags", [])), "fail", "", r.get("root_cause", "")])
            fails.append([
                str(p),
                ";".join(r.get("detected_flags", [])),
                r.get("root_cause", ""),
                " | ".join(r.get("suggestions", []))
            ])

    with open(report_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "flags", "status", "onnx_path", "note_or_root_cause"])
        w.writerows(rows)

    with open(fail_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "flags", "root_cause", "suggestions"])
        w.writerows(fails)

# -----------------------------
# [G] 自動 fp16 上拋再轉換
# -----------------------------
def convert_auto_with_upcast(
    tflite_path: str,
    onnx_out_dir: str,
    timeout_sec: int = 600,
    force_overwrite: bool = False
) -> dict:
    """
    先嘗試直接轉換，若失敗且偵測到 fp16，則自動上拋 fp32 再重試一次。
    """
    from fp16_to_fp32_upcast import hook_fp16_to_fp32
    r = convert_with_diagnostics(tflite_path, onnx_out_dir, timeout_sec=timeout_sec, force_overwrite=force_overwrite)
    if r["status"] == "ok":
        return r
    if "fp16" in r.get("detected_flags", []):
        fp32_path = hook_fp16_to_fp32(tflite_path)
        r2 = convert_with_diagnostics(fp32_path, onnx_out_dir, timeout_sec=timeout_sec, force_overwrite=True)
        if r2["status"] == "ok":
            r2["note"] = "先上拋 fp32 後成功轉換"
            return r2
    return r
