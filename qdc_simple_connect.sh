#!/bin/bash
# 簡化版 QDC 連接腳本 - 根據用戶提供的命令格式

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐉 Dragon X Fall Detection System${NC}"
echo -e "${BLUE}簡化版 QDC 連接腳本${NC}"
echo "================================="

# 設置常量
SSH_KEY="qdc_id_2025-8-11_62.pem"
QDC_SSH_HOST="ssh.qdc.qualcomm.com"
QDC_TUNNEL_USER="sshtunnel"
QDC_DEVICE_HOST="sa296826.sa.svc.cluster.local"  # 用戶提供的設備主機名
LOCAL_PORT=2222
REMOTE_PORT=22
QDC_DEVICE_USER="hcktest"

# 檢查SSH密鑰
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}❌ SSH密鑰文件不存在: $SSH_KEY${NC}"
    echo "請確保SSH密鑰在當前目錄中"
    exit 1
fi

# 設置SSH密鑰權限
chmod 600 "$SSH_KEY"
echo -e "${GREEN}✅ SSH密鑰權限設置完成${NC}"

# 檢查端口是否已被佔用
if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️ 端口 $LOCAL_PORT 已被使用，終止現有連接...${NC}"
    kill $(lsof -ti:$LOCAL_PORT) 2>/dev/null
    sleep 2
fi

# 啟動SSH隧道 - 按照用戶提供的格式
echo -e "${YELLOW}🔄 設置SSH隧道到QDC...${NC}"
echo -e "${YELLOW}使用命令: ssh -i $SSH_KEY -L $LOCAL_PORT:$QDC_DEVICE_HOST:$REMOTE_PORT -N $QDC_TUNNEL_USER@$QDC_SSH_HOST${NC}"

# 啟動SSH隧道在後台
ssh -i "$SSH_KEY" -L $LOCAL_PORT:$QDC_DEVICE_HOST:$REMOTE_PORT -N $QDC_TUNNEL_USER@$QDC_SSH_HOST -f

# 檢查隧道是否成功建立
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SSH隧道成功在背景建立${NC}"
    
    # 等待隧道完全啟動
    sleep 2
    
    echo -e "${YELLOW}🔹 您現在可以使用以下命令連接到QDC設備:${NC}"
    echo -e "  ssh -i $SSH_KEY -o StrictHostKeychecking=no -o UserKnownHostsFile=/dev/null -p $LOCAL_PORT $QDC_DEVICE_USER@localhost"
    
    # 提供停止隧道的說明
    echo -e "${YELLOW}🔹 需要停止隧道時，請運行:${NC}"
    echo -e "  kill \$(lsof -ti:$LOCAL_PORT)"
    
    # 詢問是否要立即連接
    read -p "是否立即連接到設備? (y/n): " CONNECT_NOW
    if [[ $CONNECT_NOW == "y" || $CONNECT_NOW == "Y" ]]; then
        echo -e "${BLUE}連接到設備...${NC}"
        ssh -i "$SSH_KEY" -o StrictHostKeychecking=no -o UserKnownHostsFile=/dev/null -p $LOCAL_PORT $QDC_DEVICE_USER@localhost
    fi
else
    echo -e "${RED}❌ SSH隧道建立失敗${NC}"
    exit 1
fi
