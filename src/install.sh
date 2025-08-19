PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo -e "\n⚠️ 偵測到 Python 3.13，scipy 等科學套件尚未支援此版本。\n將自動安裝並切換到 Python 3.10 (需 pyenv)..."
    if command -v pyenv >/dev/null 2>&1; then
        pyenv install -s 3.10.14
        export PYENV_VERSION=3.10.14
        export PATH="$(pyenv root)/shims:$PATH"
        echo -e "\n✅ 已切換到 Python 3.10.14，將重新執行安裝腳本...\n"
        exec bash "$0"
        exit 0
    else
        echo -e "❌ 未安裝 pyenv，請手動安裝 pyenv 或切換 Python 版本至 3.10/3.11。"
        exit 1
    fi
fi

#!/bin/bash
# install.sh - 跨平台自動安裝與 QDC 連接整合腳本
# 支援 macOS (ARM64/Intel)、Windows (x86/ARM64)、Linux

set -e

# 取得本腳本所在目錄，所有相對路徑都以此為基準
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 顯示歡迎訊息
CYAN='\033[0;36m'
NC='\033[0m'
echo -e "${CYAN}🐉 Dragon X Fall Detection System - 跨平台安裝啟動${NC}"
echo -e "=============================================="

# 互動式選單：讓使用者選擇安裝情境
UNAME_S="$(uname -s)"
UNAME_M="$(uname -m)"

echo -e "\n請選擇安裝情境："
echo "  1) 自動偵測 (推薦)"
echo "  2) QDC Cloud Device (遠端自動安裝)"
echo "  3) macOS ARM64 (Apple Silicon)"
echo "  4) Windows ARM64 (Snapdragon X Elite)"
echo "  5) Windows x86 (Intel/AMD)"
echo "  6) Linux (x86/ARM)"
read -p "請輸入選項 [1-6] (預設1): " INSTALL_CHOICE
INSTALL_CHOICE=${INSTALL_CHOICE:-1}

case $INSTALL_CHOICE in
    2)
        PLATFORM="qdc_cloud"
        ;;
    3)
        PLATFORM="macos_arm64"
        ;;
    4)
        PLATFORM="windows_arm64"
        ;;
    5)
        PLATFORM="windows_x86"
        ;;
    6)
        PLATFORM="linux"
        ;;
    *)
        # 自動偵測
        if [[ "$UNAME_S" =~ ^MINGW|^CYGWIN|^MSYS ]]; then
            PLATFORM="windows"
        elif [[ "$UNAME_S" == "Darwin" ]]; then
            if [[ "$UNAME_M" == "arm64" ]]; then
                PLATFORM="macos_arm64"
            else
                PLATFORM="macos_x86"
            fi
        elif [[ "$UNAME_S" == "Linux" ]]; then
            PLATFORM="linux"
        else
            PLATFORM="unknown"
        fi
        ;;
esac

echo -e "\n選擇的安裝情境: $PLATFORM ($UNAME_S/$UNAME_M)"

# 新增：用途選擇
USE_CASE=""
echo -e "\n請選擇安裝用途："
echo "  1) 推論 (Infer)"
echo "  2) QAI Hub 模型最佳化 (QAI Hub Optimize)"
echo "  3) Snapdragon NPU 部署 (Snapdragon/CRD 推論加速)"
read -p "請輸入選項 [1-3] (預設1): " USE_CASE_CHOICE
USE_CASE_CHOICE=${USE_CASE_CHOICE:-1}
case $USE_CASE_CHOICE in
    2)
        USE_CASE="qaihub"
        ;;
    3)
        USE_CASE="snapdragon"
        ;;
    *)
        USE_CASE="infer"
        ;;
esac




# 1. 先檢查 src 目錄下是否有 .venv 或 .venv_mediapipe，若有則移除
if [ -d ".venv" ]; then
    echo -e "\n⚠️  src 目錄下偵測到 .venv，將自動移除..."
    rm -rf .venv
fi
if [ -d ".venv_mediapipe" ]; then
    echo -e "\n⚠️  src 目錄下偵測到 .venv_mediapipe，將自動移除..."
    rm -rf .venv_mediapipe
fi

# 1.1 macOS ARM64 自動安裝 gfortran、openblas（for scipy/scientific packages）
if [[ "$PLATFORM" == "macos_arm64" ]]; then
    if ! command -v gfortran >/dev/null 2>&1; then
        echo -e "\n🔧 未偵測到 gfortran，將自動安裝 (需 Homebrew)..."
        if command -v brew >/dev/null 2>&1; then
            brew install gfortran
        else
            echo -e "❌ 未安裝 Homebrew，請先安裝 Homebrew 再重試。"
            exit 1
        fi
    fi
    if ! brew list openblas >/dev/null 2>&1; then
        echo -e "\n🔧 未偵測到 openblas，將自動安裝 (需 Homebrew)..."
        brew install openblas
    fi
fi

# 2. 自動建立/切換對應用途的 venv（以腳本目錄為基準）
VENV_SCRIPT=""
if [[ "$USE_CASE" == "qaihub" ]]; then
    VENV_SCRIPT="$SCRIPT_DIR/qaihub_optimize/venv_setup.sh"
elif [[ "$USE_CASE" == "snapdragon" ]]; then
    VENV_SCRIPT="$SCRIPT_DIR/snapdragon_npu/venv_setup.sh"
else
    VENV_SCRIPT="$SCRIPT_DIR/infer_demo/venv_setup.sh"
fi

echo -e "\n🔎 將自動建立並啟用專屬虛擬環境: $VENV_SCRIPT"


if [[ -f "$VENV_SCRIPT" ]]; then
    bash "$VENV_SCRIPT"
else
    echo -e "❌ 找不到 $VENV_SCRIPT，請確認腳本存在。"
    exit 1
fi

# 2. 整合 QDC 連接腳本
if [[ "$PLATFORM" == "qdc_cloud" ]]; then
    echo -e "\n☁️ QDC Cloud Device - 自動執行 QDC 連接腳本..."
    if [[ "$UNAME_S" == "Darwin" || "$UNAME_S" == "Linux" ]]; then
        bash ./qdc_auto_connect.sh
    else
        cmd.exe /c qdc_auto_connect.bat
    fi
    exit 0
else
    echo -e "\n${CYAN}✨ Dragon X Fall Detection System - 本地安裝完成！${NC}"
    echo -e "----------------------------------------------"
    echo -e "【本地啟動說明】"
    echo -e "1. 啟動虛擬環境（如有）: source .venv_mediapipe/bin/activate"
    echo -e "2. 執行主程式: python dragon_x_fall_detection_system.py"
    echo -e "3. 或參考 README.md 進行測試與啟動"
    echo -e "4. 如需連接 QDC，請手動執行 qdc_auto_connect.sh/bat"
    echo -e "----------------------------------------------"
    # 根據用途提示 demo 目錄
    if [[ "$USE_CASE" == "infer" ]]; then
        echo -e "\n🚀 本地推論/效能展示腳本："
        echo -e "  cd src/infer_demo && python hackathon_final_demo.py"
    elif [[ "$USE_CASE" == "qaihub" ]]; then
        echo -e "\n🚀 QAI Hub 模型最佳化/技術展示腳本："
        echo -e "  cd src/qaihub_optimize && python qai_hub_simple_demo.py"
    elif [[ "$USE_CASE" == "snapdragon" ]]; then
        echo -e "\n🚀 Snapdragon NPU 部署/推論 demo："
        echo -e "  cd src/snapdragon_npu && python snapdragon_realtime_demo.py"
    fi
    echo -e "----------------------------------------------"
fi
