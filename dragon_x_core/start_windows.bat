@echo off
chcp 65001 > nul
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
set "REQUIREMENTS_FILE=requirements_windows.txt"
if not exist "%REQUIREMENTS_FILE%" (
    set "REQUIREMENTS_FILE=requirements.txt"
)

set "INSTALL_DEPS=0"
if not exist venv\ (
    echo 未找到虛擬環境。需要創建新的環境並安裝依賴。
    set "INSTALL_DEPS=1"
) else (
    set /p CHECK_DEPS=是否檢查並更新依賴? (y/n): 
    if /i "%CHECK_DEPS%"=="y" (
        set "INSTALL_DEPS=1"
    )
)

REM 創建並設置虛擬環境
if "%INSTALL_DEPS%"=="1" (
    echo 設置 Python 虛擬環境...
    python -m venv venv
)

REM 嘗試激活虛擬環境（若存在）
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM 若需要安裝依賴，執行安裝
if "%INSTALL_DEPS%"=="1" (
    echo 安裝依賴...
    if exist "%REQUIREMENTS_FILE%" (
        pip install -r "%REQUIREMENTS_FILE%"
    ) else (
        echo 找不到依賴檔案：%REQUIREMENTS_FILE%
    )
)

echo.
echo 請選擇要運行的系統版本:
echo 1) 標準版 (不建議在 Windows 上使用)
echo 2) Windows 版
echo 3) 跨平台兼容版
echo 4) Dragon X 強化版推論啟動 (QAI Hub/相機回退)
echo q) 退出

set /p CHOICE=請選擇 [1-4, q]: 

if "%CHOICE%"=="1" goto RUN_STD
if "%CHOICE%"=="2" goto RUN_WIN
if "%CHOICE%"=="3" goto RUN_COMP
if /i "%CHOICE%"=="q" goto QUIT
if "%CHOICE%"=="4" goto RUN_ENHANCED

echo 無效選擇，退出...
goto DEACT

:RUN_STD
echo 啟動標準版系統...
python main.py
goto DEACT

:RUN_WIN
echo 啟動 Windows 版系統...
python main_windows.py
goto DEACT

:RUN_COMP
echo 啟動跨平台兼容版系統...
python main_compatible.py
goto DEACT

:RUN_ENHANCED
echo 啟動 Dragon X 強化版推論（QAI Hub/相機回退）...
REM 從 core 目錄回到根目錄後啟動統一啟動器批次檔
if exist ..\run_dragon_x_real_inference_ascii_fixed.bat (
    call ..\run_dragon_x_real_inference_ascii_fixed.bat run-app
) else (
    echo 未找到統一啟動器：..\run_dragon_x_real_inference_ascii_fixed.bat
)
goto DEACT

:DEACT
REM 退出虛擬環境（若有）
if exist venv\Scripts\deactivate.bat (
    call venv\Scripts\deactivate.bat
)
echo 系統已關閉。
pause
goto :eof

:QUIT
echo 退出...
goto DEACT
