#!/bin/bash
# Qualcomm Device Cloud SSH連接和部署腳本

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
Pecho ✅ 部署完成！
echchmod +x device_cloud_deploy.bat

# 上傳部署腳本到Device Cloud
echo -e "${YELLOW}� 上傳部署腳本到Device Cloud...${NC}"
scp -i "$SSH_KEY_PATH" -P $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null device_cloud_deploy.bat $USERNAME@localhost:C:/Users/$USERNAME/

# 將.env配置文件上傳（重要的環境配置）
if [ -f ".env" ]; then
    echo -e "${YELLOW}� 上傳環境配置文件...${NC}"
    scp -i "$SSH_KEY_PATH" -P $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null .env $USERNAME@localhost:C:/Users/$USERNAME/
else
    echo -e "${YELLOW}⚠️ .env文件不存在，環境變量可能需要手動設置${NC}"
fiROJ_DIR%
echo � 可以執行以下命令測試:
echo    cd %PROJ_DIR%
echo    python unified_ai_detector.py
echo    python dragon_x_fall_detection_system.py
echo    python hackathon_final_demo.py
EOL033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🐉 Dragon X Fall Detection System${NC}"
echo -e "${CYAN}Qualcomm Device Cloud 部署腳本${NC}"
echo "=============================================="

# 檢查SSH密鑰
if [ ! -f "qdc_id_2025-8-11_62.pem" ]; then
    echo -e "${RED}❌ SSH密鑰文件不存在: qdc_id_2025-8-11_62.pem${NC}"
    echo "請確保SSH密鑰在當前目錄中"
    exit 1
fi

# 設置SSH密鑰權限
chmod 600 qdc_id_2025-8-11_62.pem
echo -e "${GREEN}✅ SSH密鑰權限設置完成${NC}"

# 設置QDC隧道常量
QDC_SSH_HOST="ssh.qdc.qualcomm.com"
QDC_TUNNEL_USER="sshtunnel"
QDC_DEVICE_HOST="sa296481.sa.svc.cluster.local"
LOCAL_PORT=2222
REMOTE_PORT=22

# 獲取本地設備資訊
echo -e "${YELLOW}📋 設備資訊設置:${NC}"
read -p "用戶名 (默認: hcktest): " USERNAME
USERNAME=${USERNAME:-hcktest}
SSH_KEY_PATH="$(pwd)/qdc_id_2025-8-11_62.pem"

echo -e "${BLUE}🔗 連接信息:${NC}"
echo "   QDC隧道主機: $QDC_SSH_HOST"
echo "   目標設備: $QDC_DEVICE_HOST"
echo "   本地埠: $LOCAL_PORT"
echo "   用戶名: $USERNAME"
echo "   SSH密鑰: $SSH_KEY_PATH"

# 測試SSH隧道連接
echo -e "${YELLOW}🔍 設置SSH隧道...${NC}"
echo -e "${CYAN}⚠️ 重要提示: 此連接將在背景運行。如需停止，請使用 'kill \$(lsof -ti:$LOCAL_PORT)'${NC}"
echo -e "${YELLOW}🔄 設置SSH隧道到QDC: $QDC_SSH_HOST -> $QDC_DEVICE_HOST${NC}"

# 啟動SSH隧道
ssh -i "$SSH_KEY_PATH" -L $LOCAL_PORT:$QDC_DEVICE_HOST:$REMOTE_PORT -N $QDC_TUNNEL_USER@$QDC_SSH_HOST -o ConnectTimeout=10 -o StrictHostKeyChecking=no -f

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SSH隧道建立成功${NC}"
    # 等待隧道完全啟動
    sleep 3
    
    # 測試隧道連接
    ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost "echo 'SSH連接成功'" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 通過隧道的SSH連接測試成功${NC}"
    else
        echo -e "${RED}❌ 通過隧道的SSH連接失敗，請檢查設置${NC}"
        echo "正在清理隧道..."
        kill $(lsof -ti:$LOCAL_PORT) 2>/dev/null
        exit 1
    fi
else
    echo -e "${RED}❌ SSH隧道建立失敗${NC}"
    exit 1
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SSH連接測試成功${NC}"
else
    echo -e "${RED}❌ SSH連接失敗，請檢查網絡和設備狀態${NC}"
    exit 1
fi

# 創建部署腳本
echo -e "${YELLOW}📦 創建部署腳本...${NC}"

