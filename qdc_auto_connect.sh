#!/bin/bash
# QDC (Qualcomm Device Cloud) 自動連接腳本 - Mac 端
# 此腳本用於從 Mac 端建立 SSH 隧道並連接到 QDC
# 版本：2025.08.13 - 修復批處理文件語法問題，簡化設計

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🐉 Dragon X Fall Detection System${NC}"
echo -e "${CYAN}Qualcomm Device Cloud 自動連接腳本 - Mac 端${NC}"
echo "=============================================="

# 設置常量
QDC_SSH_HOST="ssh.qdc.qualcomm.com"
QDC_TUNNEL_USER="sshtunnel"
DEFAULT_QDC_DEVICE_HOST="sa297054.sa.svc.cluster.local"
LOCAL_PORT=2222
REMOTE_PORT=22
USERNAME="hcktest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_KEY_PATH="${SCRIPT_DIR}/qdc_id_2025-8-11_62.pem"
WINDOWS_OS=0 # 默認非 Windows 環境
LOCAL_ENV_FILE="${SCRIPT_DIR}/.env"
LOCAL_API_TOKEN=""
POST_INSTALL_CONFIG=0  # 預設不需安裝後再 configure，若初次失敗會設為1
CONFIG_DIR_NAME=".qai_hub"  # QAI Hub CLI 實際使用的設定資料夾 (注意是底線 _ )

# 嘗試從本地 .env 讀取 QAI_HUB_API_TOKEN
if [ -f "$LOCAL_ENV_FILE" ]; then
    LOCAL_API_TOKEN=$(grep -E '^QAI_HUB_API_TOKEN=' "$LOCAL_ENV_FILE" | head -n1 | cut -d'=' -f2- | tr -d '"' | tr -d '\r')
    if [ ! -z "$LOCAL_API_TOKEN" ]; then
        echo -e "${GREEN}✅ 從本地 .env 讀取到 QAI_HUB_API_TOKEN${NC}"
    else
        echo -e "${YELLOW}⚠️ 本地 .env 存在但未找到 QAI_HUB_API_TOKEN 變數${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️ 未找到本地 .env，可稍後手動提供 API Token${NC}"
fi

# 存儲最近的主機名到配置文件
QDC_CONFIG_FILE="${SCRIPT_DIR}/.qdc_config"

# 檢查是否有配置文件並讀取上次的主機名
LAST_QDC_DEVICE_HOST=""
if [ -f "$QDC_CONFIG_FILE" ]; then
    LAST_QDC_DEVICE_HOST=$(grep "QDC_DEVICE_HOST" "$QDC_CONFIG_FILE" | cut -d'=' -f2)
fi

# 如果有上次使用的主機名，使用它作為默認值
if [ ! -z "$LAST_QDC_DEVICE_HOST" ]; then
    DEFAULT_QDC_DEVICE_HOST="$LAST_QDC_DEVICE_HOST"
fi

# 提示用戶輸入主機名
echo -e "${YELLOW}📋 QDC主機名設置:${NC}"
echo -e "${BLUE}每天的QDC session主機名都會變動，請輸入今天的主機名${NC}"
echo -e "${BLUE}格式例如: sa297036.sa.svc.cluster.local${NC}"
read -p "QDC主機名 (默認: $DEFAULT_QDC_DEVICE_HOST): " INPUT_QDC_DEVICE_HOST

# 如果用戶沒有輸入，使用默認值
QDC_DEVICE_HOST=${INPUT_QDC_DEVICE_HOST:-$DEFAULT_QDC_DEVICE_HOST}

# 保存當前使用的主機名到配置文件
echo "QDC_DEVICE_HOST=$QDC_DEVICE_HOST" > "$QDC_CONFIG_FILE"

echo -e "${GREEN}✅ 使用QDC主機名: $QDC_DEVICE_HOST${NC}"

