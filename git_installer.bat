@echo off
chcp 65001 > nul
REM Windows上安裝Git的腳本

echo 📦 在Windows上安裝Git...
echo ======================================

REM 檢查是否已安裝Git
where git >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Git已經安裝，版本信息:
    git --version
    exit /b 0
)

echo 🔍 檢測系統架構...
if exist "%ProgramFiles(x86)%" (
    echo 檢測到64位系統
    set ARCH=64
) else (
    echo 檢測到32位系統
    set ARCH=32
)

echo 📥 下載Git安裝程序...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.39.0.windows.1/Git-2.39.0-win%ARCH%-bit.exe' -OutFile '%TEMP%\git_installer.exe'}"

if %errorlevel% neq 0 (
    echo ❌ 下載Git安裝程序失敗
    echo 請手動訪問 https://git-scm.com/download/win 下載並安裝Git
    exit /b 1
)

echo 🚀 開始安裝Git...
echo 安裝程序將在後台運行，請等待...
start /wait %TEMP%\git_installer.exe /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS

echo 清理臨時文件...
del %TEMP%\git_installer.exe

echo ✅ Git安裝完成，重新打開命令行後生效
echo 請重新登錄或重啟計算機，然後運行 'git --version' 驗證安裝
