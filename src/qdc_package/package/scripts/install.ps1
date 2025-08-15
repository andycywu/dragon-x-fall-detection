# Dragon X Fall Detection System
# QDC 自動安裝腳本 (PowerShell)

# 啟用錯誤處理
$ErrorActionPreference = "Stop"

# 函數: 寫入帶顏色的消息
function Write-ColorMessage {
    param (
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    
    Write-Host $Message -ForegroundColor $ForegroundColor
}

# 開始安裝
Clear-Host
Write-ColorMessage "🐉 Dragon X Fall Detection System - QDC 自動安裝" -ForegroundColor Cyan
Write-ColorMessage "=========================================" -ForegroundColor Cyan
Write-ColorMessage ""

# 確定腳本路徑
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackagePath = Split-Path -Parent $ScriptPath

# 設置日誌檔案
$LogFile = Join-Path $ScriptPath "install_log.txt"
try {
    Start-Transcript -Path $LogFile -Append -ErrorAction SilentlyContinue
    Write-ColorMessage "📋 安裝記錄將保存到: $LogFile" -ForegroundColor Yellow
} catch {
    Write-ColorMessage "⚠️ 無法創建日誌文件，繼續安裝但不記錄日誌" -ForegroundColor Yellow
}

# 檢查安裝檔案是否存在
$GitInstaller = Join-Path $PackagePath "Git-2.40.0-64-bit.exe"
$PythonInstaller = Join-Path $PackagePath "python-3.10.11-amd64.exe"

$FilesExist = $true

if (-not (Test-Path $GitInstaller)) {
    Write-ColorMessage "❌ 找不到 Git 安裝檔: $GitInstaller" -ForegroundColor Red
    $FilesExist = $false
}

if (-not (Test-Path $PythonInstaller)) {
    Write-ColorMessage "❌ 找不到 Python 安裝檔: $PythonInstaller" -ForegroundColor Red
    $FilesExist = $false
}

if (-not $FilesExist) {
    Write-ColorMessage "❌ 缺少必要安裝檔案，請確保安裝包完整解壓" -ForegroundColor Red
    return
}

# 安裝 Git
Write-ColorMessage "`n🔄 安裝 Git..." -ForegroundColor Yellow
try {
    # 使用絕對路徑並檢查進程是否已存在
    $process = Start-Process -FilePath $GitInstaller -ArgumentList "/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES" -PassThru -Wait
    if ($process.ExitCode -eq 0) {
        Write-ColorMessage "✅ Git 安裝成功" -ForegroundColor Green
    } else {
        Write-ColorMessage "❌ Git 安裝失敗，退出代碼: $($process.ExitCode)" -ForegroundColor Red
    }
} catch {
    Write-ColorMessage "❌ Git 安裝出錯: $_" -ForegroundColor Red
}

# 等待一下確保安裝完成
Start-Sleep -Seconds 5

# 安裝 Python
Write-ColorMessage "`n🔄 安裝 Python..." -ForegroundColor Yellow
try {
    # 使用絕對路徑並設置更詳細的參數
    $process = Start-Process -FilePath $PythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0", "Include_pip=1" -PassThru -Wait
    if ($process.ExitCode -eq 0) {
        Write-ColorMessage "✅ Python 安裝成功" -ForegroundColor Green
    } else {
        Write-ColorMessage "❌ Python 安裝失敗，退出代碼: $($process.ExitCode)" -ForegroundColor Red
    }
} catch {
    Write-ColorMessage "❌ Python 安裝出錯: $_" -ForegroundColor Red
}

# 等待一下確保安裝完成
Start-Sleep -Seconds 5

# 刷新環境變數
Write-ColorMessage "`n🔄 更新環境變數..." -ForegroundColor Yellow
try {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-ColorMessage "✅ 環境變數已更新" -ForegroundColor Green
} catch {
    Write-ColorMessage "❌ 環境變數更新失敗: $_" -ForegroundColor Red
}

# 驗證安裝
Write-ColorMessage "`n🔍 驗證安裝..." -ForegroundColor Yellow

# 檢查 Git
$gitInstalled = $false
try {
    # 使用絕對路徑嘗試執行 Git
    $gitPath = "C:\Program Files\Git\bin\git.exe"
    if (Test-Path $gitPath) {
        $GitVersion = & $gitPath --version
        Write-ColorMessage "✅ Git 已安裝: $GitVersion" -ForegroundColor Green
        $gitInstalled = $true
    } else {
        # 嘗試在 PATH 中查找
        $GitVersion = git --version
        Write-ColorMessage "✅ Git 已安裝: $GitVersion" -ForegroundColor Green
        $gitInstalled = $true
    }
} catch {
    Write-ColorMessage "❌ Git 驗證失敗，可能需要重啟 CMD 或 PowerShell" -ForegroundColor Red
}

# 檢查 Python
$pythonInstalled = $false
try {
    # 使用絕對路徑嘗試執行 Python
    $pythonPath = "C:\Program Files\Python310\python.exe"
    if (Test-Path $pythonPath) {
        $PythonVersion = & $pythonPath --version
        Write-ColorMessage "✅ Python 已安裝: $PythonVersion" -ForegroundColor Green
        $pythonInstalled = $true
    } else {
        # 嘗試在 PATH 中查找
        $PythonVersion = python --version
        Write-ColorMessage "✅ Python 已安裝: $PythonVersion" -ForegroundColor Green
        $pythonInstalled = $true
    }
} catch {
    Write-ColorMessage "❌ Python 驗證失敗，可能需要重啟 CMD 或 PowerShell" -ForegroundColor Red
}

# 如果 Git 和 Python 都已成功安裝，繼續克隆和設置
if ($gitInstalled -and $pythonInstalled) {
    # 克隆專案
    Write-ColorMessage "`n🔍 檢查專案倉庫..." -ForegroundColor Yellow
    if (-not (Test-Path "C:\dragon-x-fall-detection")) {
        Write-ColorMessage "🔄 克隆 GitHub 倉庫..." -ForegroundColor Yellow
        try {
            Set-Location C:\
            & $gitPath clone https://github.com/andycywu/dragon-x-fall-detection.git
            if ($LASTEXITCODE -eq 0) {
                Write-ColorMessage "✅ 倉庫克隆成功" -ForegroundColor Green
            } else {
                Write-ColorMessage "❌ 克隆倉庫失敗，退出代碼: $LASTEXITCODE" -ForegroundColor Red
            }
        } catch {
            Write-ColorMessage "❌ 克隆倉庫出錯: $_" -ForegroundColor Red
        }
    } else {
        Write-ColorMessage "ℹ️ 倉庫已存在，正在更新..." -ForegroundColor Blue
        try {
            Set-Location C:\dragon-x-fall-detection
            & $gitPath pull
            if ($LASTEXITCODE -eq 0) {
                Write-ColorMessage "✅ 倉庫更新完成" -ForegroundColor Green
            } else {
                Write-ColorMessage "❌ 更新倉庫失敗，退出代碼: $LASTEXITCODE" -ForegroundColor Red
            }
        } catch {
            Write-ColorMessage "❌ 更新倉庫出錯: $_" -ForegroundColor Red
        }
    }

    # 配置 QAI Hub
    Write-ColorMessage "`n🔄 設置 QAI Hub 配置..." -ForegroundColor Yellow
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
        Write-ColorMessage "✅ QAI Hub 配置完成" -ForegroundColor Green
    } catch {
        Write-ColorMessage "❌ QAI Hub 配置失敗: $_" -ForegroundColor Red
    }

    # 安裝 Python 套件
    if (Test-Path "C:\dragon-x-fall-detection") {
        Write-ColorMessage "`n🔄 安裝 Python 套件..." -ForegroundColor Yellow
        try {
            Set-Location C:\dragon-x-fall-detection
            & $pythonPath -m pip install numpy opencv-python onnxruntime
            & $pythonPath -m pip install -r requirements.txt
            & $pythonPath -m pip install -U qai-hub qai-hub-models "protobuf==4.25.3"
            Write-ColorMessage "✅ Python 套件安裝完成" -ForegroundColor Green
        } catch {
            Write-ColorMessage "❌ Python 套件安裝失敗: $_" -ForegroundColor Red
        }
    }

    # 創建自動啟動捷徑
    Write-ColorMessage "`n🔄 創建桌面捷徑..." -ForegroundColor Yellow
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Dragon X Fall Detection.lnk")
        $Shortcut.TargetPath = "cmd.exe"
        $Shortcut.Arguments = "/k cd C:\dragon-x-fall-detection && $pythonPath dragon_x_fall_detection_system.py"
        $Shortcut.WorkingDirectory = "C:\dragon-x-fall-detection"
        $Shortcut.Save()
        Write-ColorMessage "✅ 桌面捷徑創建完成" -ForegroundColor Green
    } catch {
        Write-ColorMessage "❌ 桌面捷徑創建失敗: $_" -ForegroundColor Red
    }

    Write-ColorMessage "`n🎉 Dragon X Fall Detection System - 安裝完成！" -ForegroundColor Cyan
    Write-ColorMessage "您可以通過桌面捷徑或以下命令運行系統:" -ForegroundColor Cyan
    Write-ColorMessage "   cd C:\dragon-x-fall-detection" -ForegroundColor White
    Write-ColorMessage "   python dragon_x_fall_detection_system.py" -ForegroundColor White
    
} else {
    Write-ColorMessage "`n⚠️ Git 或 Python 安裝未能完成" -ForegroundColor Yellow
    Write-ColorMessage "請重啟電腦後再嘗試運行應用程序" -ForegroundColor Yellow
}

Write-ColorMessage "`n完整安裝日誌可在此查看: $LogFile" -ForegroundColor Yellow

try {
    Stop-Transcript -ErrorAction SilentlyContinue
} catch {
    # 忽略停止日誌時的錯誤
}

# 返回成功代碼
exit 0
