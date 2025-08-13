#!/bin/bash
# QDC 安裝包準備腳本

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🐉 Dragon X Fall Detection System${NC}"
echo -e "${CYAN}QDC 安裝包準備腳本${NC}"
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

cat > "$SCRIPTS_DIR/install.ps1" << 'EOL'
# Dragon X Fall Detection System
# QDC 自動安裝腳本 (PowerShell)

Write-Host "🐉 Dragon X Fall Detection System - QDC 自動安裝" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 確定腳本路徑
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackagePath = Split-Path -Parent $ScriptPath

# 設置日誌檔案
$LogFile = Join-Path $ScriptPath "install_log.txt"
Start-Transcript -Path $LogFile -Append

Write-Host "📋 安裝記錄將保存到: $LogFile" -ForegroundColor Yellow

# 設置環境變數以避免互動式提示
$env:GIT_REDIRECT_STDERR = "2>&1"

# 安裝 Git
$GitInstaller = Join-Path $PackagePath "Git-2.40.0-64-bit.exe"
if (Test-Path $GitInstaller) {
    Write-Host "🔄 安裝 Git..." -ForegroundColor Yellow
    try {
        Start-Process -FilePath $GitInstaller -ArgumentList "/VERYSILENT", "/NORESTART" -Wait
        Write-Host "✅ Git 安裝成功" -ForegroundColor Green
    } catch {
        Write-Host "❌ Git 安裝失敗: $_" -ForegroundColor Red
    }
} else {
    Write-Host "❌ 找不到 Git 安裝檔: $GitInstaller" -ForegroundColor Red
}

# 安裝 Python
$PythonInstaller = Join-Path $PackagePath "python-3.10.11-amd64.exe"
if (Test-Path $PythonInstaller) {
    Write-Host "🔄 安裝 Python..." -ForegroundColor Yellow
    try {
        Start-Process -FilePath $PythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait
        Write-Host "✅ Python 安裝成功" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python 安裝失敗: $_" -ForegroundColor Red
    }
} else {
    Write-Host "❌ 找不到 Python 安裝檔: $PythonInstaller" -ForegroundColor Red
}

# 刷新環境變數
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 驗證安裝
Write-Host "🔍 驗證安裝..." -ForegroundColor Yellow

# 檢查 Git
try {
    $GitVersion = git --version
    Write-Host "✅ Git 已安裝: $GitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git 驗證失敗" -ForegroundColor Red
}

# 檢查 Python
try {
    $PythonVersion = python --version
    Write-Host "✅ Python 已安裝: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 驗證失敗" -ForegroundColor Red
}

# 克隆專案
Write-Host "🔍 檢查專案倉庫..." -ForegroundColor Yellow
if (-not (Test-Path "C:\dragon-x-fall-detection")) {
    Write-Host "🔄 克隆 GitHub 倉庫..." -ForegroundColor Yellow
    try {
        Set-Location C:\
        git clone https://github.com/andycywu/dragon-x-fall-detection.git
        Write-Host "✅ 倉庫克隆成功" -ForegroundColor Green
    } catch {
        Write-Host "❌ 克隆倉庫失敗: $_" -ForegroundColor Red
    }
} else {
    Write-Host "ℹ️ 倉庫已存在，正在更新..." -ForegroundColor Blue
    try {
        Set-Location C:\dragon-x-fall-detection
        git pull
        Write-Host "✅ 倉庫更新完成" -ForegroundColor Green
    } catch {
        Write-Host "❌ 更新倉庫失敗: $_" -ForegroundColor Red
    }
}

# 配置 QAI Hub
Write-Host "🔄 設置 QAI Hub 配置..." -ForegroundColor Yellow
try {
    $QaiHubDir = "$env:USERPROFILE\.qai_hub"
    if (-not (Test-Path $QaiHubDir)) {
        New-Item -Path $QaiHubDir -ItemType Directory -Force | Out-Null
    }
    
    $ConfigContent = @"
[default]
api_token = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
api_key = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
base_api_url = https://app.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
"@
    
    Set-Content -Path "$QaiHubDir\client.ini" -Value $ConfigContent
    Write-Host "✅ QAI Hub 配置完成" -ForegroundColor Green
} catch {
    Write-Host "❌ QAI Hub 配置失敗: $_" -ForegroundColor Red
}

