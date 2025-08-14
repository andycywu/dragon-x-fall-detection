            # QNN backend DLL 自動偵測與設置
            if [ $WINDOWS_OS -eq 1 ]; then
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
PYTHON_TARGET_VERSION="3.11"          # 主要大版本/次版本 (升級至 3.11 ARM64)
PYTHON_PATCH_VERSION="9"              # 指定修正版號 (官方 installer 組合需要)
PYTHON_FULL_VERSION="${PYTHON_TARGET_VERSION}.${PYTHON_PATCH_VERSION}"  # 3.11.9
PYTHON_REQUIRED_ARCH="ARM64"          # 目標架構
REQUIRED_PY_PACKAGES=(numpy opencv-python onnxruntime onnxruntime-directml python-dotenv protobuf==4.25.3 qai-hub qai-hub-models)
OPTIONAL_PY_PACKAGES=(psutil packaging)
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

# ===== 立即偵測遠端 OS 與架構 (統一安裝策略) =====
echo -e "${YELLOW}� 探測遠端系統資訊...${NC}"
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

# 統一決定 Python 安裝架構參數
if [ $WINDOWS_OS -eq 1 ]; then
    if [ $REMOTE_OS_ARM64 -eq 1 ]; then
        WINGET_PY_ARCH="--architecture arm64"
    else
        WINGET_PY_ARCH="--architecture x64"
    fi
    echo -e "${BLUE}🛠️  之後 winget Python 安裝將使用: $WINGET_PY_ARCH${NC}"
fi

# 檢查用戶主目錄 (依平台)
echo -e "${YELLOW}🔍 檢查用戶主目錄...${NC}"
if [ $WINDOWS_OS -eq 1 ]; then
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

