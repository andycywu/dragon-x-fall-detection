@echo off
REM QDC (Qualcomm Device Cloud) 設置腳本 - Windows 版
REM 此腳本用於在 QDC Windows 環境中設置和配置

echo 🐉 Dragon X Fall Detection System
echo Qualcomm Device Cloud 設置腳本 - QDC 端 (Windows)
echo ==============================================

REM 檢查Python
echo 檢查Python安裝...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python未安裝，請先安裝Python
    exit /b 1
)

echo Python版本:
python --version

REM 項目目錄
set "PROJ_DIR=C:\dragon_x_fall_detection"
echo 項目目錄: %PROJ_DIR%

REM 創建項目目錄
echo 創建項目目錄...
if not exist "%PROJ_DIR%" mkdir "%PROJ_DIR%"
cd /d "%PROJ_DIR%"

REM 檢查Git
echo 檢查Git安裝...
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo Git未安裝，請先安裝Git
    exit /b 1
)

REM 克隆或更新GitHub倉庫
set GITHUB_REPO=https://github.com/andycywu/dragon-x-fall-detection.git
echo 使用GitHub倉庫: %GITHUB_REPO%

if exist ".git" (
    echo 倉庫已存在，更新代碼...
    git pull origin main
) else (
    echo 克隆GitHub倉庫...
    git clone %GITHUB_REPO% .
    if %errorlevel% neq 0 (
        echo 克隆倉庫失敗
        exit /b 1
    )
)

REM 安裝Python套件
echo 安裝Python套件...
pip install numpy opencv-python onnxruntime
pip install -r requirements.txt

REM 設置QAI Hub
echo 設置QAI Hub...
pip install -U qai-hub qai-hub-models "protobuf==4.25.3"

REM 設置QAI Hub認證
echo 設置QAI Hub認證...
if not exist "%USERPROFILE%\.qai_hub" mkdir "%USERPROFILE%\.qai_hub"
echo [default] > "%USERPROFILE%\.qai_hub\client.ini"
echo api_token = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d >> "%USERPROFILE%\.qai_hub\client.ini"
echo api_key = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d >> "%USERPROFILE%\.qai_hub\client.ini"
echo base_api_url = https://app.aihub.qualcomm.com >> "%USERPROFILE%\.qai_hub\client.ini"
echo web_url = https://app.aihub.qualcomm.com >> "%USERPROFILE%\.qai_hub\client.ini"

REM 測試QAI Hub連接
echo 測試QAI Hub連接...
python -c "import qai_hub as hub; print('可用設備:', [d.name for d in hub.get_devices()])" 2>nul
if %errorlevel% neq 0 (
    echo QAI Hub 連接失敗，請手動修復設置
) else (
    echo QAI Hub 連接成功
)

echo ✅ QDC設置完成！
echo ==============================================
echo 📋 可執行的指令:
echo 1. 運行AI檢測系統:
echo    python unified_ai_detector.py
echo    python dragon_x_fall_detection_system.py
echo    python hackathon_final_demo.py
echo.
echo 2. 更新系統 (當GitHub有新變更時):
echo    cd %PROJ_DIR% ^&^& git pull
echo.
echo 🐉 準備在Snapdragon X Elite上測試你的AI系統！
