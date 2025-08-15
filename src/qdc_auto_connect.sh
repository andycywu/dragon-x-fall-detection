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
echo -e "=============================================="

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
PYTHON_TARGET_VERSION="3.11"          # 主要大版本/次版本 (升級至 3.11 ARM64)
PYTHON_PATCH_VERSION="9"              # 指定修正版號 (官方 installer 組合需要)
PYTHON_FULL_VERSION="${PYTHON_TARGET_VERSION}.${PYTHON_PATCH_VERSION}"  # 3.11.9
PYTHON_REQUIRED_ARCH="ARM64"          # 目標架構
REQUIRED_PY_PACKAGES=()
OPTIONAL_PY_PACKAGES=()
QNN_PROVIDER_TEST_SCRIPT='import onnxruntime as ort;print("QNNExecutionProvider" in ort.get_available_providers())'
DIRECTML_PROVIDER_TEST_SCRIPT='import onnxruntime as ort;print("DmlExecutionProvider" in ort.get_available_providers())'

echo -e "${BLUE}🔧 目標 Python 版本: ${PYTHON_TARGET_VERSION} / 目標架構: ${PYTHON_REQUIRED_ARCH}${NC}"

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
echo -e "QDC_DEVICE_HOST=$QDC_DEVICE_HOST" > "$QDC_CONFIG_FILE"

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
    echo -e "請確保SSH密鑰在當前目錄中"
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
    echo -e "1. QDC設備可能已重啟"
    echo -e "2. 網絡連接問題"
    echo -e "3. SSH密鑰可能已更改"
    echo -e ""
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

# ===== 立即偵測遠端 OS 與架構 (統一安裝策略) =====
echo -e "${YELLOW}🔍 探測遠端系統資訊...${NC}"
OS_TYPE=$(ssh_exec "ver" 2>/dev/null)
WINDOWS_OS=0
REMOTE_OS_ARCH="UNKNOWN"
REMOTE_OS_ARM64=0
if [[ "$OS_TYPE" == *"Microsoft Windows"* ]]; then
    WINDOWS_OS=1
    REMOTE_OS_ARCH=$(ssh_exec "echo %PROCESSOR_ARCHITECTURE%" 2>/dev/null | tr -d '\r' | tr '[:lower:]' '[:upper:]')
    if [ -z "$REMOTE_OS_ARCH" ]; then
        REMOTE_OS_ARCH=$(ssh_exec "powershell -NoProfile -Command \"$env:PROCESSOR_ARCHITECTURE\"" 2>/dev/null | tr -d '\r' | tr '[:lower:]' '[:upper:]')
    fi
    [ -z "$REMOTE_OS_ARCH" ] && REMOTE_OS_ARCH="UNKNOWN"
    if [ "$REMOTE_OS_ARCH" = "ARM64" ]; then
        REMOTE_OS_ARM64=1
        echo -e "${GREEN}✅ 遠端 Windows (ARM64)${NC}"
    else
        echo -e "${YELLOW}⚠️ 遠端 Windows 架構: $REMOTE_OS_ARCH (非 ARM64)${NC}"
    fi
else
    echo -e "${CYAN}ℹ️ 非 Windows 環境 (暫以 Unix/Linux 流程)${NC}"
fi

# 統一決定 Python 安裝架構參數（強制 x64）
if [[ "$WINDOWS_OS" == "1" ]]; then
    WINGET_PY_ARCH="--architecture x64"
    echo -e "${BLUE}🛠️  之後 winget Python 安裝將強制使用: $WINGET_PY_ARCH${NC}"
fi

# 檢查用戶主目錄 (依平台)
echo -e "${YELLOW}🔍 檢查用戶主目錄...${NC}"
if [[ "$WINDOWS_OS" == "1" ]]; then
    USER_HOME_DIR=$(ssh_exec "echo %USERPROFILE%" 2>/dev/null | tr -d '\r')
else
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

