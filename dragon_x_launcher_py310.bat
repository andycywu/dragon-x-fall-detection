@echo off
REM 使用 Python 3.10 執行 Dragon X Fall Detection 系統
echo 正在使用 Python 3.10 啟動 Dragon X Fall Detection 系統...

REM 設定 Python 3.10 的路徑
set PYTHON_PATH=C:\Users\HCKTest\AppData\Local\Programs\Python\Python310\python.exe

REM 設定 UTF-8 編碼環境變數
set PYTHONIOENCODING=utf-8
chcp 65001 > nul

REM 執行主程式
"%PYTHON_PATH%" C:\dragon-x-fall-detection\dragon_x_fall_detection_system.py

echo 程式已完成執行。
pause

echo 程式已完成執行。
pause
