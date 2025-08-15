#!/bin/bash
# macOS ARM64 (Apple Silicon) 專用安裝腳本 - 修復版
# 修復了依賴衝突問題

echo "🍎 Dragon X Fall Detection - Apple Silicon 專用安裝 (修復版)"
echo "===================================================="

# 檢查是否為 macOS
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "❌ 此腳本僅適用於 macOS。"
    exit 1
fi

# 檢查是否為 ARM64 架構
if [[ "$(uname -m)" != "arm64" ]]; then
    echo "❌ 此腳本僅適用於 Apple Silicon (ARM64) Mac。"
    exit 1
fi

# 確保使用 Python 3
PYTHON_CMD="python3"

# 檢查 Python 環境
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ 找不到 Python 3，請安裝後再試。"
    echo "建議使用 Homebrew 安裝: brew install python@3.11"
    exit 1
fi

# 顯示環境信息
echo "📊 環境信息:"
echo "macOS 版本: $(sw_vers -productVersion)"
echo "處理器: Apple Silicon ($(uname -m))"
echo "Python: $($PYTHON_CMD --version)"

# 檢查虛擬環境
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "⚠️ 未檢測到虛擬環境。強烈建議使用虛擬環境安裝依賴。"
    echo "要創建虛擬環境，請運行: python3 -m venv .venv_dragon_x"
    echo "然後啟動環境: source .venv_dragon_x/bin/activate"
    
    read -p "要繼續安裝嗎？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 安裝已取消。"
        exit 1
    fi
else
    echo "✅ 使用虛擬環境: $VIRTUAL_ENV"
fi

# 安裝基本 Python 工具
echo "🔧 更新基本 Python 工具..."
$PYTHON_CMD -m pip install --upgrade pip setuptools wheel

# 安裝兼容版本的 NumPy (1.26.0)
echo "🧮 安裝兼容版本的 NumPy (1.26.0)..."
$PYTHON_CMD -m pip install numpy==1.26.0 --prefer-binary

# 安裝 ONNX Runtime 和 CoreML 加速器
echo "🧠 安裝 ONNX Runtime..."
$PYTHON_CMD -m pip install onnxruntime==1.18.0 --prefer-binary

# 安裝 PyTorch (Apple Silicon 原生版本)
echo "🔥 安裝 PyTorch (Apple Silicon 原生版本)..."
$PYTHON_CMD -m pip install torch torchvision --prefer-binary

# 安裝 MediaPipe
echo "👁️ 安裝 MediaPipe..."
$PYTHON_CMD -m pip install mediapipe==0.10.14 --prefer-binary

# 安裝 Protobuf 3.20.3 (兼容版本)
echo "📦 安裝 Protobuf 3.20.3 (兼容版本)..."
$PYTHON_CMD -m pip install protobuf==3.20.3 --prefer-binary

# 安裝 QAI Hub
echo "🌐 安裝 QAI Hub..."
$PYTHON_CMD -m pip install qai-hub==0.9.0 --prefer-binary

# 安裝基本計算機視覺庫
echo "📸 安裝計算機視覺庫..."
$PYTHON_CMD -m pip install opencv-python-headless==4.10.0.84 Pillow==9.5.0 scipy==1.10.1 --prefer-binary

# 安裝其他重要依賴
echo "🔌 安裝其他關鍵依賴..."
$PYTHON_CMD -m pip install matplotlib==3.7.1 pandas==1.5.3 streamlit==1.28.0 requests==2.28.2 --prefer-binary

# 設置 QAI Hub
echo "🔑 設置 QAI Hub..."
chmod +x setup_qai_hub_fixed.py
$PYTHON_CMD setup_qai_hub_fixed.py

# 檢查安裝
echo "🧪 檢查安裝..."

# 檢查 NumPy 和 ONNX Runtime
echo "檢查 NumPy 和 ONNX Runtime..."
$PYTHON_CMD -c "
import sys
import numpy as np
print(f'Python {sys.version}')
print(f'NumPy {np.__version__}')

try:
    import onnxruntime as ort
    print(f'ONNX Runtime {ort.__version__}')
    print(f'可用提供者: {ort.get_available_providers()}')
except ImportError:
    print('❌ ONNX Runtime 未安裝')
"

# 檢查 PyTorch
echo "檢查 PyTorch..."
$PYTHON_CMD -c "
try:
    import torch
    print(f'PyTorch {torch.__version__}')
    print(f'MPS (Metal) 可用: {torch.backends.mps.is_available()}')
except ImportError:
    print('❌ PyTorch 未安裝')
"

# 檢查 QAI Hub
echo "檢查 QAI Hub 配置..."
$PYTHON_CMD -c "
import os
from pathlib import Path
config_path = os.path.join(str(Path.home()), '.qai_hub', 'client.ini')
if os.path.exists(config_path):
    print(f'✅ QAI Hub 配置文件存在: {config_path}')
    with open(config_path, 'r') as f:
        content = f.read()
        if 'api_token' in content:
            print('✅ QAI Hub API Token 已設置')
else:
    print(f'❌ QAI Hub 配置文件不存在: {config_path}')
"

echo "✨ 安裝完成！您現在可以開始使用 Dragon X Fall Detection 系統。"
echo "注意：某些依賴關係已被優化以解決衝突。如果您需要運行特定模塊，可能需要額外安裝相關依賴。"
