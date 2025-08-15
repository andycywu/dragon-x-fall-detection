# 在 Qualcomm Snapdragon X Elite 設備上強制 git pull 並覆蓋本地更改
# 使用方法: .\git_pull_overwrite.ps1

Write-Host "===== 強制 git pull 並覆蓋本地更改 =====" -ForegroundColor Red
Write-Host "警告: 此操作將會丟失所有未提交的本地更改！" -ForegroundColor Yellow
Write-Host ""

# 確認用戶真的想要執行此操作
$confirm = Read-Host "您確定要繼續嗎？這將會丟失所有未提交的本地更改！(y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "操作已取消。" -ForegroundColor Cyan
    exit 0
}

Write-Host ""
Write-Host "正在執行強制 git pull..." -ForegroundColor Cyan

# 放棄所有本地更改
Write-Host "放棄所有本地更改..." -ForegroundColor Yellow
git reset --hard

# 清理未跟踪的文件和目錄
Write-Host "刪除所有未跟踪的文件..." -ForegroundColor Yellow
git clean -fd

# 拉取最新的代碼
Write-Host "從遠程倉庫拉取最新代碼..." -ForegroundColor Green
$pullResult = git pull origin main
$exitCode = $LASTEXITCODE

# 檢查操作是否成功
if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "===== 操作成功完成 =====" -ForegroundColor Green
    Write-Host "已強制拉取最新代碼並覆蓋所有本地更改。" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "===== 操作失敗 =====" -ForegroundColor Red
    Write-Host "拉取代碼時出錯，請檢查網絡連接或倉庫狀態。" -ForegroundColor Red
}

Write-Host ""
Write-Host "按任意鍵繼續..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