cat > device_cloud_deploy.bat << 'EOL'
@echo off
REM Device Cloud Windows部署腳本

echo 🐉 在Device Cloud上部署Dragon X Fall Detection System
echo ==================================================

REM 創建項目目錄
set PROJ_DIR=C:\dragon_x_fall_detection
if not exist %PROJ_DIR% mkdir %PROJ_DIR%
cd /d %PROJ_DIR%

REM 檢查Git是否已安裝
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 安裝Git...請手動安裝Git後重試
    exit /b 1
)

REM 設置GitHub倉庫URL
set GITHUB_REPO=https://github.com/andycywu/dragon-x-fall-detection.git
echo 🌐 使用GitHub倉庫: %GITHUB_REPO%

REM 克隆或更新倉庫
if exist .git (
    echo 🔄 更新現有倉庫...
    git pull origin main
) else (
    echo 📥 克隆GitHub倉庫...
    git clone %GITHUB_REPO% .
)

REM 檢查Python環境
echo 🐍 檢查Python環境...
python --version

REM 運行設置腳本
if exist device_cloud_setup.py (
    echo 🚀 運行設置腳本...
    python device_cloud_setup.py
) else (
    echo ⚠️ 設置腳本不存在
)

echo "✅ 部署完成！"
echo "📋 項目位置: $PROJ_DIR"
echo "� 可以執行以下命令測試:"
echo "   cd $PROJ_DIR"
echo "   python3 unified_ai_detector.py"
echo "   python3 dragon_x_fall_detection_system.py"
echo "   python3 hackathon_final_demo.py"
EOL

chmod +x device_cloud_deploy.sh

# 上傳部署腳本到Device Cloud
echo -e "${YELLOW}� 上傳部署腳本到Device Cloud...${NC}"
scp -i "$SSH_KEY_PATH" -P $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null device_cloud_deploy.sh $USERNAME@localhost:/tmp/

# 將.env配置文件上傳（重要的環境配置）
if [ -f ".env" ]; then
    echo -e "${YELLOW}� 上傳環境配置文件...${NC}"
    scp -i "$SSH_KEY_PATH" -P $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null .env $USERNAME@localhost:/tmp/
else
    echo -e "${YELLOW}⚠️ .env文件不存在，環境變量可能需要手動設置${NC}"
fi

# 執行遠程部署
echo -e "${YELLOW}🚀 執行遠程部署...${NC}"
ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost << 'REMOTE_SCRIPT'

echo "🐉 在Device Cloud設備上開始部署..."

# 創建項目目錄
PROJ_DIR="/opt/dragon_x_fall_detection"
sudo mkdir -p $PROJ_DIR
cd $PROJ_DIR

# 移動上傳的腳本和配置
echo "📁 準備部署腳本..."
sudo mv /tmp/device_cloud_deploy.sh . 2>/dev/null
sudo mv /tmp/.env . 2>/dev/null 2>/dev/null

# 設置權限
sudo chmod +x *.sh 2>/dev/null

# 執行部署腳本
echo "🚀 執行部署腳本..."
sudo ./device_cloud_deploy.sh

echo "✅ GitHub部署流程設置完成！"
echo "📋 項目將從GitHub倉庫直接拉取"
echo "� 後續更新只需執行 'git pull' 即可"

REMOTE_SCRIPT

echo -e "${GREEN}🎉 Device Cloud部署完成！${NC}"
echo "=============================================="
echo -e "${CYAN}📋 接下來可以:${NC}"
echo "1. SSH連接到設備:"
echo "   ssh -i $SSH_KEY_PATH -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost"
echo ""
echo "2. 進入項目目錄:"
echo "   cd /opt/dragon_x_fall_detection"
echo ""
echo "3. 運行AI檢測系統:"
echo "   python3 unified_ai_detector.py"
echo "   python3 dragon_x_fall_detection_system.py"
echo "   python3 hackathon_final_demo.py"
echo ""
echo "4. 更新系統 (當GitHub有新變更時):"
echo "   cd /opt/dragon_x_fall_detection && git pull"
echo ""
echo "5. 停止SSH隧道:"
echo "   kill \$(lsof -ti:$LOCAL_PORT)"
echo ""
echo -e "${GREEN}🐉 準備在Snapdragon X Elite上測試你的AI系統！${NC}"
