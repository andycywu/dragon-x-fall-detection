@echo off
setlocal enabledelayedexpansion

echo [INFO] QDC Windows 環境一鍵設置腳本

rem 設置顏色
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "BLUE=[34m"
set "NC=[0m"

rem 設置配置文件路徑
set "CONFIG_FILE=%USERPROFILE%\.qdc_config.txt"

rem 設置默認值
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

rem 準備設置腳本
echo %YELLOW%[INFO]%NC% 準備設置腳本...
set "SETUP_SCRIPT=%TEMP%\qdc_setup.bat"
copy /y "%~dp0qdc_setup.bat" "%SETUP_SCRIPT%" > nul
echo %GREEN%[SUCCESS]%NC% 設置腳本已準備: %SETUP_SCRIPT%

rem 啟動SSH隧道
echo %YELLOW%[INFO]%NC% 啟動SSH隧道...
echo %BLUE%[COMMAND]%NC% ssh -i "!SSH_KEY_PATH!" -L !LOCAL_PORT!:!REMOTE_HOST!:!REMOTE_PORT! -N sshtunnel@ssh.qdc.qualcomm.com
start "" ssh -i "!SSH_KEY_PATH!" -L !LOCAL_PORT!:!REMOTE_HOST!:!REMOTE_PORT! -N sshtunnel@ssh.qdc.qualcomm.com

rem 等待隧道建立
echo %YELLOW%[INFO]%NC% 等待隧道建立 (5秒)...
timeout /t 5 /nobreak > nul

rem 檢測遠程環境
echo %YELLOW%[INFO]%NC% 檢測遠程環境...
ssh -i "!SSH_KEY_PATH!" -p !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null !USERNAME!@localhost "ver" > "%TEMP%\qdc_os_check.txt" 2>&1
findstr /i "Microsoft Windows" "%TEMP%\qdc_os_check.txt" > nul
if %ERRORLEVEL% EQU 0 (
    echo %BLUE%[INFO]%NC% 檢測到 Windows 操作系統
    set "IS_WINDOWS=1"
) else (
    echo %BLUE%[INFO]%NC% 檢測到 Unix/Linux 操作系統
    set "IS_WINDOWS=0"
)

rem 上傳設置腳本
echo %YELLOW%[INFO]%NC% 上傳設置腳本到遠程...
if "!IS_WINDOWS!"=="1" (
    rem Windows環境
    set "REMOTE_HOME=C:\Users\!USERNAME!"
    set "REMOTE_SCRIPT=!REMOTE_HOME!\qdc_setup.bat"
    
    echo %BLUE%[INFO]%NC% 使用Windows風格路徑: !REMOTE_SCRIPT!
    echo %BLUE%[INFO]%NC% 嘗試使用SCP上傳...
    
    scp -i "!SSH_KEY_PATH!" -P !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "%~dp0qdc_setup.bat" !USERNAME!@localhost:!REMOTE_SCRIPT! > nul 2>&1
    
    if %ERRORLEVEL% NEQ 0 (
        echo %YELLOW%[WARN]%NC% SCP上傳失敗，嘗試替代方法...
        
        rem 使用SSH和cat命令組合上傳
        echo %BLUE%[INFO]%NC% 使用SSH命令直接創建文件...
        ssh -i "!SSH_KEY_PATH!" -p !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null !USERNAME!@localhost "copy nul !REMOTE_SCRIPT!" > nul 2>&1
        
        rem 分塊上傳文件內容
        for /f "usebackq delims=" %%a in ("%~dp0qdc_setup.bat") do (
            set "line=%%a"
            set "line=!line:\=\\!"
            set "line=!line:"=\"!"
            ssh -i "!SSH_KEY_PATH!" -p !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null !USERNAME!@localhost "echo !line! >> !REMOTE_SCRIPT!" > nul 2>&1
        )
    )
) else (
    rem Unix/Linux環境
    set "REMOTE_HOME=/home/!USERNAME!"
    set "REMOTE_SCRIPT=!REMOTE_HOME!/qdc_setup.sh"
    
    echo %BLUE%[INFO]%NC% 使用Unix風格路徑: !REMOTE_SCRIPT!
    scp -i "!SSH_KEY_PATH!" -P !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "%~dp0qdc_setup.sh" !USERNAME!@localhost:!REMOTE_SCRIPT!
    
    if %ERRORLEVEL% NEQ 0 (
        echo %YELLOW%[WARN]%NC% SCP上傳失敗，嘗試替代方法...
        ssh -i "!SSH_KEY_PATH!" -p !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null !USERNAME!@localhost "cat > !REMOTE_SCRIPT!" < "%~dp0qdc_setup.sh"
    )
)

echo %GREEN%[SUCCESS]%NC% 設置腳本已上傳

rem 執行遠程設置腳本
echo %YELLOW%[INFO]%NC% 開始在QDC中執行設置...

if "!IS_WINDOWS!"=="1" (
    echo %BLUE%[INFO]%NC% 在Windows環境下執行.bat腳本
    ssh -i "!SSH_KEY_PATH!" -p !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null !USERNAME!@localhost "cd !REMOTE_HOME! && qdc_setup.bat"
) else (
    echo %BLUE%[INFO]%NC% 在Unix/Linux環境下執行.sh腳本
    ssh -i "!SSH_KEY_PATH!" -p !LOCAL_PORT! -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null !USERNAME!@localhost "chmod +x !REMOTE_SCRIPT! && !REMOTE_SCRIPT!"
)

echo %GREEN%[SUCCESS]%NC% QDC環境設置完成!

endlocal