# 若本地無 token 則詢問輸入（可直接 Enter 跳過）
if [ -z "$LOCAL_API_TOKEN" ]; then
    read -p "輸入 QAI_HUB_API_TOKEN (可留空稍後再設): " INPUT_TOKEN
    if [ ! -z "$INPUT_TOKEN" ]; then
        LOCAL_API_TOKEN="$INPUT_TOKEN"
    fi
fi

# 檢查SSH密鑰
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${RED}❌ SSH密鑰文件不存在: $SSH_KEY_PATH${NC}"
    echo "請確保SSH密鑰在當前目錄中"
    exit 1
fi

# 設置SSH密鑰權限
chmod 600 "$SSH_KEY_PATH"
echo -e "${GREEN}✅ SSH密鑰權限設置完成${NC}"

# 定義簡化的 SSH 命令函數
ssh_exec() {
    ssh -i "$SSH_KEY_PATH" -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost "$@"
}

# 定義簡化的 SCP 命令函數
scp_transfer() {
    scp -i "$SSH_KEY_PATH" -P $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$1" "$USERNAME@localhost:$2"
}

# 檢查是否已有隧道在運行
TUNNEL_PID=$(lsof -ti:$LOCAL_PORT 2>/dev/null)
if [ ! -z "$TUNNEL_PID" ]; then
    echo -e "${YELLOW}⚠️ 已有隧道在運行 (PID: $TUNNEL_PID)${NC}"
    read -p "是否重新啟動隧道？ (y/n): " RESTART_TUNNEL
    if [ "$RESTART_TUNNEL" = "y" ]; then
        echo -e "${YELLOW}🔄 停止現有隧道...${NC}"
        kill $TUNNEL_PID
        sleep 2
    else
        echo -e "${GREEN}✅ 使用現有隧道${NC}"
    fi
fi

# 如果沒有運行中的隧道或選擇重啟，則啟動新隧道
if [ -z "$TUNNEL_PID" ] || [ "$RESTART_TUNNEL" = "y" ]; then
    echo -e "${YELLOW}🔍 設置SSH隧道...${NC}"
    echo -e "${CYAN}⚠️ 重要提示: 此連接將在背景運行。如需停止，請使用 'kill \$(lsof -ti:$LOCAL_PORT)'${NC}"
    echo -e "${YELLOW}🔄 設置SSH隧道到QDC: $QDC_SSH_HOST -> $QDC_DEVICE_HOST${NC}"
    
    # 啟動SSH隧道
    ssh -i "$SSH_KEY_PATH" -L $LOCAL_PORT:$QDC_DEVICE_HOST:$REMOTE_PORT -N $QDC_TUNNEL_USER@$QDC_SSH_HOST -o ConnectTimeout=10 -o StrictHostKeyChecking=no -f
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ SSH隧道建立成功${NC}"
        # 等待隧道完全啟動
        sleep 3
    else
        echo -e "${RED}❌ SSH隧道建立失敗${NC}"
        exit 1
    fi
fi

# 測試隧道連接
echo -e "${YELLOW}🔍 測試SSH連接...${NC}"
ssh_exec "echo 'Connection successful'" >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SSH連接測試成功${NC}"
else
    echo -e "${RED}❌ SSH連接失敗，請檢查網絡和設備狀態${NC}"
    echo -e "${YELLOW}⚠️ 可能原因:${NC}"
    echo "1. QDC設備可能已重啟"
    echo "2. 網絡連接問題"
    echo "3. SSH密鑰可能已更改"
    echo ""
    echo -e "${YELLOW}嘗試重新連接...${NC}"
    
    # 停止現有隧道
    TUNNEL_PID=$(lsof -ti:$LOCAL_PORT 2>/dev/null)
    if [ ! -z "$TUNNEL_PID" ]; then
        kill $TUNNEL_PID
        sleep 2
    fi
    
    # 重新啟動隧道
    ssh -i "$SSH_KEY_PATH" -L $LOCAL_PORT:$QDC_DEVICE_HOST:$REMOTE_PORT -N $QDC_TUNNEL_USER@$QDC_SSH_HOST -o ConnectTimeout=10 -o StrictHostKeyChecking=no -f
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ SSH隧道重新建立成功${NC}"
        # 等待隧道完全啟動
        sleep 3
        
        # 再次測試連接
        ssh_exec "echo 'Connection successful'" >/dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ SSH連接測試成功${NC}"
        else
            echo -e "${RED}❌ 重試後仍連接失敗，請檢查網絡和設備狀態${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ SSH隧道重新建立失敗${NC}"
        exit 1
    fi
