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




# 啟動選單與主程式執行
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

echo "系統已關閉。"
