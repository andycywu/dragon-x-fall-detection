#!/bin/bash
# 自動啟動 .venv_mediapipe 虛擬環境的腳本

# 項目根目錄
PROJECT_ROOT="/Users/andycyw/mvp_fall_detection_starter"

# 檢查是否在項目目錄中
if [[ "$PWD" == "$PROJECT_ROOT" ]]; then
    # 檢查虛擬環境是否存在
    if [[ -d "$PROJECT_ROOT/.venv_mediapipe" ]]; then
        # 檢查是否已經啟動虛擬環境
        if [[ "$VIRTUAL_ENV" != "$PROJECT_ROOT/.venv_mediapipe" ]]; then
            echo "🚀 正在啟動 MediaPipe 虛擬環境..."
            source "$PROJECT_ROOT/.venv_mediapipe/bin/activate"
            echo "✅ MediaPipe 虛擬環境已啟動"
            echo "📦 Python 版本: $(python --version)"
            echo "📍 虛擬環境路徑: $VIRTUAL_ENV"
        fi
    else
        echo "❌ MediaPipe 虛擬環境不存在，請先創建："
        echo "   python3.11 -m venv .venv_mediapipe"
    fi
fi