fi

# 檢查用戶主目錄
echo -e "${YELLOW}🔍 檢查用戶主目錄...${NC}"

# 嘗試檢測操作系統類型
OS_TYPE=$(ssh_exec "ver" 2>/dev/null)
WINDOWS_OS=0

if [[ "$OS_TYPE" == *"Microsoft Windows"* ]]; then
    echo -e "${BLUE}✅ 檢測到 Windows 操作系統${NC}"
    WINDOWS_OS=1
    # Windows 環境下使用 %USERPROFILE%
    USER_HOME_DIR=$(ssh_exec "echo %USERPROFILE%" 2>/dev/null | tr -d '\r')
else
    # 嘗試獲取 Unix/Linux 環境下的 $HOME
    USER_HOME_DIR=$(ssh_exec "echo \$HOME" 2>/dev/null | tr -d '\r')
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

# 準備設置指南
echo -e "${YELLOW}📦 準備連接到 QDC...${NC}"

# Windows 環境設置
if [ $WINDOWS_OS -eq 1 ]; then
    # 檢查 Git 和 Python
    echo -e "${YELLOW}🔍 檢查 QDC 環境...${NC}"
    
    # 檢查 Git 是否已安裝
    echo -e "${BLUE}ℹ️ 檢查 Git 安裝狀態...${NC}"
    GIT_CHECK=$(ssh_exec "where git 2>nul")
    
    if [ -z "$GIT_CHECK" ]; then
        echo -e "${RED}❌ Git 未安裝或無法找到${NC}"
        echo -e "${YELLOW}⚠️ 請確保 QDC session 創建時已安裝 Git${NC}"
        GIT_INSTALLED=0
    else
        GIT_VERSION=$(ssh_exec "git --version")
        echo -e "${GREEN}✅ Git 已安裝: $GIT_VERSION${NC}"
        GIT_INSTALLED=1
    fi
    
    # 檢查 Python 是否已安裝 - 改進版本
    echo -e "${BLUE}ℹ️ 檢查 Python 安裝狀態...${NC}"
    
    # 首先檢查 python 命令
    PYTHON_CHECK=$(ssh_exec "where python 2>nul")
    
    if [ ! -z "$PYTHON_CHECK" ]; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$(ssh_exec "$PYTHON_CMD --version 2>&1")
        echo -e "${GREEN}✅ Python 已安裝: $PYTHON_VERSION${NC}"
        PYTHON_INSTALLED=1
    else
        # 如果 python 不存在，檢查 py 命令
        PY_CHECK=$(ssh_exec "where py 2>nul")
        
        if [ ! -z "$PY_CHECK" ]; then
            PYTHON_CMD="py"
            PYTHON_VERSION=$(ssh_exec "$PYTHON_CMD --version 2>&1")
            echo -e "${GREEN}✅ Python 已安裝: $PYTHON_VERSION${NC}"
            PYTHON_INSTALLED=1
        else
            echo -e "${RED}❌ Python 未安裝或無法找到${NC}"
            echo -e "${YELLOW}⚠️ 請確保 QDC session 創建時已安裝 Python${NC}"
            PYTHON_INSTALLED=0
            PYTHON_CMD="python"  # 默認設置
        fi
    fi
    
    if [ $PYTHON_INSTALLED -eq 1 ]; then
        echo -e "${BLUE}ℹ️ 使用 Python 命令: $PYTHON_CMD${NC}"

        echo -e "${YELLOW}🔍 檢查 python-dotenv 是否已安裝...${NC}"
        DOTENV_CHECK=$(ssh_exec "$PYTHON_CMD -c \"import dotenv; print('OK')\" 2>nul")
        if [[ "$DOTENV_CHECK" == *"OK"* ]]; then
            echo -e "${GREEN}✅ python-dotenv 已存在${NC}"
        else
            echo -e "${BLUE}ℹ️ 安裝 python-dotenv...(強制安裝單一套件)${NC}"
            ssh_exec "\"$PYTHON_CMD\" -m pip install --quiet --no-cache-dir python-dotenv"
            DOTENV_CHECK2=$(ssh_exec "$PYTHON_CMD -c \"import dotenv; print('OK')\" 2>nul")
            if [[ "$DOTENV_CHECK2" == *"OK"* ]]; then
                echo -e "${GREEN}✅ python-dotenv 安裝成功${NC}"
            else
                echo -e "${RED}❌ python-dotenv 安裝失敗 (稍後可手動執行: pip install python-dotenv)${NC}"
            fi
        fi
    fi
    
    # 創建批處理文件 - 使用更簡單、更穩定的方法 (不再直接寫 client.ini, 改為 CLI configure)
    echo -e "${YELLOW}📝 創建批處理文件...${NC}"
    
    # 創建一個本地臨時批處理文件 - 使用超簡化版本
    TEMP_BATCH_FILE="$SCRIPT_DIR/temp_qdc_setup.bat"
    cat > "$TEMP_BATCH_FILE" << 'EOL'
