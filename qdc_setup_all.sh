#!/bin/bash
# QDC (Qualcomm Device Cloud) 一鍵設置腳本
# 此腳本自動完成 QDC 的連接和環境設置

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🐉 Dragon X Fall Detection System${NC}"
echo -e "${CYAN}Qualcomm Device Cloud 一鍵設置腳本${NC}"
echo "=============================================="

# 設置常量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USERNAME="hcktest"
SSH_KEY_PATH="${SCRIPT_DIR}/qdc_id_2025-8-11_62.pem"
LOCAL_PORT=2222

# 檢查 qdc_auto_connect.sh 是否存在
if [ ! -f "${SCRIPT_DIR}/qdc_auto_connect.sh" ]; then
    echo -e "${RED}❌ 連接腳本不存在: ${SCRIPT_DIR}/qdc_auto_connect.sh${NC}"
    echo "請確保連接腳本在當前目錄中"
    exit 1
fi

# 設置執行權限
chmod +x "${SCRIPT_DIR}/qdc_auto_connect.sh"

# 運行連接腳本
echo -e "${YELLOW}🔄 運行 QDC 連接腳本...${NC}"
"${SCRIPT_DIR}/qdc_auto_connect.sh"

# 檢查連接是否成功
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ QDC 連接失敗，無法繼續設置${NC}"
    exit 1
fi

# 在 QDC 上執行設置腳本
echo -e "${YELLOW}🚀 在 QDC 上執行設置腳本...${NC}"

# 獲取用戶主目錄
echo -e "${YELLOW}🔍 檢查用戶主目錄...${NC}"

# 嘗試檢測操作系統類型
OS_TYPE=$(ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost "ver" 2>/dev/null)
WINDOWS_OS=0

if [[ "$OS_TYPE" == *"Microsoft Windows"* ]]; then
    echo -e "${BLUE}✅ 檢測到 Windows 操作系統${NC}"
    WINDOWS_OS=1
    # Windows 環境下使用 %USERPROFILE%
    USER_HOME_DIR=$(ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost "echo %USERPROFILE%" 2>/dev/null)
else
    # 嘗試獲取 Unix/Linux 環境下的 $HOME
    USER_HOME_DIR=$(ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost "echo \$HOME" 2>/dev/null | tr -d '\r')
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

# 執行遠程設置腳本
echo -e "
${YELLOW}🚀 開始在 QDC 中執行設置...${NC}"

if [ $WINDOWS_OS -eq 1 ]; then
    # Windows 環境下執行 .bat 文件
    SETUP_SCRIPT_NAME="qdc_setup.bat"
    SCRIPT_PATH="$USER_HOME_DIR\$SETUP_SCRIPT_NAME"
    
    echo -e "${BLUE}ℹ️ 在 Windows 環境下執行 .bat 腳本${NC}"
    ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost "cd "$USER_HOME_DIR" && $SETUP_SCRIPT_NAME"
else
    # Linux/Unix 環境下執行 .sh 文件
    SETUP_SCRIPT_NAME="qdc_setup.sh"
    SCRIPT_PATH="$USER_HOME_DIR/$SETUP_SCRIPT_NAME"
    
    echo -e "${BLUE}ℹ️ 在 Unix/Linux 環境下執行 .sh 腳本${NC}"
    ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost "chmod +x $SCRIPT_PATH && $SCRIPT_PATH"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ QDC 設置成功！${NC}"
else
    echo -e "${RED}❌ QDC 設置失敗${NC}"
    echo -e "${YELLOW}⚠️ 請手動檢查設置腳本並修復問題${NC}"
    exit 1
fi

# 創建方便的 SSH 連接腳本
cat > qdc_ssh.sh << EOL
#!/bin/bash
# 快速連接 QDC 的 SSH 腳本

# 檢查是否已有隧道在運行
TUNNEL_PID=\$(lsof -ti:$LOCAL_PORT 2>/dev/null)
if [ -z "\$TUNNEL_PID" ]; then
    echo "⚠️ 沒有運行中的隧道，將先啟動隧道"
    ./qdc_auto_connect.sh
    
    if [ \$? -ne 0 ]; then
        echo "❌ 無法啟動隧道，請檢查連接問題"
        exit 1
    fi
fi

# 連接到 QDC
ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost
EOL

chmod +x qdc_ssh.sh

echo -e "${GREEN}🎉 QDC 設置完成！${NC}"
echo "=============================================="
echo -e "${CYAN}📋 接下來可以:${NC}"
echo "1. 使用快速連接腳本連接 QDC:"
echo "   ./qdc_ssh.sh"
echo ""
echo "2. 停止 SSH 隧道:"
echo "   kill \$(lsof -ti:$LOCAL_PORT)"
echo ""
echo -e "${GREEN}🐉 Dragon X Fall Detection System 已完全設置！${NC}"