# === test_images 上傳選擇 (若存在) ===
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
    
    # 檢查 Python 是否已安裝並且為 ARM64 (若 OS 支援)
    echo -e "${BLUE}ℹ️ 檢查 Python (ARM64) 安裝狀態...${NC}"
    
    # 首先檢查 python 命令
    PYTHON_CHECK=$(ssh_exec "where python 2>nul")
    
    if [ ! -z "$PYTHON_CHECK" ]; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$(ssh_exec "$PYTHON_CMD --version 2>&1")
        if echo "$PYTHON_VERSION" | grep -qi "was not found"; then
            echo -e "${YELLOW}⚠️ 偵測到 Windows Store 佔位 python (實際未安裝)${NC}"
            PYTHON_INSTALLED=0
        else
            echo -e "${GREEN}✅ Python 已安裝: $PYTHON_VERSION${NC}"
            PYTHON_INSTALLED=1
        fi
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

        # 偵測 Python 架構 (透過 platform.machine())
        PY_MACHINE=$(ssh_exec "$PYTHON_CMD -c \"import platform;print(platform.machine())\"" 2>/dev/null | tr -d '\r')
        PY_VERSION_STR=$(ssh_exec "$PYTHON_CMD -c \"import sys;print(sys.version.split()[0])\"" 2>/dev/null | tr -d '\r')
        echo -e "${BLUE}ℹ️ 遠端 Python 版本: ${PY_VERSION_STR} / 機器架構: ${PY_MACHINE}${NC}"
        NEED_ARM64_REINSTALL=0
        if [[ ! "$PY_MACHINE" =~ [Aa][Rr][Mm]64 ]]; then
            echo -e "${YELLOW}⚠️ 當前 Python 不是 ARM64 (偵測為: $PY_MACHINE)${NC}"
            NEED_ARM64_REINSTALL=1
        fi
        if [[ ! "$PY_VERSION_STR" == ${PYTHON_TARGET_VERSION}* ]]; then
            echo -e "${YELLOW}⚠️ Python 版本與目標 ${PYTHON_TARGET_VERSION} 不符${NC}"
            NEED_ARM64_REINSTALL=1
        fi
            if [ $NEED_ARM64_REINSTALL -eq 1 ]; then
                # 若已存在錯誤架構 Python 且 OS 為 ARM64，可選擇嘗試卸載
                if [ "$REMOTE_OS_ARM64" = "1" ] && [[ "$PY_MACHINE" != *"ARM64"* ]]; then
                    echo -e "${YELLOW}⚠️ 偵測到 OS=ARM64 但 Python=$PY_MACHINE，可選擇卸載 x64 Python 後再裝 ARM64。${NC}"
                    read -t 8 -p "是否嘗試 winget 卸載現有 Python 3.11? (y/N): " UNINSTALL_DECISION || true
                    if [[ "$UNINSTALL_DECISION" == "y" || "$UNINSTALL_DECISION" == "Y" ]]; then
                        echo -e "${BLUE}�️  嘗試卸載現有 Python 3.11 (x64)...${NC}"
                        ssh_exec "winget uninstall --id Python.Python.${PYTHON_TARGET_VERSION} --silent" >/dev/null 2>&1 || true
                        sleep 2
                    fi
                    # 進一步提供官方安裝程式強制 ARM64 方案
                    echo -e "${YELLOW}💡 可嘗試下載 python-${PYTHON_FULL_VERSION}-arm64.exe 官方安裝程式並靜默安裝 (若 winget 仍裝成 x64)。${NC}"
                    read -t 12 -p "是否嘗試官方 ARM64 安裝程式強制重裝？ (y/N): " FORCE_ARM64 || true
                    if [[ "$FORCE_ARM64" == "y" || "$FORCE_ARM64" == "Y" ]]; then
                        echo -e "${BLUE}🌐 下載 ARM64 安裝程式...${NC}"
                        ssh_exec "powershell -NoProfile -Command \"$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri https://www.python.org/ftp/python/${PYTHON_FULL_VERSION}/python-${PYTHON_FULL_VERSION}-arm64.exe -OutFile $env:TEMP\\py_arm64_setup.exe\"" >/dev/null 2>&1 || true
                        echo -e "${BLUE}📦 靜默安裝 ARM64 Python...${NC}"
                        ssh_exec "powershell -NoProfile -Command \"Start-Process -FilePath $env:TEMP\\py_arm64_setup.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1 Include_test=0' -Wait\"" >/dev/null 2>&1 || true
                        echo -e "${BLUE}🔁 重新檢測 Python 架構...${NC}"
                        PY_MACHINE=$(ssh_exec "$PYTHON_CMD -c \"import platform;print(platform.machine())\"" 2>/dev/null | tr -d '\r')
                        echo -e "${BLUE}📊 目前 Python machine: $PY_MACHINE${NC}"
                        if [[ "$PY_MACHINE" =~ [Aa][Rr][Mm]64 ]]; then
                            echo -e "${GREEN}✅ ARM64 Python 重新安裝成功${NC}"
                        else
                            echo -e "${RED}❌ 仍非 ARM64 Python，可能 PATH 仍指向舊版本，需手動清理環境變數與舊安裝路徑${NC}"
                        fi
                    fi
                fi
                if [ $WINDOWS_OS -eq 1 ]; then
                    echo -e "${YELLOW}🔄 使用 winget 安裝指定架構 Python ${PYTHON_TARGET_VERSION} (${WINGET_PY_ARCH})...${NC}"
                    ssh_exec "winget install --id Python.Python.${PYTHON_TARGET_VERSION} --source winget --silent --override \"InstallAllUsers=1 PrependPath=1\" $WINGET_PY_ARCH" >/dev/null 2>&1 || true
                fi
            echo -e "${BLUE}ℹ️ 重新載入 PATH 後再檢測 python ...${NC}"
            # 再次檢測 (可能需要新 session，但先嘗試)
            PYTHON_CMD="python"
            PY_MACHINE=$(ssh_exec "$PYTHON_CMD -c \"import platform;print(platform.machine())\"" 2>/dev/null | tr -d '\r')
            PY_VERSION_STR=$(ssh_exec "$PYTHON_CMD -c \"import sys;print(sys.version.split()[0])\"" 2>/dev/null | tr -d '\r')
            echo -e "${BLUE}ℹ️ 安裝後 Python 版本: ${PY_VERSION_STR} / 架構: ${PY_MACHINE}${NC}"
            if [[ "$PY_MACHINE" =~ [Aa][Rr][Mm]64 ]]; then
                echo -e "${GREEN}✅ 已取得 ARM64 Python${NC}"
            else
                if [ "$REMOTE_OS_ARM64" = "1" ]; then
                    echo -e "${RED}❌ 仍非 ARM64 Python，請手動下載官方 ARM64 安裝程式 (python.org) 並重新執行腳本${NC}"
                else
                    echo -e "${YELLOW}ℹ️ 因 OS 非 ARM64，僅能使用 x64 Python；QNN 原生加速將受限${NC}"
                fi
            fi
        else
            echo -e "${GREEN}✅ Python 已符合 ARM64 + 版本需求${NC}"
        fi

        echo -e "${YELLOW}�🔍 檢查 python-dotenv 是否已安裝...${NC}"
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

