#!/bin/bash
# Qualcomm Device Cloud SSH連接腳本

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🐉 Dragon X Fall Detection System${NC}"
echo -e "${CYAN}Qualcomm Device Cloud 連接腳本${NC}"
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

# 檢查現有隧道並關閉
echo -e "${YELLOW}🔍 檢查現有隧道...${NC}"
if lsof -ti:$LOCAL_PORT > /dev/null; then
    echo -e "${YELLOW}⚠️ 關閉現有隧道...${NC}"
    kill $(lsof -ti:$LOCAL_PORT)
    sleep 2
fi

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

echo -e "${GREEN}🎉 SSH隧道已建立！${NC}"
echo "=============================================="
echo -e "${CYAN}📋 接下來可以:${NC}"
echo "1. SSH連接到設備:"
echo "   ssh -i $SSH_KEY_PATH -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost"
echo ""
echo "2. 上傳Git安裝腳本:"
echo "   scp -i $SSH_KEY_PATH -P $LOCAL_PORT -o StrictHostKeyChecking=no git_installer.bat $USERNAME@localhost:C:/Users/$USERNAME/"
echo ""
echo "3. 上傳部署腳本:"
echo "   scp -i $SSH_KEY_PATH -P $LOCAL_PORT -o StrictHostKeyChecking=no deploy_github.bat $USERNAME@localhost:C:/Users/$USERNAME/"
echo ""
echo "4. 運行Git安裝腳本:"
echo "   ssh -i $SSH_KEY_PATH -p $LOCAL_PORT -o StrictHostKeyChecking=no $USERNAME@localhost \"cd C:/Users/$USERNAME/ && git_installer.bat\""
echo ""
echo "5. 運行部署腳本:"
echo "   ssh -i $SSH_KEY_PATH -p $LOCAL_PORT -o StrictHostKeyChecking=no $USERNAME@localhost \"cd C:/Users/$USERNAME/ && deploy_github.bat\""
echo ""
echo "6. 停止SSH隧道:"
echo "   kill \$(lsof -ti:$LOCAL_PORT)"
echo ""
echo -e "${GREEN}🐉 準備在Snapdragon X Elite上測試你的AI系統！${NC}"
