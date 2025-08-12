#!/bin/bash
# 更新版的 Qualcomm Device Cloud 部署腳本

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐉 Dragon X Fall Detection System${NC}"
echo -e "${BLUE}更新版 QDC 部署腳本${NC}"
echo "================================="

# 設置常量
SSH_KEY="qdc_id_2025-8-11_62.pem"
QDC_DEVICE_USER="hcktest"
LOCAL_PORT=2222

# 檢查 SSH 隧道是否已建立
if ! lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}❌ SSH 隧道未建立。請先運行 qdc_connect_updated.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 檢查 SSH 連接...${NC}"
ssh -i "$SSH_KEY" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 $QDC_DEVICE_USER@localhost "echo 連接成功" >/dev/null 2>&1

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ SSH 連接失敗，請確保隧道已正確建立${NC}"
    exit 1
fi

echo -e "${GREEN}✅ SSH 連接正常${NC}"

# 確認設備上的代碼目錄
echo -e "${YELLOW}🔍 檢查目標設備上的代碼目錄...${NC}"
PROJECT_DIR="/opt/dragon_x_fall_detection"

ssh -i "$SSH_KEY" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $QDC_DEVICE_USER@localhost "sudo mkdir -p $PROJECT_DIR && sudo chmod 777 $PROJECT_DIR"

echo -e "${YELLOW}📥 從 GitHub 更新代碼...${NC}"
ssh -i "$SSH_KEY" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $QDC_DEVICE_USER@localhost "cd $PROJECT_DIR && if [ -d .git ]; then git pull; else git clone https://github.com/andycywu/dragon-x-fall-detection.git .; fi"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 代碼更新失敗${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 代碼已更新${NC}"

# 修復跨平台兼容版本
echo -e "${YELLOW}🔧 修復跨平台兼容版本...${NC}"
ssh -i "$SSH_KEY" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $QDC_DEVICE_USER@localhost "cd $PROJECT_DIR/dragon_x_core && chmod +x fix_compatible.sh && ./fix_compatible.sh"

echo -e "${GREEN}✅ 部署完成！您現在可以運行以下命令來執行系統：${NC}"
echo -e "${YELLOW}1. 標準版（適用於 Linux/Unix）:${NC}"
echo -e "   ssh -i $SSH_KEY -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $QDC_DEVICE_USER@localhost \"cd $PROJECT_DIR/dragon_x_core && python3 main.py\""
echo -e "${YELLOW}2. 跨平台兼容版（推薦）:${NC}"
echo -e "   ssh -i $SSH_KEY -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $QDC_DEVICE_USER@localhost \"cd $PROJECT_DIR/dragon_x_core && python3 main_compatible.py\""
echo -e "${YELLOW}3. Windows 版:${NC}"
echo -e "   ssh -i $SSH_KEY -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $QDC_DEVICE_USER@localhost \"cd $PROJECT_DIR/dragon_x_core && python3 main_windows.py\""
