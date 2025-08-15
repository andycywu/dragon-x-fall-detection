#!/bin/bash
# 安裝 Dragon X Fall Detection 依賴包 (macOS 和 Linux 版本)

echo "🐉 Dragon X Fall Detection System - 環境設置"
echo "==============================================="

# 確保使用 Python 3
PYTHON_CMD="python3"

# 檢查 Python 環境
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ 找不到 Python 3，請安裝後再試。"
    exit 1
fi

# 顯示檢測到的平台信息
echo "📊 系統信息:"
echo "OS: $(uname -s)"
echo "架構: $(uname -m)"
echo "Python: $($PYTHON_CMD --version)"

# 檢查虛擬環境
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "⚠️ 未檢測到虛擬環境。建議使用虛擬環境安裝依賴。"
    read -p "要繼續安裝嗎？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 安裝已取消。請先設置虛擬環境後再試。"
        exit 1
    fi
else
    echo "✅ 使用虛擬環境: $VIRTUAL_ENV"
fi

# 檢查是否為 macOS ARM64 (Apple Silicon)
if [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
    echo "✅ 檢測到 Apple Silicon (ARM64)"
fi

# 執行平台特定安裝腳本
echo "🔧 開始安裝平台優化依賴包..."

# 確保腳本有執行權限
chmod +x install_platform_accelerators.py

# 執行安裝腳本，捕獲錯誤
if ! $PYTHON_CMD install_platform_accelerators.py; then
    echo "⚠️ 安裝過程中發生錯誤，嘗試替代方案..."
    
    # 針對 macOS 的替代安裝方案
    if [[ "$(uname -s)" == "Darwin" ]]; then
        echo "📱 檢測到 macOS，使用替代安裝方法..."
        
        # 安裝基本依賴
        echo "安裝核心依賴..."
        $PYTHON_CMD -m pip install onnxruntime==1.18.0 --prefer-binary
        
        # 針對 Apple Silicon 安裝 CoreML 加速器
        if [[ "$(uname -m)" == "arm64" ]]; then
            echo "安裝 CoreML 加速器 (適用於 Apple Silicon)..."
            $PYTHON_CMD -m pip install onnxruntime-coreml --prefer-binary
            
            echo "安裝 PyTorch (適用於 Apple Silicon)..."
            $PYTHON_CMD -m pip install torch torchvision --prefer-binary
        else
            echo "安裝 PyTorch (適用於 Intel Mac)..."
            $PYTHON_CMD -m pip install torch torchvision --prefer-binary
        fi
        
        # 安裝其他基本依賴
        echo "安裝其他依賴..."
        $PYTHON_CMD -m pip install mediapipe opencv-python-headless Pillow numpy scipy --prefer-binary
        
        # 嘗試安裝剩餘依賴
        echo "安裝剩餘依賴..."
        $PYTHON_CMD -m pip install -r requirements.txt --ignore-installed --prefer-binary || true
    fi
fi

echo "✨ 安裝完成！您現在可以開始使用 Dragon X Fall Detection 系統。"