echo -e "\033[1;32mSetup completed successfully!\033[0m"
# Windows 環境設置與 clone/安裝/設定合併
if [[ "$WINDOWS_OS" == "1" ]]; then
    echo -e "${YELLOW}🔍 檢查 QDC 環境...${NC}"
    # 檢查 Git
    echo -e "${BLUE}ℹ️ 檢查 Git 安裝狀態...${NC}"
    GIT_CHECK=$(ssh_exec "where git 2>nul")
    if [ -z "$GIT_CHECK" ]; then
    echo -e "${RED}❌ Git 未安裝或無法找到，嘗試安裝...${NC}"
        ssh_exec "winget install --id Git.Git --source winget --silent" >/dev/null 2>&1 || true
    else
        GIT_VERSION=$(ssh_exec "git --version")
    echo -e "${GREEN}✅ Git 已安裝: $GIT_VERSION${NC}"
    fi
    # 檢查 Python（強制 x64）
    echo -e "${BLUE}ℹ️ 檢查 Python (x64) 安裝狀態...${NC}"
    PYTHON_CHECK=$(ssh_exec "where python 2>nul")
    PYTHON_CMD="python"
    PYTHON_INSTALLED=0
    if [ ! -z "$PYTHON_CHECK" ]; then
        PYTHON_VERSION=$(ssh_exec "$PYTHON_CMD --version 2>&1")
    echo -e "${GREEN}✅ Python 已安裝: $PYTHON_VERSION${NC}"
        PYTHON_INSTALLED=1
    else
    echo -e "${RED}❌ Python 未安裝，嘗試安裝...${NC}"
        ssh_exec "winget install --id Python.Python.${PYTHON_TARGET_VERSION} --source winget --silent --override \"InstallAllUsers=1 PrependPath=1\" $WINGET_PY_ARCH" >/dev/null 2>&1 || true
        PYTHON_INSTALLED=1
    fi
    # clone/pull repo
    echo -e "${YELLOW}🔄 檢查/克隆/更新專案...${NC}"
    REPO_EXISTS=$(ssh_exec "if exist C:\\dragon-x-fall-detection (echo yes) else (echo no)")
    if [[ "$REPO_EXISTS" == *"yes"* ]]; then
    echo -e "${BLUE}ℹ️ 倉庫已存在，更新中...${NC}"
        ssh_exec "cd C:\\dragon-x-fall-detection && git pull"
        # 先安裝 requirements.txt
        echo -e "${YELLOW}🔍 進入專案目錄安裝 requirements.txt...${NC}"
        ssh_exec "cd C:\\dragon-x-fall-detection && $PYTHON_CMD -m pip install --upgrade pip && $PYTHON_CMD -m pip install -r requirements.txt" || true
    else
    echo -e "${BLUE}ℹ️ 克隆倉庫...${NC}"
        ssh_exec "cd C:\\ && git clone https://github.com/andycywu/dragon-x-fall-detection.git"
    fi
    # 上傳 .env
    if [ -f "$LOCAL_ENV_FILE" ]; then
    echo -e "${YELLOW}📤 上傳本地 .env 到 QDC...${NC}"
        scp_transfer "$LOCAL_ENV_FILE" "$USER_HOME_DIR/.env"
        scp_transfer "$LOCAL_ENV_FILE" "$USER_HOME_DIR/dragon-x-fall-detection/.env" 2>/dev/null || true
    fi
    # 若專案已存在且 requirements.txt 安裝無誤，再做 qai-hub configure
    if [[ "$REPO_EXISTS" == *"yes"* ]] && [ ! -z "$LOCAL_API_TOKEN" ]; then
        echo -e "${YELLOW}🔧 執行 QAI Hub CLI configure...${NC}"
        echo -e "[DEBUG] 執行指令: qai-hub configure --api_token $LOCAL_API_TOKEN"
        CONFIG_RESULT=$(ssh_exec "qai-hub configure --api_token $LOCAL_API_TOKEN" 2>&1)
        echo -e "[DEBUG] configure 輸出: $CONFIG_RESULT"
        if [[ "$CONFIG_RESULT" == *"Successfully configured"* ]] || [[ "$CONFIG_RESULT" == *"success"* ]]; then
            echo -e "${GREEN}✅ QAI Hub CLI 已建立 client.ini${NC}"
        else
            echo -e "${RED}❌ 未生成 client.ini，將嘗試手動輸入 token 進行 configure${NC}"
            read -p "請手動輸入 QAI_HUB_API_TOKEN（可直接複製 .env 內容）: " MANUAL_TOKEN
            if [ ! -z "$MANUAL_TOKEN" ]; then
                echo -e "[DEBUG] 執行指令: qai-hub configure --api_token $MANUAL_TOKEN"
                CONFIG_RESULT2=$(ssh_exec "qai-hub configure --api_token $MANUAL_TOKEN" 2>&1)
                echo -e "[DEBUG] configure 輸出: $CONFIG_RESULT2"
                if [[ "$CONFIG_RESULT2" == *"Successfully configured"* ]] || [[ "$CONFIG_RESULT2" == *"success"* ]]; then
                    echo -e "${GREEN}✅ QAI Hub CLI 已建立 client.ini（手動 token）${NC}"
                else
                    echo -e "${RED}❌ 仍未生成 client.ini，請檢查 token 或手動於 QDC 執行: qai-hub configure --api_token <TOKEN>${NC}"
                fi
            else
                echo -e "${YELLOW}⚠️ 未輸入 token，請稍後手動於 QDC 執行: qai-hub configure --api_token <TOKEN>${NC}"
            fi
        fi
        CONFIG_PATH_WIN="$USER_HOME_DIR\\$CONFIG_DIR_NAME\\client.ini"
        sleep 2  # 等待 client.ini 寫入
        echo -e "[DEBUG] 驗證 client.ini 路徑: $CONFIG_PATH_WIN"
        INI_CHECK=$(ssh_exec "cmd /c if exist \"$CONFIG_PATH_WIN\" (echo FOUND) else (echo MISSING)")
        echo -e "[DEBUG] client.ini 狀態: $INI_CHECK"
        if [[ "$INI_CHECK" == *"FOUND"* ]]; then
            echo -e "${GREEN}✅ 已找到 client.ini: $CONFIG_PATH_WIN${NC}"
        else
            echo -e "${RED}❌ 未生成 client.ini，請手動於 QDC 執行: qai-hub configure --api_token <TOKEN>${NC}"
            echo -e "[DEBUG] 遠端 .qai_hub 目錄內容:"
            ssh_exec "dir $USER_HOME_DIR\\$CONFIG_DIR_NAME"
            echo -e "[DEBUG] 遠端家目錄內容:"
            ssh_exec "dir $USER_HOME_DIR"
        fi
    elif [ -z "$LOCAL_API_TOKEN" ]; then
    echo -e "${YELLOW}⚠️ 未提供 API Token，將跳過自動 configure（可稍後手動執行 qai-hub configure）${NC}"
        POST_INSTALL_CONFIG=0
    fi
    # 安裝 Python 套件（補充：若 requirements.txt 沒有的也補裝）
    echo -e "${YELLOW}🔍 安裝/驗證 Python 套件...${NC}"
    ssh_exec "$PYTHON_CMD -m pip install --upgrade pip" >/dev/null 2>&1 || true
    echo -e "${YELLOW}🔍 直接安裝 requirements.txt...${NC}"
    ssh_exec "cd C:\\dragon-x-fall-detection && $PYTHON_CMD -m pip install --upgrade pip && $PYTHON_CMD -m pip install -r requirements.txt" || true
    # 驗證 client.ini
    if [ ! -z "$LOCAL_API_TOKEN" ]; then
        CONFIG_PATH_WIN="$USER_HOME_DIR\\$CONFIG_DIR_NAME\\client.ini"
        INI_CHECK=$(ssh_exec "cmd /c if exist \"$CONFIG_PATH_WIN\" (echo FOUND) else (echo MISSING)")
        if [[ "$INI_CHECK" == *"FOUND"* ]]; then
            echo -e "${GREEN}✅ 已找到 client.ini: $CONFIG_PATH_WIN${NC}"
        else
            echo -e "${RED}❌ 未生成 client.ini，請手動於 QDC 執行: qai-hub configure --api_token <TOKEN>${NC}"
        fi
    fi
