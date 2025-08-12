#!/bin/bash
# Device Cloud部署腳本

echo "🐉 在Device Cloud上部署Dragon X Fall Detection System"
echo "=================================================="

# 創建項目目錄
PROJ_DIR="/opt/dragon_x_fall_detection"
sudo mkdir -p $PROJ_DIR
cd $PROJ_DIR

# 檢查Git是否已安裝
if ! command -v git &> /dev/null; then
    echo "📦 安裝Git..."
    sudo apt-get update
    sudo apt-get install -y git
fi

# 設置GitHub倉庫URL
GITHUB_REPO="https://github.com/andycywu/dragon-x-fall-detection.git"
echo "🌐 使用GitHub倉庫: $GITHUB_REPO"

# 克隆或更新倉庫
if [ -d ".git" ]; then
    echo "🔄 更新現有倉庫..."
    git pull origin main
else
    echo "📥 克隆GitHub倉庫..."
    sudo git clone $GITHUB_REPO .
fi

# 檢查Python環境
echo "🐍 檢查Python環境..."
python3 --version

# 檢查Python依賴
echo "📋 安裝/更新Python依賴..."
if [ -f "requirements.txt" ]; then
    sudo pip3 install -r requirements.txt
else
    echo "⚠️ requirements.txt不存在，跳過依賴安裝"
fi

echo "✅ 部署完成！"
echo "📋 項目位置: $PROJ_DIR"
echo "🔹 可以執行以下命令測試:"
echo "   cd $PROJ_DIR"
echo "   python3 dragon_x_core/main.py"
echo "   python3 dragon_x_core/main_compatible.py"
