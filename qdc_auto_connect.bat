@echo off
setlocal enabledelayedexpansion

echo [INFO] QDC Windows 環境自動連接腳本

rem 設置顏色
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "BLUE=[34m"
set "NC=[0m"

rem 設置默認值
set "CONFIG_FILE=%USERPROFILE%\.qdc_config.txt"
set "DEFAULT_USERNAME=u2380"
set "DEFAULT_LOCAL_PORT=2222"
set "DEFAULT_REMOTE_HOST=sa297036.sa.svc.cluster.local"
set "DEFAULT_REMOTE_PORT=22"
set "DEFAULT_SSH_KEY_PATH=%USERPROFILE%\.ssh\id_rsa"

rem 讀取配置文件（如果存在）
if exist "%CONFIG_FILE%" (
    echo %BLUE%[INFO]%NC% 讀取配置文件: %CONFIG_FILE%
    for /f "tokens=1,* delims==" %%a in (%CONFIG_FILE%) do (
        if "%%a"=="USERNAME" set "DEFAULT_USERNAME=%%b"
        if "%%a"=="LOCAL_PORT" set "DEFAULT_LOCAL_PORT=%%b"
        if "%%a"=="REMOTE_HOST" set "DEFAULT_REMOTE_HOST=%%b"
        if "%%a"=="REMOTE_PORT" set "DEFAULT_REMOTE_PORT=%%b"
        if "%%a"=="SSH_KEY_PATH" set "DEFAULT_SSH_KEY_PATH=%%b"
    )
)

rem 設置輸入參數
set /p "USERNAME=請輸入用戶名 [%DEFAULT_USERNAME%]: "
if "!USERNAME!"=="" set "USERNAME=%DEFAULT_USERNAME%"

set /p "LOCAL_PORT=請輸入本地端口 [%DEFAULT_LOCAL_PORT%]: "
if "!LOCAL_PORT!"=="" set "LOCAL_PORT=%DEFAULT_LOCAL_PORT%"

set /p "REMOTE_HOST=請輸入遠程主機（每日變動）[%DEFAULT_REMOTE_HOST%]: "
if "!REMOTE_HOST!"=="" set "REMOTE_HOST=%DEFAULT_REMOTE_HOST%"

set /p "REMOTE_PORT=請輸入遠程端口 [%DEFAULT_REMOTE_PORT%]: "
if "!REMOTE_PORT!"=="" set "REMOTE_PORT=%DEFAULT_REMOTE_PORT%"

set /p "SSH_KEY_PATH=請輸入SSH密鑰路徑 [%DEFAULT_SSH_KEY_PATH%]: "
if "!SSH_KEY_PATH!"=="" set "SSH_KEY_PATH=%DEFAULT_SSH_KEY_PATH%"

rem 保存配置
echo %YELLOW%[INFO]%NC% 保存配置到: %CONFIG_FILE%
(
    echo USERNAME=!USERNAME!
    echo LOCAL_PORT=!LOCAL_PORT!
    echo REMOTE_HOST=!REMOTE_HOST!
    echo REMOTE_PORT=!REMOTE_PORT!
    echo SSH_KEY_PATH=!SSH_KEY_PATH!
) > "%CONFIG_FILE%"

rem 啟動SSH隧道
echo %YELLOW%[INFO]%NC% 啟動SSH隧道...
echo %BLUE%[COMMAND]%NC% ssh -i "!SSH_KEY_PATH!" -L !LOCAL_PORT!:!REMOTE_HOST!:!REMOTE_PORT! -N sshtunnel@ssh.qdc.qualcomm.com
start "" ssh -i "!SSH_KEY_PATH!" -L !LOCAL_PORT!:!REMOTE_HOST!:!REMOTE_PORT! -N sshtunnel@ssh.qdc.qualcomm.com

rem 等待隧道建立
echo %YELLOW%[INFO]%NC% 等待隧道建立 (5秒)...
timeout /t 5 /nobreak > nul

rem 啟動SSH連接
echo %YELLOW%[INFO]%NC% 連接到QDC...
echo %BLUE%[COMMAND]%NC% ssh -i "!SSH_KEY_PATH!" -p !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null !USERNAME!@localhost
ssh -i "!SSH_KEY_PATH!" -p !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null !USERNAME!@localhost

echo %GREEN%[SUCCESS]%NC% SSH連接已完成

endlocal