fi
# === test_images 上傳（流程最後） ===
LOCAL_TEST_IMAGES_DIR="$SCRIPT_DIR/test_images"
if [ -d "$LOCAL_TEST_IMAGES_DIR" ]; then
    FILE_COUNT=$(find "$LOCAL_TEST_IMAGES_DIR" -type f | wc -l | tr -d ' ')
    DIR_COUNT=$(find "$LOCAL_TEST_IMAGES_DIR" -type d | wc -l | tr -d ' ')
    echo -e "${YELLOW}📤 偵測到 test_images (檔案: $FILE_COUNT)${NC}"
    read -t 10 -p "上傳 test_images? (a=全部 / n=指定前N個 / s=跳過) [a/n/s]: " TI_DECISION || TI_DECISION="a"
    case "$TI_DECISION" in
        n|N)
            read -p "輸入要上傳的前 N 個檔案數 (默認 10): " TI_N
            TI_N=${TI_N:-10}
            echo -e "${BLUE}🔧 將上傳前 $TI_N 個檔案到遠端 test_images_partial${NC}"
            TMP_LIST=$(find "$LOCAL_TEST_IMAGES_DIR" -type f | head -n $TI_N)
            TAR_TMP="$SCRIPT_DIR/test_images_partial_upload"
            rm -rf "$TAR_TMP" 2>/dev/null || true
            mkdir -p "$TAR_TMP"
            I=0
            while IFS= read -r P; do
                BN=$(basename "$P")
                cp "$P" "$TAR_TMP/$BN"
            done <<< "$TMP_LIST"
            scp -r -i "$SSH_KEY_PATH" -P $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$TAR_TMP" "$USERNAME@localhost:$USER_HOME_DIR/test_images_partial" 2>&1 && echo -e "${GREEN}✅ 已上傳部分測試影像 -> test_images_partial${NC}" || echo -e "${RED}❌ 部分上傳失敗${NC}"
            rm -rf "$TAR_TMP" || true
            ;;
        s|S)
            echo -e "${CYAN}ℹ️ 跳過 test_images 上傳${NC}"
            ;;
        *)
            echo -e "${BLUE}🌐 上傳全部 test_images...${NC}"
            scp -r -i "$SSH_KEY_PATH" -P $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$LOCAL_TEST_IMAGES_DIR" "$USERNAME@localhost:$USER_HOME_DIR" 2>&1
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ test_images 已上傳到 $USER_HOME_DIR/${NC}"
                if [ $WINDOWS_OS -eq 1 ]; then
                    REMOTE_CHECK=$(ssh_exec "if exist \"$USER_HOME_DIR\\test_images\" (echo EXISTS) else (echo MISSING)")
                else
                    REMOTE_CHECK=$(ssh_exec "[ -d '$USER_HOME_DIR/test_images' ] && echo EXISTS || echo MISSING")
                fi
                [[ "$REMOTE_CHECK" == *"EXISTS"* ]] && echo -e "${GREEN}📂 遠端 test_images 驗證成功${NC}" || echo -e "${YELLOW}⚠️ 未驗證到 test_images${NC}"
            else
                echo -e "${RED}❌ 上傳 test_images 失敗 (可稍後手動執行)${NC}"
            fi
            ;;
    esac