@echo off
rem =========================================
rem QDC Ultra Simple Setup Tool
rem =========================================

echo Starting QDC Setup...

rem Check Git
echo Checking Git...
where git >nul 2>&1
if not errorlevel 1 (
  echo Git is installed
  git --version
) else (
  echo Git not found. Installing Git using winget...
  winget install --id Git.Git --source winget --silent
  echo Git installation requested. Please check if installed.
)

rem Check Python 3.10
echo Checking Python 3.10...
where python >nul 2>&1
if not errorlevel 1 (
  python --version
  echo Checking if Python 3.10 is installed...
  python -c "import sys; print(sys.version)" | findstr "3.10" >nul
  if not errorlevel 1 (
    echo Python 3.10 is available as 'python'
    goto CLONE_REPO
  ) else (
    echo Current Python is not version 3.10
  )
)

echo Installing Python 3.10 using winget...
winget install --id Python.Python.3.10 --source winget --silent
echo Python 3.10 installation requested. This may take a few minutes.
echo After installation, you may need to restart the terminal.

:CLONE_REPO
echo Setting up repository...
if exist C:\dragon-x-fall-detection (
  echo Updating existing repository
  cd C:\dragon-x-fall-detection
  git pull
) else (
  echo Cloning new repository
  cd C:\
  git clone https://github.com/andycywu/dragon-x-fall-detection.git
)

echo Skipping manual client.ini creation in batch (將於主腳本用 CLI 配置)

