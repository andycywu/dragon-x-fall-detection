@echo off
setlocal enabledelayedexpansion

echo [INFO] QDC Windows 環境 SSH 連接腳本

rem 設置顏色
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "BLUE=[34m"
set "NC=[0m"

rem 設置配置文件路徑
set "CONFIG_FILE=%USERPROFILE%\.qdc_config.txt"

rem 檢查配置文件是否存在
if not exist "%CONFIG_FILE%" (
    echo %RED%[ERROR]%NC% 配置文件不存在: %CONFIG_FILE%
    echo %YELLOW%[提示]%NC% 請先運行 qdc_auto_connect.bat 設置配置
    exit /b 1
)

rem 讀取配置文件
echo %BLUE%[INFO]%NC% 讀取配置文件: %CONFIG_FILE%
for /f "tokens=1,* delims==" %%a in (%CONFIG_FILE%) do (
    if "%%a"=="USERNAME" set "USERNAME=%%b"
    if "%%a"=="LOCAL_PORT" set "LOCAL_PORT=%%b"
    if "%%a"=="SSH_KEY_PATH" set "SSH_KEY_PATH=%%b"
)

rem 檢查配置是否完整
if not defined USERNAME (
    echo %RED%[ERROR]%NC% 用戶名未設置
    exit /b 1
)
if not defined LOCAL_PORT (
    echo %RED%[ERROR]%NC% 本地端口未設置
    exit /b 1
)
if not defined SSH_KEY_PATH (
    echo %RED%[ERROR]%NC% SSH密鑰路徑未設置
    exit /b 1
)

rem 啟動SSH連接
echo %YELLOW%[INFO]%NC% 連接到QDC...
echo %BLUE%[COMMAND]%NC% ssh -i "!SSH_KEY_PATH!" -p !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null !USERNAME!@localhost
ssh -i "!SSH_KEY_PATH!" -p !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null !USERNAME!@localhost

echo %GREEN%[SUCCESS]%NC% SSH連接已完成

endlocal
