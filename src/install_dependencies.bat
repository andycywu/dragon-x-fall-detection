@echo off
chcp 65001 > nul
:: Dragon X Fall Detection System 依賴包安裝腳本 (Windows 版本)
echo 🐉 Dragon X Fall Detection System - 環境設置
echo ===============================================

:: 檢查 Python 環境
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ 找不到 Python，請安裝後再試。
    exit /b 1
)

:: 顯示檢測到的平台信息
echo 📊 系統信息:
echo OS: Windows
wmic OS get OSArchitecture | findstr /i "64-bit" >nul
if %ERRORLEVEL% equ 0 (
    echo 架構: 64-bit
    
    :: 檢查是否為 ARM64
    wmic cpu get caption | findstr /i "ARM" >nul
    if %ERRORLEVEL% equ 0 (
        echo ✅ 檢測到 ARM64 架構 (Snapdragon)
    )
)

python --version

:: 檢查虛擬環境
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️ 未檢測到虛擬環境。建議使用虛擬環境安裝依賴。
    echo 要繼續安裝嗎？(Y/N)
    choice /c YN /m "選擇"
    if errorlevel 2 (
        echo 🛑 安裝已取消。請先設置虛擬環境後再試。
        exit /b 1
    )
) else (
    echo ✅ 使用虛擬環境: %VIRTUAL_ENV%
)

:: 執行平台特定安裝腳本
echo 🔧 開始安裝平台優化依賴包...
python install_platform_accelerators.py

echo ✨ 安裝完成！您現在可以開始使用 Dragon X Fall Detection 系統。
pause