# 安裝 Python 套件
if (Test-Path "C:\dragon-x-fall-detection") {
    Write-Host "🔄 安裝 Python 套件..." -ForegroundColor Yellow
    try {
        Set-Location C:\dragon-x-fall-detection
        pip install numpy opencv-python onnxruntime
        pip install -r requirements.txt
        pip install -U qai-hub qai-hub-models "protobuf==4.25.3"
        Write-Host "✅ Python 套件安裝完成" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python 套件安裝失敗: $_" -ForegroundColor Red
    }
}

# 創建自動啟動捷徑
Write-Host "🔄 創建桌面捷徑..." -ForegroundColor Yellow
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Dragon X Fall Detection.lnk")
    $Shortcut.TargetPath = "cmd.exe"
    $Shortcut.Arguments = "/k cd C:\dragon-x-fall-detection && python dragon_x_fall_detection_system.py"
    $Shortcut.WorkingDirectory = "C:\dragon-x-fall-detection"
    $Shortcut.Save()
    Write-Host "✅ 桌面捷徑創建完成" -ForegroundColor Green
} catch {
    Write-Host "❌ 桌面捷徑創建失敗: $_" -ForegroundColor Red
}

Write-Host "`n🎉 Dragon X Fall Detection System - 安裝完成！" -ForegroundColor Cyan
Write-Host "您可以通過桌面捷徑或以下命令運行系統:" -ForegroundColor Cyan
Write-Host "   cd C:\dragon-x-fall-detection" -ForegroundColor White
Write-Host "   python dragon_x_fall_detection_system.py" -ForegroundColor White
Write-Host "`n完整安裝日誌可在此查看: $LogFile" -ForegroundColor Yellow

Stop-Transcript
EOL

# 創建自動運行批處理檔
echo -e "${YELLOW}📝 創建自動運行批處理檔...${NC}"

cat > "$PACKAGE_DIR/run_installer.bat" << 'EOL'
@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0\scripts\install.ps1"
EOL

# 創建自動運行批處理檔 (System32)
cat > "$PACKAGE_DIR/RunMe.bat" << 'EOL'
@echo off
echo 🐉 Dragon X Fall Detection System - QDC 自動安裝
echo =========================================
echo.
echo 正在啟動安裝程序，請勿關閉此窗口...
echo.
start "" powershell -ExecutionPolicy Bypass -File "%~dp0\scripts\install.ps1"
echo.
echo 如果安裝程序沒有自動啟動，請手動運行 scripts\install.ps1
echo.
pause
EOL

# 創建說明文件
echo -e "${YELLOW}📝 創建說明文件...${NC}"

cat > "$PACKAGE_DIR/README.txt" << 'EOL'
Dragon X Fall Detection System - QDC 安裝包
==========================================

此安裝包包含：
1. Git 安裝程序
2. Python 3.10 安裝程序
3. 自動安裝腳本

安裝說明：
1. 雙擊運行 "RunMe.bat"
2. 等待安裝完成
3. 安裝完成後，可以通過桌面捷徑或命令運行系統

手動安裝方式：
1. 運行 Git-2.40.0-64-bit.exe 安裝 Git
2. 運行 python-3.10.11-amd64.exe 安裝 Python
3. 運行 PowerShell 腳本：
   powershell -ExecutionPolicy Bypass -File "scripts\install.ps1"

Dragon X Team
==========================================
EOL

# 創建 zip 包
echo -e "${YELLOW}📦 創建 zip 包...${NC}"
cd "$WORK_DIR"
zip -r qdc_installer.zip package/

echo -e "${GREEN}✅ QDC 安裝包準備完成: $WORK_DIR/qdc_installer.zip${NC}"
echo -e "${BLUE}ℹ️ 在 QDC 創建 session 時上傳此 zip 包，系統將自動安裝所需環境${NC}"
echo ""