else
    echo -e "${CYAN}ℹ️ 未找到本地 test_images 目錄，跳過上傳區段${NC}"
fi

# 連接成功，顯示使用說明
echo -e "${GREEN}🎉 QDC連接成功！${NC}"
echo -e "=============================================="
echo -e "${CYAN}📋 接下來可以:${NC}"

if [[ "$WINDOWS_OS" == "1" ]]; then
    # Windows環境的說明
    echo -e "1. 直接SSH進入QDC:"
    echo -e "   ssh -i $SSH_KEY_PATH -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost"
    echo -e "   (如出現 'Permanently added ... to the list of known hosts.' 屬於正常現象，代表首次連線已自動信任)"
    echo -e ""
    echo -e "2. 運行檢測系統:"
    echo -e "   cd C:\\dragon-x-fall-detection"
    echo -e "   C:\\Users\\HCKTest\\AppData\\Local\\Programs\\Python\\Python310\\python.exe dragon_x_fall_detection_system.py"
    echo -e ""
    echo -e "3. 或使用我們的最終解決方案:"
    echo -e "   C:\\dragon-x-fall-detection\\run_dragon_x_final.bat"
    echo -e ""
else
    # Unix/Linux環境的說明
    echo -e "1. 直接SSH進入QDC:"
    echo -e "   ssh -i $SSH_KEY_PATH -p $LOCAL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $USERNAME@localhost"
    echo -e ""
    echo -e "2. 在QDC上克隆倉庫:"
    echo -e "   cd ~"
    echo -e "   git clone https://github.com/andycywu/dragon-x-fall-detection.git"
    echo -e "   cd dragon-x-fall-detection"
    echo -e ""
    echo -e "3. 安裝必要的Python套件:"
    echo -e "   pip install numpy opencv-python onnxruntime"
    echo -e "   pip install -r requirements.txt"
    echo -e "   pip install -U qai-hub qai-hub-models protobuf==4.25.3"
fi

echo -e ""
echo -e "4. 停止SSH隧道:"
echo -e "   kill \$(lsof -ti:$LOCAL_PORT)"
echo -e ""
echo -e "${GREEN}🐉 Dragon X Fall Detection System - QDC 連接設置完成！${NC}"

# QNN backend DLL 自動偵測與設置（建議放到最後，確保環境都 ready）
if [[ "$WINDOWS_OS" == "1" ]]; then
    echo -e "${BLUE}🔍 嘗試自動偵測 QNN backend DLL...${NC}"
    QNN_SDK_PATH=$(ssh_exec "echo %QNN_SDK_ROOT%")
    if [[ ! -z "$QNN_SDK_PATH" && "$QNN_SDK_PATH" != "%QNN_SDK_ROOT%" ]]; then
        QNN_DLL_PATH=$(ssh_exec "powershell -NoProfile -Command \"Get-ChildItem -Path '$QNN_SDK_PATH' -Recurse -Filter QnnHtp.dll | Select-Object -First 1 -ExpandProperty FullName\"")
        if [[ ! -z "$QNN_DLL_PATH" ]]; then
            ssh_exec "setx QNN_BACKEND_PATH \"$QNN_DLL_PATH\"" >/dev/null 2>&1 && echo -e "${GREEN}✅ 已自動設 QNN_BACKEND_PATH=$QNN_DLL_PATH${NC}"
        else
            echo -e "${YELLOW}⚠️ 未找到 QnnHtp.dll，請確認 QNN SDK 安裝完整${NC}"
        fi
    else
    echo -e "${YELLOW}⚠️ QNN_SDK_ROOT 未設，請先安裝 QNN SDK 並設環境變數${NC}"
    fi
fi
