#!/bin/bash
# QDC 安裝包準備腳本 - 修正版

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🐉 Dragon X Fall Detection System${NC}"
echo -e "${CYAN}QDC 安裝包準備腳本 (修正版)${NC}"
echo "=============================================="

# 設置目錄
WORK_DIR="$(pwd)/qdc_package"
DOWNLOAD_DIR="$WORK_DIR/downloads"
PACKAGE_DIR="$WORK_DIR/package"
SCRIPTS_DIR="$PACKAGE_DIR/scripts"

# 創建目錄
mkdir -p "$DOWNLOAD_DIR"
mkdir -p "$SCRIPTS_DIR"

echo -e "${YELLOW}📂 創建工作目錄: $WORK_DIR${NC}"

# 下載安裝檔
echo -e "${YELLOW}📥 開始下載 Git 和 Python 安裝檔...${NC}"

# 下載 Git
GIT_URL="https://github.com/git-for-windows/git/releases/download/v2.40.0.windows.1/Git-2.40.0-64-bit.exe"
GIT_INSTALLER="$DOWNLOAD_DIR/Git-2.40.0-64-bit.exe"

if [ ! -f "$GIT_INSTALLER" ]; then
    echo -e "${BLUE}ℹ️ 下載 Git 安裝程序...${NC}"
    curl -L "$GIT_URL" -o "$GIT_INSTALLER"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Git 安裝檔下載成功${NC}"
    else
        echo -e "${RED}❌ Git 安裝檔下載失敗${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 已存在 Git 安裝檔${NC}"
fi

# 複製 Git 安裝檔到打包目錄
cp "$GIT_INSTALLER" "$PACKAGE_DIR/"

# 下載 Python
PYTHON_URL="https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
PYTHON_INSTALLER="$DOWNLOAD_DIR/python-3.10.11-amd64.exe"

if [ ! -f "$PYTHON_INSTALLER" ]; then
    echo -e "${BLUE}ℹ️ 下載 Python 安裝程序...${NC}"
    curl -L "$PYTHON_URL" -o "$PYTHON_INSTALLER"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Python 安裝檔下載成功${NC}"
    else
        echo -e "${RED}❌ Python 安裝檔下載失敗${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 已存在 Python 安裝檔${NC}"
fi

# 複製 Python 安裝檔到打包目錄
cp "$PYTHON_INSTALLER" "$PACKAGE_DIR/"

# 創建 PowerShell 安裝腳本
echo -e "${YELLOW}📝 創建 PowerShell 安裝腳本...${NC}"

# 使用修正後的安裝腳本
cp "$(pwd)/fixed_install.ps1" "$SCRIPTS_DIR/install.ps1"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PowerShell 安裝腳本複製成功${NC}"
else
    echo -e "${RED}❌ PowerShell 安裝腳本複製失敗${NC}"
    
    # 創建一個基本版本的腳本
    cat > "$SCRIPTS_DIR/install.ps1" << 'EOL'
# Dragon X Fall Detection System
# QDC 自動安裝腳本 (PowerShell) - 簡化版

# 啟用錯誤處理
$ErrorActionPreference = "Stop"

# 開始安裝
Write-Host "🐉 Dragon X Fall Detection System - QDC 自動安裝" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 確定腳本路徑
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackagePath = Split-Path -Parent $ScriptPath

# 檢查安裝檔案是否存在
$GitInstaller = Join-Path $PackagePath "Git-2.40.0-64-bit.exe"
$PythonInstaller = Join-Path $PackagePath "python-3.10.11-amd64.exe"

if (-not (Test-Path $GitInstaller)) {
    Write-Host "❌ 找不到 Git 安裝檔: $GitInstaller" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $PythonInstaller)) {
    Write-Host "❌ 找不到 Python 安裝檔: $PythonInstaller" -ForegroundColor Red
    exit 1
}

# 安裝 Git
Write-Host "🔄 安裝 Git..." -ForegroundColor Yellow
Start-Process -FilePath $GitInstaller -ArgumentList "/VERYSILENT", "/NORESTART" -Wait
Write-Host "✅ Git 安裝完成" -ForegroundColor Green

# 安裝 Python
Write-Host "🔄 安裝 Python..." -ForegroundColor Yellow
Start-Process -FilePath $PythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait
Write-Host "✅ Python 安裝完成" -ForegroundColor Green

# 刷新環境變數
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "🎉 安裝完成！" -ForegroundColor Green
Write-Host "請重啟命令提示符後執行 git --version 和 python --version 檢查安裝" -ForegroundColor Yellow

pause
EOL
    echo -e "${YELLOW}⚠️ 已創建簡化版 PowerShell 安裝腳本${NC}"
fi

# 創建自動運行批處理檔
echo -e "${YELLOW}📝 創建自動運行批處理檔...${NC}"

# 使用修正後的批處理檔
cp "$(pwd)/fixed_RunMe.bat" "$PACKAGE_DIR/RunMe.bat"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 自動運行批處理檔複製成功${NC}"
else
    echo -e "${RED}❌ 自動運行批處理檔複製失敗${NC}"
    
    # 創建一個基本版本的批處理檔
    cat > "$PACKAGE_DIR/RunMe.bat" << 'EOL'
@echo off
echo 🐉 Dragon X Fall Detection System - QDC 自動安裝
echo =========================================
echo.
echo 正在啟動安裝程序，請勿關閉此窗口...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0\scripts\install.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo 安裝腳本執行失敗，請查看錯誤信息
) else (
    echo 安裝腳本執行完成！
)

pause
EOL
    echo -e "${YELLOW}⚠️ 已創建簡化版自動運行批處理檔${NC}"
fi

# 創建說明文件
echo -e "${YELLOW}📝 創建說明文件...${NC}"

cat > "$PACKAGE_DIR/README.txt" << 'EOL'
Dragon X Fall Detection System - QDC 安裝包 (修正版)
==========================================

此安裝包包含：
1. Git 安裝程序
2. Python 3.10 安裝程序
3. 自動安裝腳本

安裝說明：
1. 雙擊運行 "RunMe.bat"
2. 等待安裝完成
3. 重啟電腦（重要！）
4. 安裝完成後，打開命令提示符運行系統

手動安裝方式（如自動安裝失敗）：
1. 雙擊運行 Git-2.40.0-64-bit.exe 安裝 Git
2. 雙擊運行 python-3.10.11-amd64.exe 安裝 Python
3. 重啟電腦
4. 開啟命令提示符，執行：
   cd C:\
   git clone https://github.com/andycywu/dragon-x-fall-detection.git
   cd dragon-x-fall-detection
   pip install numpy opencv-python onnxruntime
   pip install -r requirements.txt
   pip install -U qai-hub qai-hub-models "protobuf==4.25.3"
   python dragon_x_fall_detection_system.py

故障排除：
1. 如果安裝過程中出現錯誤，請查看 scripts 資料夾中的日誌文件
2. 確保安裝過程中有管理員權限
3. 安裝後必須重啟電腦，確保環境變數生效

Dragon X Team
==========================================
EOL

# 創建 zip 包
echo -e "${YELLOW}📦 創建 zip 包...${NC}"
cd "$WORK_DIR"
zip -r qdc_installer_fixed.zip package/

echo -e "${GREEN}✅ QDC 安裝包準備完成: $WORK_DIR/qdc_installer_fixed.zip${NC}"
echo -e "${BLUE}ℹ️ 在 QDC 創建 session 時上傳此 zip 包，系統將自動安裝所需環境${NC}"
echo ""