rem Check Python 3.11
echo Checking Python 3.11...
where python >nul 2>&1
if not errorlevel 1 (
  python --version
    echo Checking if Python 3.11 is installed...
    python -c "import sys; print(sys.version)" | findstr "3.11" >nul
  if not errorlevel 1 (
    echo Python 3.11 is available as 'python'
    goto CLONE_REPO
  ) else (
    echo Current Python is not version 3.11
  )
)

echo Detecting OS architecture...
for /f "tokens=*" %%A in ('echo %PROCESSOR_ARCHITECTURE%') do set CURR_ARCH=%%A
echo Current machine arch: %CURR_ARCH%
set PY_ARCH_ARG=--architecture arm64
if /I NOT "%CURR_ARCH%"=="ARM64" set PY_ARCH_ARG=--architecture x64
echo Installing Python 3.11 with %PY_ARCH_ARG% ...
winget install --id Python.Python.3.11 --source winget --silent %PY_ARCH_ARG%
echo Python 3.11 installation requested. This may take a few minutes.
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
    echo -e "${YELLOW}🔍 檢查 / 安裝 ARM64 Python 套件 (含 onnxruntime / QNN 需求)...${NC}"
        
        # 檢查 numpy 套件，使用確定的 Python 命令
        NUMPY_CHECK=$(ssh_exec "$PYTHON_CMD -c \"import numpy; print('OK')\" 2>nul")
        
        if [[ "$NUMPY_CHECK" == *"OK"* ]]; then
            echo -e "${GREEN}✅ 偵測到部分套件，將補齊 ARM64 需求${NC}"
        else
            echo -e "${YELLOW}⚠️ 尚未安裝核心套件${NC}"
        fi

    read -p "是否進行 ARM64/目前架構 Python 套件完整安裝/更新？ (y/n): " INSTALL_PACKAGES
        if [ "$INSTALL_PACKAGES" = "y" ]; then
            # 一次升級 pip
            ssh_exec "$PYTHON_CMD -m pip install --upgrade pip" >/dev/null 2>&1 || true
            if [ "$REMOTE_OS_ARM64" = "1" ]; then
                echo -e "${BLUE}ℹ️ 安裝 / 更新必要套件 (ARM64 wheel) ...${NC}"
            else
                echo -e "${YELLOW}ℹ️ 遠端非 ARM64 OS，將安裝 x64 版套件 (QNN 原生 NPU 可能無法啟用) ...${NC}"
            fi
            INSTALL_FAIL_LIST=()
            # 第一階段: numpy, protobuf
            for PKG in numpy "protobuf==4.25.3"; do
                echo -e "${BLUE}→ $PKG${NC}"
                ssh_exec "$PYTHON_CMD -m pip install --no-cache-dir --only-binary=:all: --upgrade $PKG" >/dev/null 2>&1 || INSTALL_FAIL_LIST+=("$PKG:install")
                IMPORT_NAME="$PKG"; [ "$PKG" = "protobuf==4.25.3" ] && IMPORT_NAME="google.protobuf"
                IMPORT_TEST=$(ssh_exec "$PYTHON_CMD -c 'import $IMPORT_NAME; print(\"OK\")'" 2>/dev/null | tr -d '\r')
                if [[ "$IMPORT_TEST" == *"OK"* ]]; then
                    echo -e "${GREEN}   ✔ import $IMPORT_NAME 成功${NC}"
                else
                    echo -e "${RED}   ✖ import $IMPORT_NAME 失敗${NC}"
                    INSTALL_FAIL_LIST+=("$PKG:import")
                fi
            done
            # 第二階段: onnxruntime, onnxruntime-directml, opencv-python
            for PKG in onnxruntime onnxruntime-directml opencv-python; do
                echo -e "${BLUE}→ $PKG${NC}"
                ssh_exec "$PYTHON_CMD -m pip install --no-cache-dir --only-binary=:all: --upgrade $PKG" >/dev/null 2>&1 || INSTALL_FAIL_LIST+=("$PKG:install")
                IMPORT_NAME="$PKG"; [ "$PKG" = "onnxruntime-directml" ] && IMPORT_NAME="onnxruntime"; [ "$PKG" = "opencv-python" ] && IMPORT_NAME="cv2"
                IMPORT_TEST=$(ssh_exec "$PYTHON_CMD -c 'import $IMPORT_NAME; print(\"OK\")'" 2>/dev/null | tr -d '\r')
                if [[ "$IMPORT_TEST" == *"OK"* ]]; then
                    echo -e "${GREEN}   ✔ import $IMPORT_NAME 成功${NC}"
                else
                    echo -e "${RED}   ✖ import $IMPORT_NAME 失敗${NC}"
                    INSTALL_FAIL_LIST+=("$PKG:import")
                fi
            done
            # 第三階段: qai-hub, qai-hub-models, python-dotenv
            for PKG in qai-hub qai-hub-models python-dotenv; do
                echo -e "${BLUE}→ $PKG${NC}"
                ssh_exec "$PYTHON_CMD -m pip install --no-cache-dir --upgrade $PKG" >/dev/null 2>&1 || INSTALL_FAIL_LIST+=("$PKG:install")
                IMPORT_NAME="$PKG"; [ "$PKG" = "python-dotenv" ] && IMPORT_NAME="dotenv"
                IMPORT_TEST=$(ssh_exec "$PYTHON_CMD -c 'import $IMPORT_NAME; print(\"OK\")'" 2>/dev/null | tr -d '\r')
                if [[ "$IMPORT_TEST" == *"OK"* ]]; then
                    echo -e "${GREEN}   ✔ import $IMPORT_NAME 成功${NC}"
                else
                    echo -e "${RED}   ✖ import $IMPORT_NAME 失敗${NC}"
                    INSTALL_FAIL_LIST+=("$PKG:import")
                fi
            done
            # 自動產生 requirements_arm64.txt
            echo -e "${BLUE}📝 產生 requirements_arm64.txt...${NC}"
            echo "numpy\nprotobuf==4.25.3\nonnxruntime\nonnxruntime-directml\nopencv-python\nqai-hub\nqai-hub-models\npython-dotenv" > "$SCRIPT_DIR/requirements_arm64.txt"
            if [ ${#INSTALL_FAIL_LIST[@]} -gt 0 ]; then
                echo -e "${RED}❌ 以下套件安裝或匯入失敗:${NC}"
                for F in "${INSTALL_FAIL_LIST[@]}"; do echo "  - $F"; done
                echo -e "${YELLOW}👉 建議手動逐一重試，如:${NC}"
                echo "    $PYTHON_CMD -m pip install --no-cache-dir --upgrade <pkg>"
                echo -e "${YELLOW}若為 onnxruntime 失敗，可嘗試先升級 pip/setuptools/wheel 再重裝。${NC}"
                echo -e "${YELLOW}若為 opencv-python，可改用 opencv-python-headless 或指定舊版。${NC}"
            else
                echo -e "${GREEN}✅ 必要套件全部可匯入${NC}"
            fi
            if [ ${#OPTIONAL_PY_PACKAGES[@]} -gt 0 ]; then
                echo -e "${BLUE}ℹ️ 安裝可選套件...${NC}"
                for PKG in "${OPTIONAL_PY_PACKAGES[@]}"; do
                    ssh_exec "$PYTHON_CMD -m pip install --no-cache-dir --upgrade $PKG" >/dev/null 2>&1 || true
                done
            fi

            # 再測試部分 provider 可用性
            QNN_AVAILABLE=$(ssh_exec "$PYTHON_CMD -c \"$QNN_PROVIDER_TEST_SCRIPT\"" 2>/dev/null | tr -d '\r')
            DML_AVAILABLE=$(ssh_exec "$PYTHON_CMD -c \"$DIRECTML_PROVIDER_TEST_SCRIPT\"" 2>/dev/null | tr -d '\r')
            echo -e "${BLUE}ℹ️ Provider 測試: QNN=$QNN_AVAILABLE / DirectML=$DML_AVAILABLE${NC}"
            if [ "$QNN_AVAILABLE" != "True" ]; then
                echo -e "${YELLOW}⚠️ QNNExecutionProvider 尚不可用${NC}"
                echo -e "${BLUE}👉 請確認已在裝置安裝 Qualcomm AI Engine Direct (QNN) SDK 並設定環境變數:${NC}"
                echo -e "    setx QNN_SDK_ROOT C:\\Qualcomm\\AIStack\\QNN   (或實際安裝路徑)"
                echo -e "    並確保 provider options 中 backend_path 指向對應 dll (例如 QnnHtp.dll)"
            else
                echo -e "${GREEN}✅ QNNExecutionProvider 可用${NC}"
            fi
            if [ "$DML_AVAILABLE" != "True" ]; then
                echo -e "${YELLOW}ℹ️ DirectML 未啟用 (可能不影響 QNN 使用)${NC}"
            fi

            # 安裝結果總結
            echo -e "${BLUE}📦 安裝結果總結:${NC}"
            if [ ${#INSTALL_FAIL_LIST[@]} -gt 0 ]; then
                echo -e "${RED}  ✖ 失敗套件數: ${#INSTALL_FAIL_LIST[@]}${NC}"
            else
                echo -e "${GREEN}  ✔ 全部必要套件匯入成功${NC}"
            fi
            echo -e "${BLUE}  QNN Provider: ${NC}$([ "$QNN_AVAILABLE" == "True" ] && echo "✅" || echo "❌")"
            echo -e "${BLUE}  DirectML Provider: ${NC}$([ "$DML_AVAILABLE" == "True" ] && echo "✅" || echo "❌")"
            if [ ${#INSTALL_FAIL_LIST[@]} -gt 0 ]; then
                echo -e "${YELLOW}🛠 建議: 針對失敗套件逐一手動重試並查看錯誤訊息。${NC}"
            fi
            # 自動修復 Windows 遠端 PATH
            if [ $WINDOWS_OS -eq 1 ]; then
                echo -e "${BLUE}🔧 嘗試自動修復遠端 PATH...${NC}"
                SCRIPTS_PATH_WIN="%USERPROFILE%\\AppData\\Local\\Programs\\Python\\Python311\\Scripts"
                PATH_CHECK=$(ssh_exec "echo %PATH% | findstr /I /C:\"$SCRIPTS_PATH_WIN\"")
                if [ -z "$PATH_CHECK" ]; then
                    ssh_exec "setx PATH \"%PATH%;$SCRIPTS_PATH_WIN\"" >/dev/null 2>&1 && echo -e "${GREEN}✅ 已將 Scripts 目錄加入 PATH${NC}"
                else
                    echo -e "${GREEN}✅ Scripts 目錄已在 PATH${NC}"
                fi
            fi

            # 若先前 configure 失敗且有 token，安裝後再嘗試一次
            if [ ! -z "$LOCAL_API_TOKEN" ] && [ "$POST_INSTALL_CONFIG" = "1" ]; then
                if command -v ssh >/dev/null 2>&1; then
                    echo -e "${BLUE}ℹ️ 安裝後重試 QAI Hub configure...${NC}"
                    CONFIG_RESULT2=$(ssh_exec "qai-hub configure --api_token $LOCAL_API_TOKEN" 2>&1)
                    if [[ "$CONFIG_RESULT2" == *"Successfully"* ]] || [[ "$CONFIG_RESULT2" == *"success"* ]]; then
                        echo -e "${GREEN}✅ 第二次 configure 成功${NC}"
                    else
                        echo -e "${RED}❌ 仍無法 configure，請手動在 QDC 執行: qai-hub configure --api_token YOUR_TOKEN${NC}"
                        echo -e "${YELLOW}🔧 除錯建議:${NC}"
                        echo "  1. 確認 Scripts 目錄 (如 C:\\Users\\<USER>\\AppData\\Local\\Programs\\Python\\Python311\\Scripts) 已加入 PATH"
                        echo "  2. 執行: $PYTHON_CMD -m pip install --upgrade pip setuptools wheel"
                        echo "  3. 重裝 CLI: $PYTHON_CMD -m pip install -U qai-hub qai-hub-models"
                        echo "  4. 再次執行: qai-hub configure --api_token <TOKEN>"
                    fi
                fi
            fi
        else
            echo -e "${BLUE}ℹ️ 跳過 ARM64 套件安裝${NC}"
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
