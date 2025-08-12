#!/bin/bash
# Dragon X 跌倒檢測系統啟動腳本

# 檢測操作系統
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="mac"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="windows"
else
    PLATFORM="other"
fi

# 顯示歡迎訊息
echo "========================================"
echo "   Dragon X 跌倒檢測系統 - 啟動工具"
echo "========================================"
echo ""

# 檢查 Python 環境
echo "檢查 Python 環境..."
if ! command -v python3 &> /dev/null; then
    echo "錯誤: 找不到 Python 3。請安裝 Python 3.8 或更高版本。"
    exit 1
fi

# 檢查是否已安裝依賴
echo "檢查依賴..."
REQUIREMENTS_FILE="requirements.txt"
if [ "$PLATFORM" = "windows" ]; then
    REQUIREMENTS_FILE="requirements_windows.txt"
fi

INSTALL_DEPS=0
if [ ! -d "venv" ]; then
    echo "未找到虛擬環境。需要創建新的環境並安裝依賴。"
    INSTALL_DEPS=1
else
    read -p "是否檢查並更新依賴? (y/n): " CHECK_DEPS
    if [ "$CHECK_DEPS" = "y" ] || [ "$CHECK_DEPS" = "Y" ]; then
        INSTALL_DEPS=1
    fi
fi

# 創建並設置虛擬環境
if [ $INSTALL_DEPS -eq 1 ]; then
    echo "設置 Python 虛擬環境..."
    python3 -m venv venv
    
    # 激活虛擬環境
    if [ "$PLATFORM" = "windows" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    # 安裝依賴
    echo "安裝依賴..."
    pip install -r $REQUIREMENTS_FILE
else
    # 激活虛擬環境
    if [ "$PLATFORM" = "windows" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
fi

# 運行適當的主程序
echo ""
echo "請選擇要運行的系統版本:"
echo "1) 標準版 (Mac/Unix)"
echo "2) Windows 版"
echo "3) 跨平台兼容版"
echo "q) 退出"

read -p "請選擇 [1-3, q]: " CHOICE

case $CHOICE in
    1)
        echo "啟動標準版系統..."
        python main.py
        ;;
    2)
        echo "啟動 Windows 版系統..."
        python main_windows.py
        ;;
    3)
        echo "啟動跨平台兼容版系統..."
        python main_compatible.py
        ;;
    q|Q)
        echo "退出..."
        ;;
    *)
        echo "無效選擇，退出..."
        ;;
esac

# 退出虛擬環境
deactivate
echo "系統已關閉。"
