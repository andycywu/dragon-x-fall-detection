#!/bin/bash
# 更新版的 Qualcomm Device Cloud SSH 隧道設置腳本

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐉 Dragon X Fall Detection System${NC}"
echo -e "${BLUE}更新版 QDC SSH 隧道設置${NC}"
echo "================================="

# 設置常量
SSH_KEY="qdc_id_2025-8-11_62.pem"
QDC_SSH_HOST="ssh.qdc.qualcomm.com"
QDC_TUNNEL_USER="sshtunnel"
QDC_DEVICE_HOST="sa296812.sa.svc.cluster.local"  # 使用用戶提供的設備主機名
LOCAL_PORT=2222
REMOTE_PORT=22

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

# 啟動SSH隧道
echo -e "${YELLOW}🔄 設置SSH隧道到QDC: $QDC_SSH_HOST -> $QDC_DEVICE_HOST${NC}"
echo -e "${YELLOW}使用命令: ssh -i $SSH_KEY -L $LOCAL_PORT:$QDC_DEVICE_HOST:$REMOTE_PORT -N $QDC_TUNNEL_USER@$QDC_SSH_HOST${NC}"

# 使用-f選項在背景運行隧道
ssh -i "$SSH_KEY" -L $LOCAL_PORT:$QDC_DEVICE_HOST:$REMOTE_PORT -N $QDC_TUNNEL_USER@$QDC_SSH_HOST -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -f

# 檢查隧道是否成功建立
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SSH隧道成功在背景建立${NC}"
    echo -e "${YELLOW}🔹 使用以下命令可以連接到QDC設備:${NC}"
    echo -e "  ssh -i $SSH_KEY -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null hcktest@localhost"
    echo -e "${YELLOW}🔹 停止隧道:${NC}"
    echo -e "  kill \$(lsof -ti:$LOCAL_PORT)"
else
    echo -e "${RED}❌ SSH隧道建立失敗${NC}"
    exit 1
fi
