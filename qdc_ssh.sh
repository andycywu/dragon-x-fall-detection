#!/bin/bash
# QDC (Qualcomm Device Cloud) 快速連接腳本
# 此腳本僅用於快速建立SSH隧道並連接到QDC

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🐉 Dragon X Fall Detection System${NC}"
echo -e "${CYAN}Qualcomm Device Cloud 快速連接腳本${NC}"
echo "=============================================="

# 設置常量
QDC_SSH_HOST="ssh.qdc.qualcomm.com"
QDC_TUNNEL_USER="sshtunnel"
LOCAL_PORT=2222
REMOTE_PORT=22
USERNAME="hcktest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_KEY_PATH="${SCRIPT_DIR}/qdc_id_2025-8-11_62.pem"

# 配置文件
QDC_CONFIG_FILE="${SCRIPT_DIR}/.qdc_config"

# 檢查是否有配置文件
if [ ! -f "$QDC_CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠️ 未找到QDC配置文件，請先運行 qdc_auto_connect.sh${NC}"
    exit 1
fi

# 讀取配置文件中的主機名
QDC_DEVICE_HOST=$(grep "QDC_DEVICE_HOST" "$QDC_CONFIG_FILE" | cut -d'=' -f2)

if [ -z "$QDC_DEVICE_HOST" ]; then
    echo -e "${RED}❌ 無法從配置文件讀取QDC主機名${NC}"
    echo -e "${YELLOW}請運行 qdc_auto_connect.sh 設置主機名${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 使用QDC主機名: $QDC_DEVICE_HOST${NC}"

# 檢查SSH密鑰
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${RED}❌ SSH密鑰文件不存在: $SSH_KEY_PATH${NC}"
    echo "請確保SSH密鑰在當前目錄中"
    exit 1
fi

# 設置SSH密鑰權限
chmod 600 "$SSH_KEY_PATH"

# 檢查是否已有隧道在運行
TUNNEL_PID=$(lsof -ti:$LOCAL_PORT 2>/dev/null)
if [ ! -z "$TUNNEL_PID" ]; then
    echo -e "${GREEN}✅ 已有隧道在運行 (PID: $TUNNEL_PID)${NC}"
else
    echo -e "${YELLOW}🔄 設置SSH隧道...${NC}"
    
    # 啟動SSH隧道
    ssh -i "$SSH_KEY_PATH" -L $LOCAL_PORT:$QDC_DEVICE_HOST:$REMOTE_PORT -N $QDC_TUNNEL_USER@$QDC_SSH_HOST -o ConnectTimeout=10 -o StrictHostKeyChecking=no -f
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ SSH隧道建立成功${NC}"
        # 等待隧道完全啟動
        sleep 2
    else
        echo -e "${RED}❌ SSH隧道建立失敗${NC}"
        exit 1
    fi
fi

# 測試連接並檢查用戶主目錄
echo -e "${YELLOW}🔍 測試連接並檢查用戶環境...${NC}"

# 嘗試檢測操作系統類型
OS_TYPE=$(ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 $USERNAME@localhost "ver" 2>/dev/null)
WINDOWS_OS=0

if [[ "$OS_TYPE" == *"Microsoft Windows"* ]]; then
    echo -e "${BLUE}✅ 檢測到 Windows 操作系統${NC}"
    WINDOWS_OS=1
    # Windows 環境下使用 %USERPROFILE%
    USER_HOME_DIR=$(ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 $USERNAME@localhost "echo %USERPROFILE%" 2>/dev/null)
else
    # 嘗試獲取 Unix/Linux 環境下的 $HOME
    USER_HOME_DIR=$(ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 $USERNAME@localhost "echo \$HOME" 2>/dev/null | tr -d '\r')
fi

# 檢查獲取到的目錄是否有效
if [ -z "$USER_HOME_DIR" ] || [ "$USER_HOME_DIR" = "\$HOME" ] || [ "$USER_HOME_DIR" = "%USERPROFILE%" ]; then
    if [ $WINDOWS_OS -eq 1 ]; then
        echo -e "${YELLOW}⚠️ 無法確定用戶主目錄，使用默認路徑 C:/Users/$USERNAME${NC}"
        USER_HOME_DIR="C:/Users/$USERNAME"
    else
        echo -e "${YELLOW}⚠️ 無法確定用戶主目錄，使用默認路徑 /home/$USERNAME${NC}"
        USER_HOME_DIR="/home/$USERNAME"
    fi
else
    echo -e "${GREEN}✅ 檢測到用戶主目錄: $USER_HOME_DIR${NC}"
fi

# 連接到QDC
echo -e "${YELLOW}🔄 連接到QDC...${NC}"
ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost

# 如果連接失敗或用戶退出，詢問是否要關閉隧道
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️ SSH連接已關閉或失敗${NC}"
else
    echo -e "${GREEN}✅ SSH連接已關閉${NC}"
fi

read -p "是否要關閉SSH隧道？ (y/n): " CLOSE_TUNNEL
if [ "$CLOSE_TUNNEL" = "y" ]; then
    TUNNEL_PID=$(lsof -ti:$LOCAL_PORT 2>/dev/null)
    if [ ! -z "$TUNNEL_PID" ]; then
        kill $TUNNEL_PID
        echo -e "${GREEN}✅ SSH隧道已關閉${NC}"
    else
        echo -e "${YELLOW}⚠️ 沒有運行中的隧道${NC}"
    fi
else
    echo -e "${BLUE}ℹ️ SSH隧道繼續在背景運行${NC}"
    echo -e "${BLUE}ℹ️ 若要手動關閉，請執行: kill \$(lsof -ti:$LOCAL_PORT)${NC}"
fi