echo Setup completed successfully!
EOL
    
    # 上傳批處理文件
    echo -e "${YELLOW}📤 上傳批處理文件到 QDC...${NC}"
    
    # 準備上傳路徑
    REMOTE_SETUP_PATH="$USER_HOME_DIR/qdc_setup.bat"
    
    # 上傳文件
    scp_transfer "$TEMP_BATCH_FILE" "$REMOTE_SETUP_PATH"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 批處理文件上傳成功${NC}"
    else
        echo -e "${RED}❌ 批處理文件上傳失敗${NC}"
    fi
    
    # 清理臨時文件
    rm -f "$TEMP_BATCH_FILE"
    
    # 檢查批處理文件是否上傳成功
    BATCH_CHECK=$(ssh_exec "if exist \"$USER_HOME_DIR\\qdc_setup.bat\" (echo EXISTS) else (echo MISSING)")
    
    if [[ "$BATCH_CHECK" == *"EXISTS"* ]]; then
        echo -e "${GREEN}✅ 批處理文件檢測成功${NC}"
        
        # 運行批處理文件
        echo -e "${YELLOW}🔄 運行批處理文件...${NC}"
        SETUP_OUTPUT=$(ssh_exec "cd \"$USER_HOME_DIR\" && qdc_setup.bat")
        
        echo "$SETUP_OUTPUT"
        
        if [[ "$SETUP_OUTPUT" == *"Setup completed successfully"* ]]; then
            echo -e "${GREEN}✅ QDC環境設置成功${NC}"
        else
            echo -e "${YELLOW}⚠️ QDC環境設置可能不完整${NC}"
        fi
    else
        echo -e "${RED}❌ 批處理文件檢測失敗${NC}"
        
        # 嘗試直接執行命令
        echo -e "${YELLOW}🔄 直接克隆/更新倉庫...${NC}"
        
        # 檢查倉庫是否存在
        REPO_EXISTS=$(ssh_exec "if exist C:\\dragon-x-fall-detection (echo yes) else (echo no)")
        
        if [[ "$REPO_EXISTS" == *"yes"* ]]; then
            echo -e "${BLUE}ℹ️ 倉庫已存在，更新中...${NC}"
            ssh_exec "cd C:\\dragon-x-fall-detection && git pull"
        else
            echo -e "${BLUE}ℹ️ 克隆倉庫...${NC}"
            ssh_exec "cd C:\\ && git clone https://github.com/andycywu/dragon-x-fall-detection.git"
        fi
    fi
    
    # 檢查倉庫是否克隆或更新成功
    echo -e "${YELLOW}🔍 檢查倉庫狀態...${NC}"
    REPO_CHECK=$(ssh_exec "if exist C:\\dragon-x-fall-detection\\dragon_x_fall_detection_system.py (echo EXISTS) else (echo MISSING)")
    
    if [[ "$REPO_CHECK" == *"EXISTS"* ]]; then
        echo -e "${GREEN}✅ 倉庫克隆/更新成功${NC}"
    else
        echo -e "${YELLOW}⚠️ 倉庫可能未成功設置，嘗試手動克隆${NC}"
        echo -e "${BLUE}ℹ️ 執行手動克隆...${NC}"
        
        # 直接執行命令進行克隆
        ssh_exec "cd C:\\ && git clone https://github.com/andycywu/dragon-x-fall-detection.git"
        
        # 再次檢查
        REPO_CHECK=$(ssh_exec "if exist C:\\dragon-x-fall-detection\\dragon_x_fall_detection_system.py (echo EXISTS) else (echo MISSING)")
        
        if [[ "$REPO_CHECK" == *"EXISTS"* ]]; then
            echo -e "${GREEN}✅ 倉庫手動克隆成功${NC}"
        else
            echo -e "${RED}❌ 倉庫克隆失敗，請手動完成此步驟${NC}"
        fi
    fi
    
    # 上傳本地 .env（若存在）到 QDC 使用者主目錄與倉庫（若已存在）
    if [ -f "$LOCAL_ENV_FILE" ]; then
        echo -e "${YELLOW}� 上傳本地 .env 到 QDC...${NC}"
        scp_transfer "$LOCAL_ENV_FILE" "$USER_HOME_DIR/.env"
        scp_transfer "$LOCAL_ENV_FILE" "$USER_HOME_DIR/dragon-x-fall-detection/.env" 2>/dev/null || true
    fi

    # 使用 qai-hub CLI 建立 client.ini (如果有 token)
    if [ ! -z "$LOCAL_API_TOKEN" ]; then
        echo -e "${YELLOW}🔧 執行 QAI Hub CLI configure...${NC}"
        # 先確保安裝核心套件後再嘗試 configure（可能稍後才安裝, 先嘗試一次, 失敗再延後）
        CONFIG_RESULT=$(ssh_exec "qai-hub configure --api_token $LOCAL_API_TOKEN" 2>&1)
        if [[ "$CONFIG_RESULT" == *"Successfully configured"* ]] || [[ "$CONFIG_RESULT" == *"success"* ]]; then
            echo -e "${GREEN}✅ QAI Hub CLI 已建立 client.ini${NC}"
        else
            echo -e "${YELLOW}⚠️ 初次 configure 可能失敗，稍後在套件安裝後再嘗試${NC}"
            POST_INSTALL_CONFIG=1
        fi
    else
        echo -e "${YELLOW}⚠️ 未提供 API Token，將跳過自動 configure（可稍後手動執行 qai-hub configure）${NC}"
        POST_INSTALL_CONFIG=0
    fi
    
    # 檢查是否需要安裝 Python 套件
    if [ $PYTHON_INSTALLED -eq 1 ]; then
        echo -e "${YELLOW}🔍 檢查 Python 套件...${NC}"
        
        # 檢查 numpy 套件，使用確定的 Python 命令
        NUMPY_CHECK=$(ssh_exec "$PYTHON_CMD -c \"import numpy; print('OK')\" 2>nul")
        
        if [[ "$NUMPY_CHECK" == *"OK"* ]]; then
            echo -e "${GREEN}✅ Python 核心套件已安裝${NC}"
        else
            echo -e "${YELLOW}⚠️ Python 套件可能未安裝，是否安裝？ (y/n)${NC}"
            read -p "安裝 Python 套件？ (y/n): " INSTALL_PACKAGES
            
            if [ "$INSTALL_PACKAGES" = "y" ]; then
                echo -e "${BLUE}ℹ️ 安裝 Python 套件，這可能需要一些時間...${NC}"
                
                # 確保使用 Python 3.10
                PYTHON_CMD="C:\\Users\\HCKTest\\AppData\\Local\\Programs\\Python\\Python310\\python.exe"
                echo -e "${BLUE}ℹ️ 使用 Python 3.10: $PYTHON_CMD${NC}"
                
                # 使用單獨的命令安裝每個套件，避免一個失敗導致全部失敗
                echo -e "${BLUE}ℹ️ 安裝 numpy...${NC}"
                ssh_exec "cd C:\\dragon-x-fall-detection && \"$PYTHON_CMD\" -m pip install numpy"
                
                echo -e "${BLUE}ℹ️ 安裝 opencv-python...${NC}"
                ssh_exec "cd C:\\dragon-x-fall-detection && \"$PYTHON_CMD\" -m pip install opencv-python"
                
                echo -e "${BLUE}ℹ️ 安裝 onnxruntime...${NC}"
                ssh_exec "cd C:\\dragon-x-fall-detection && \"$PYTHON_CMD\" -m pip install onnxruntime"
                
                echo -e "${BLUE}ℹ️ 安裝 qai-hub 套件與 python-dotenv...${NC}"
                ssh_exec "cd C:\\dragon-x-fall-detection && \"$PYTHON_CMD\" -m pip install -U python-dotenv qai-hub qai-hub-models"

                # 再次確保 python-dotenv 存在
                DOTENV_CHECK_POST=$(ssh_exec "$PYTHON_CMD -c \"import dotenv; print('OK')\" 2>nul")
                if [[ "$DOTENV_CHECK_POST" != *"OK"* ]]; then
                    echo -e "${YELLOW}⚠️ 再嘗試單獨安裝 python-dotenv...${NC}"
                    ssh_exec "\"$PYTHON_CMD\" -m pip install python-dotenv"
                fi
                
                echo -e "${BLUE}ℹ️ 安裝 protobuf...${NC}"
                ssh_exec "cd C:\\dragon-x-fall-detection && \"$PYTHON_CMD\" -m pip install \"protobuf>=4.25.3\""
                
                # 若先前 configure 失敗且有 token，安裝後再嘗試一次
                if [ ! -z "$LOCAL_API_TOKEN" ] && [ "$POST_INSTALL_CONFIG" = "1" ]; then
                    echo -e "${BLUE}ℹ️ 安裝後重試 QAI Hub configure...${NC}"
                    CONFIG_RESULT2=$(ssh_exec "qai-hub configure --api_token $LOCAL_API_TOKEN" 2>&1)
                    if [[ "$CONFIG_RESULT2" == *"Successfully"* ]] || [[ "$CONFIG_RESULT2" == *"success"* ]]; then
                        echo -e "${GREEN}✅ 第二次 configure 成功${NC}"
                    else
                        echo -e "${RED}❌ 仍無法 configure，請手動在 QDC 執行: qai-hub configure --api_token YOUR_TOKEN${NC}"
                    fi
                fi

                # 再次檢查 numpy 是否已安裝
                NUMPY_CHECK=$(ssh_exec "\"$PYTHON_CMD\" -c \"import numpy; print('OK')\" 2>nul")
                
                if [[ "$NUMPY_CHECK" == *"OK"* ]]; then
                    echo -e "${GREEN}✅ Python 核心套件安裝成功${NC}"
                else
                    echo -e "${RED}❌ Python 套件安裝可能不完整${NC}"
                fi
            else
                echo -e "${BLUE}ℹ️ 跳過 Python 套件安裝${NC}"
            fi
        fi
    fi

    # ===== 驗證 client.ini 是否真正存在並自動重試 =====
    if [ ! -z "$LOCAL_API_TOKEN" ]; then
        echo -e "${YELLOW}🔍 驗證 client.ini 是否已建立...${NC}"
        CONFIG_PATH_WIN="$USER_HOME_DIR\\$CONFIG_DIR_NAME\\client.ini"
        MAX_CHECK_ATTEMPTS=3
        ATTEMPT=1
        CLIENT_INI_FOUND=0
        MASKED_TOKEN="${LOCAL_API_TOKEN:0:6}****${LOCAL_API_TOKEN: -4}"
        while [ $ATTEMPT -le $MAX_CHECK_ATTEMPTS ]; do
            # 強制使用 cmd /c 以避免 PowerShell 語法差異
            INI_CHECK=$(ssh_exec "cmd /c if exist \"$CONFIG_PATH_WIN\" (echo FOUND) else (echo MISSING)")
            if [[ "$INI_CHECK" == *"FOUND"* ]]; then
                echo -e "${GREEN}✅ 已找到 client.ini: $CONFIG_PATH_WIN${NC}"
                CLIENT_INI_FOUND=1
                break
            else
                echo -e "${YELLOW}⚠️ 第 $ATTEMPT 次未找到 client.ini，重新執行 configure...${NC}"
                RECONF_OUTPUT=$(ssh_exec "qai-hub configure --api_token $LOCAL_API_TOKEN" 2>&1)
                echo -e "${BLUE}ℹ️ configure 輸出 (前幾行):${NC}"
                echo "$RECONF_OUTPUT" | sed -e 's/'"$LOCAL_API_TOKEN"'/"$MASKED_TOKEN"/g' | head -n 6
                # 額外列出隱藏資料夾內容輔助除錯
                PARENT_LIST=$(ssh_exec "cmd /c if exist \"$USER_HOME_DIR\\$CONFIG_DIR_NAME\" (dir \"$USER_HOME_DIR\\$CONFIG_DIR_NAME\") else (echo <CONFIG_DIR_NOT_CREATED>)")
                echo -e "${BLUE}📂 當前設定目錄列表 (截斷):${NC}"
                echo "$PARENT_LIST" | head -n 8
                sleep 2
            fi
            ATTEMPT=$((ATTEMPT+1))
        done
        if [ $CLIENT_INI_FOUND -eq 0 ]; then
            # PowerShell fallback
            PS_CHECK=$(ssh_exec "powershell -NoProfile -Command \"if (Test-Path '$CONFIG_PATH_WIN') { Write-Output FOUND } else { Write-Output MISSING }\"")
            if [[ "$PS_CHECK" == *"FOUND"* ]]; then
                echo -e "${GREEN}✅ 已找到 client.ini (PowerShell 檢測): $CONFIG_PATH_WIN${NC}"
                CLIENT_INI_FOUND=1
            fi
        fi
        if [ $CLIENT_INI_FOUND -eq 1 ]; then
            echo -e "${YELLOW}📄 顯示 client.ini 前 5 行:${NC}"
            HEAD_CONTENT=$(ssh_exec "powershell -NoProfile -Command \"Get-Content -Path '$CONFIG_PATH_WIN' | Select-Object -First 5\"")
            # 遮罩 token
            echo "$HEAD_CONTENT" | sed -e 's/'"$LOCAL_API_TOKEN"'/"$MASKED_TOKEN"/g'
        else
            echo -e "${RED}❌ 多次重試後仍未生成 client.ini${NC}"
            echo -e "${YELLOW}👉 請手動在 QDC 內執行 (token 已遮罩):${NC}"
            echo "qai-hub configure --api_token $MASKED_TOKEN"
            echo -e "${YELLOW}🔎 之後檢查 (CMD): if exist %USERPROFILE%\\$CONFIG_DIR_NAME\\client.ini (echo OK) else (echo NO)${NC}"
        fi
    else
        echo -e "${YELLOW}ℹ️ 無 API Token，略過 client.ini 驗證${NC}"
    fi
