@echo off
echo 🐉 Dragon X Fall Detection System - QDC 自動安裝
echo =========================================
echo.
echo 正在啟動安裝程序，請勿關閉此窗口...
echo.

:: 確定當前目錄
set "CURRENT_DIR=%~dp0"
set "SCRIPT_PATH=%CURRENT_DIR%scripts\install.ps1"

:: 檢查腳本是否存在
if not exist "%SCRIPT_PATH%" (
    echo 錯誤: 找不到安裝腳本: %SCRIPT_PATH%
    echo 請確保安裝包正確解壓
    goto error
)

:: 使用絕對路徑運行 PowerShell 腳本
echo 運行安裝腳本: %SCRIPT_PATH%
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_PATH%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 安裝腳本執行失敗，請查看錯誤信息
    goto error
) else (
    echo.
    echo 安裝腳本執行完成！
    goto end
)

:error
echo.
echo 如需手動安裝，請依次執行:
echo 1. 運行 Git-2.40.0-64-bit.exe 安裝 Git
echo 2. 運行 python-3.10.11-amd64.exe 安裝 Python
echo 3. 重新嘗試運行此批處理文件
echo.

:end
pause
