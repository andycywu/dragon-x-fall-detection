# 在 Qualcomm Snapdragon X Elite Windows 11 裝置上拉取最新的程式碼
# 使用方法: .\qualcomm_pull_latest.ps1

Write-Host "===== 在 Qualcomm Snapdragon X Elite 裝置上拉取最新的程式碼 =====" -ForegroundColor Cyan
Write-Host "開始更新本地存儲庫..." -ForegroundColor Green

# 確保我們在正確的目錄中
Set-Location -Path $PSScriptRoot

# 檢查是否為 git 存儲庫
if (-not (Test-Path ".git")) {
    Write-Host "錯誤: 此目錄不是 git 存儲庫" -ForegroundColor Red
    Write-Host "請在正確的存儲庫目錄中運行此腳本" -ForegroundColor Red
    exit 1
}

# 檢查網絡連接
Write-Host "檢查網絡連接..." -ForegroundColor Yellow
$pingResult = Test-Connection -ComputerName github.com -Count 1 -Quiet
if (-not $pingResult) {
    Write-Host "警告: 無法連接到 GitHub，請檢查您的網絡連接" -ForegroundColor Yellow
    Write-Host "嘗試繼續..." -ForegroundColor Yellow
}

# 保存本地更改（如果有的話）
$status = git status --porcelain
if ($status) {
    Write-Host "檢測到本地更改，正在保存..." -ForegroundColor Yellow
    git stash
    $stashed = $true
} else {
    $stashed = $false
}

# 拉取最新更改
Write-Host "正在從 GitHub 拉取最新更改..." -ForegroundColor Green
$pullResult = git pull origin main
$exitCode = $LASTEXITCODE

# 檢查拉取是否成功
if ($exitCode -eq 0) {
    Write-Host "成功拉取最新的程式碼！" -ForegroundColor Green
} else {
    Write-Host "拉取時出現問題，請檢查錯誤訊息" -ForegroundColor Red
}

# 恢復之前的本地更改（如果有的話）
if ($stashed) {
    Write-Host "正在恢復本地更改..." -ForegroundColor Yellow
    git stash pop
    Write-Host "本地更改已恢復" -ForegroundColor Green
}

Write-Host "===== 完成 =====" -ForegroundColor Cyan
Write-Host "若需要任何協助，請聯繫開發團隊" -ForegroundColor White
Write-Host ""
Write-Host "按任意鍵退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