else
    # Unix/Linux環境 - 提供基本說明
    echo -e "${YELLOW}📤 準備 Unix/Linux 環境設置指南...${NC}"
    echo -e "${BLUE}ℹ️ 建議直接使用 git 克隆倉庫並設置環境${NC}"
fi

# 連接成功，顯示使用說明
echo -e "${GREEN}🎉 QDC連接成功！${NC}"
echo "=============================================="
echo -e "${CYAN}📋 接下來可以:${NC}"

if [ $WINDOWS_OS -eq 1 ]; then
    # Windows環境的說明
    echo "1. 直接SSH進入QDC:"
    echo "   ssh -i $SSH_KEY_PATH -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost"
    echo ""
    echo "2. 運行檢測系統:"
    echo "   cd C:\\dragon-x-fall-detection"
    echo "   C:\\Users\\HCKTest\\AppData\\Local\\Programs\\Python\\Python310\\python.exe dragon_x_fall_detection_system.py"
    echo ""
    echo "3. 或使用我們的最終解決方案:"
    echo "   C:\\dragon-x-fall-detection\\run_dragon_x_final.bat"
    echo ""
else
    # Unix/Linux環境的說明
    echo "1. 直接SSH進入QDC:"
    echo "   ssh -i $SSH_KEY_PATH -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost"
    echo ""
    echo "2. 在QDC上克隆倉庫:"
    echo "   cd ~"
    echo "   git clone https://github.com/andycywu/dragon-x-fall-detection.git"
    echo "   cd dragon-x-fall-detection"
    echo ""
    echo "3. 安裝必要的Python套件:"
    echo "   pip install numpy opencv-python onnxruntime"
    echo "   pip install -r requirements.txt"
    echo "   pip install -U qai-hub qai-hub-models protobuf==4.25.3"
fi

echo ""
echo "4. 停止SSH隧道:"
echo "   kill \$(lsof -ti:$LOCAL_PORT)"
echo ""
echo -e "${GREEN}🐉 Dragon X Fall Detection System - QDC 連接設置完成！${NC}"
