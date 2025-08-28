#!/usr/bin/env bash
# start.sh - macOS / POSIX launcher for infer_demo
# Creates/activates a project-local virtualenv (.venv_infer) and runs the live demo.

# Usage:
#   ./start.sh [--streamlit-args]
#
# Behavior:
# - Ensures a local venv (.venv_infer) exists and installs dependencies from
#   `requirements_inferMac.txt` if not present.
# - Activates the venv and ensures `streamlit` is installed inside it.
# - Launches `src/infer_demo_Mac/live_demo_mac.py` via `streamlit run`, forwarding
#   any additional CLI args to Streamlit.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv_infer"
REQ_FILE="$PROJECT_DIR/requirements_inferMac.txt"
PYTHON_CMD="${PYTHON_CMD:-python3}"

# If a config/default_onnx.txt exists and START_ONNX_MODEL not set, read it
CFG_DEFAULT_MODEL="$PROJECT_DIR/config/default_onnx.txt"
if [ -z "${START_ONNX_MODEL:-}" ] && [ -f "$CFG_DEFAULT_MODEL" ]; then
  val=$(cat "$CFG_DEFAULT_MODEL" | tr -d '\r' | sed -e 's/^\s*//' -e 's/\s*$//')
  if [ -n "$val" ]; then
    export START_ONNX_MODEL="$val"
  fi
fi

echo "[infer_demo] project: $PROJECT_DIR"
echo "[infer_demo] python: $PYTHON_CMD"

if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  echo "找不到 $PYTHON_CMD，請先安裝 Python 3.8+。"
  exit 1
fi

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
  echo "建立虛擬環境: $VENV_DIR"
  $PYTHON_CMD -m venv "$VENV_DIR"
  echo "升級 pip, setuptools, wheel..."
  "$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
  if [ -f "$REQ_FILE" ]; then
    echo "安裝 requirements from $REQ_FILE"
    "$VENV_DIR/bin/pip" install -r "$REQ_FILE"
  else
    echo "找不到需求檔 $REQ_FILE，請確認路徑。"
  fi
else
  echo "虛擬環境已存在: $VENV_DIR"
fi

# Activate venv
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# Ensure streamlit is available
if ! command -v streamlit >/dev/null 2>&1; then
  echo "在虛擬環境中找不到 streamlit，嘗試安裝..."
  pip install streamlit
fi

LIVE_PY="$PROJECT_DIR/src/infer_demo_Mac/live_demo_mac.py"
if [ ! -f "$LIVE_PY" ]; then
  echo "找不到 $LIVE_PY，請確認 live demo 檔案路徑。"
  exit 1
fi

echo "啟動 live demo... (streamlit run $LIVE_PY)"

# If a START_ONNX_MODEL is provided, run a short smoke test for visibility.
if [ -n "${START_ONNX_MODEL:-}" ]; then
  echo "Running quick ONNX smoke test for default model: ${START_ONNX_MODEL}"
  # run inside the venv's python; do not fail the launcher if test fails
  "$VENV_DIR/bin/python" "$PROJECT_DIR/scripts/onnx_smoke_test.py" "${START_ONNX_MODEL}" || true
fi

# Support optional START_* env vars to prefill demo defaults. These will be
# forwarded to Streamlit after the `--` separator so `live_demo_mac.py` can
# parse them via argparse (see the demo script for accepted flags).
#
# Available env vars:
#   START_CAMERA_ID     -> forwarded as --camera_id
#   START_RESOLUTION    -> forwarded as --resolution (e.g. 640x480)
#   START_NO_DISPLAY    -> if set to '1' forwards --no_display
#   START_ONNX_MODEL    -> forwarded as --onnx_model <path>

STREAMLIT_ARGS=()
if [ -n "${START_CAMERA_ID:-}" ]; then
  STREAMLIT_ARGS+=("--camera_id" "${START_CAMERA_ID}")
fi
if [ -n "${START_RESOLUTION:-}" ]; then
  STREAMLIT_ARGS+=("--resolution" "${START_RESOLUTION}")
fi
if [ "${START_NO_DISPLAY:-0}" = "1" ]; then
  STREAMLIT_ARGS+=("--no_display")
fi
if [ -n "${START_ONNX_MODEL:-}" ]; then
  STREAMLIT_ARGS+=("--onnx_model" "${START_ONNX_MODEL}")
fi

# User-provided args appended after env-derived args. To pass Streamlit-specific
# flags (like --server.port) use the script like:
#   ./start.sh -- --server.port 8502

if [ ${#STREAMLIT_ARGS[@]} -gt 0 ]; then
  echo "Forwarding demo defaults to streamlit: ${STREAMLIT_ARGS[*]}"
  streamlit run "$LIVE_PY" -- "${STREAMLIT_ARGS[@]}" "$@"
else
  streamlit run "$LIVE_PY" -- "$@"
fi
