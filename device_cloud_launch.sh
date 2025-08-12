#!/bin/bash
# Qualcomm Device Cloud 啟動腳本

echo "=== Dragon X Fall Detection System ==="
echo "=================================="

# 設置環境變量
export QAI_HUB_API_TOKEN="pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 檢測 CPU 架構
echo "=== 檢測系統架構..."
SYSTEM=$(uname -s)
MACHINE=$(uname -m)
echo "系統: $SYSTEM"
echo "架構: $MACHINE"

# 檢查是否是 ARM64
IS_ARM64=0
if [[ "$MACHINE" == "arm64" || "$MACHINE" == "aarch64" ]]; then
    IS_ARM64=1
    echo "=== 檢測到 ARM64 架構，啟用 Snapdragon 優化..."
    export ONNXRUNTIME_PROVIDER_PRIORITY="QNNExecutionProvider,DirectMLExecutionProvider,CPUExecutionProvider"
    export ORT_LOGGING_LEVEL="2"
    OPTIMIZATION_FLAG="--optimize_for_arm64"
else
    echo "=== 未檢測到 ARM64 架構，使用標準配置..."
    OPTIMIZATION_FLAG=""
fi

# 檢查 CPU 信息
echo "=== 硬件狀態檢查:"
if [[ "$SYSTEM" == "Linux" ]]; then
    lscpu | grep -i qualcomm || echo "未檢測到 Qualcomm CPU 信息"
elif [[ "$SYSTEM" == "Darwin" ]]; then
    sysctl -a | grep machdep.cpu.brand_string || echo "未檢測到 CPU 品牌信息"
fi

# 檢查環境狀態
echo "=== 套件狀態檢查:"
python3 -c "import numpy; print('NumPy版本:', numpy.__version__)" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo "NumPy未安裝，請先安裝必要套件"
    exit 1
fi

python3 -c "import cv2; print('OpenCV版本:', cv2.__version__)" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo "OpenCV未安裝，請先安裝必要套件"
    exit 1
fi

# 設置 QAI Hub 認證
echo "=== 設置 QAI Hub 認證..."
python3 setup_qai_hub.py
if [[ $? -ne 0 ]]; then
    echo "!!! QAI Hub 認證設置失敗，但仍將嘗試啟動系統"
fi

# 啟動 AI 檢測系統
echo "=== 啟動 AI 檢測系統..."
python3 unified_ai_detector.py --device snapdragon $OPTIMIZATION_FLAG

# 或者啟動 Dragon X 專用系統
# python3 dragon_x_fall_detection_system.py

echo "=== 系統啟動完成！"
