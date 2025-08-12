@echo off
REM Dragon X 跌倒檢測系統啟動腳本 - Windows 版本

echo ========================================
echo    Dragon X 跌倒檢測系統 - 啟動工具
echo ========================================
echo.

REM 檢查 Python 環境
echo 檢查 Python 環境...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 錯誤: 找不到 Python。請安裝 Python 3.8 或更高版本。
    pause
    exit /b 1
)

REM 檢查是否已安裝依賴
echo 檢查依賴...
set REQUIREMENTS_FILE=requirements_windows.txt
if not exist %REQUIREMENTS_FILE% (
    set REQUIREMENTS_FILE=requirements.txt
)

set INSTALL_DEPS=0
if not exist venv\ (
    echo 未找到虛擬環境。需要創建新的環境並安裝依賴。
    set INSTALL_DEPS=1
) else (
    set /p CHECK_DEPS=是否檢查並更新依賴? (y/n): 
    if /i "%CHECK_DEPS%"=="y" (
        set INSTALL_DEPS=1
    )
)

REM 創建並設置虛擬環境
if %INSTALL_DEPS%==1 (
    echo 設置 Python 虛擬環境...
    python -m venv venv
    
    REM 激活虛擬環境
    call venv\Scripts\activate.bat
    
    REM 安裝依賴
    echo 安裝依賴...
    pip install -r %REQUIREMENTS_FILE%
) else (
    REM 激活虛擬環境
    call venv\Scripts\activate.bat
)

echo.
echo 請選擇要運行的系統版本:
echo 1) 標準版 (不建議在 Windows 上使用)
echo 2) Windows 版
echo 3) 跨平台兼容版
echo q) 退出

set /p CHOICE=請選擇 [1-3, q]: 

if "%CHOICE%"=="1" (
    echo 啟動標準版系統...
    python main.py
) else if "%CHOICE%"=="2" (
    echo 啟動 Windows 版系統...
    python main_windows.py
) else if "%CHOICE%"=="3" (
    echo 啟動跨平台兼容版系統...
    python main_compatible.py
) else if /i "%CHOICE%"=="q" (
    echo 退出...
) else (
    echo 無效選擇，退出...
)

REM 退出虛擬環境
call venv\Scripts\deactivate.bat
echo 系統已關閉。
pause
