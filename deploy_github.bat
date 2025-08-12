@echo off
REM Device Cloud Windows部署腳本

echo 🐉 在Device Cloud上部署Dragon X Fall Detection System
echo ==================================================

REM 創建項目目錄
set PROJ_DIR=C:\dragon_x_fall_detection
if not exist %PROJ_DIR% mkdir %PROJ_DIR%
cd /d %PROJ_DIR%

REM 檢查Git是否已安裝
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git未安裝，請先安裝Git
    echo 可以使用 git_installer.bat 安裝
    exit /b 1
)

REM 設置GitHub倉庫URL
set GITHUB_REPO=https://github.com/andycywu/dragon-x-fall-detection.git
echo 🌐 使用GitHub倉庫: %GITHUB_REPO%

REM 克隆或更新倉庫
if exist .git (
    echo 🔄 更新現有倉庫...
    git pull origin main
) else (
    echo 📥 克隆GitHub倉庫...
    git clone %GITHUB_REPO% .
)

REM 檢查Python環境
echo 🐍 檢查Python環境...
python --version

REM 運行設置腳本
if exist device_cloud_setup.py (
    echo 🚀 運行設置腳本...
    python device_cloud_setup.py
) else (
    echo ⚠️ 設置腳本不存在
)

echo ✅ 部署完成！
echo 📋 項目位置: %PROJ_DIR%
echo 可以執行以下命令測試:
echo    cd %PROJ_DIR%
echo    python unified_ai_detector.py
echo    python dragon_x_fall_detection_system.py
echo    python hackathon_final_demo.py
