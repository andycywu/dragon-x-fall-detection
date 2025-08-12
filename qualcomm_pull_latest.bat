@echo off
REM 在 Qualcomm Snapdragon X Elite Windows 11 裝置上拉取最新的程式碼
REM 使用方法: qualcomm_pull_latest.bat

echo ===== 在 Qualcomm Snapdragon X Elite 裝置上拉取最新的程式碼 =====
echo 開始更新本地存儲庫...

REM 確保我們在正確的目錄中
cd /d "%~dp0" || (
  echo 無法進入腳本目錄
  exit /b 1
)

REM 檢查是否為 git 存儲庫
if not exist ".git" (
  echo 錯誤: 此目錄不是 git 存儲庫
  echo 請在正確的存儲庫目錄中運行此腳本
  exit /b 1
)

REM 檢查網絡連接
echo 檢查網絡連接...
ping -n 1 github.com >nul 2>&1
if %errorlevel% neq 0 (
  echo 警告: 無法連接到 GitHub，請檢查您的網絡連接
  echo 嘗試繼續...
)

REM 保存本地更改（如果有的話）
git status --porcelain > temp.txt
for /f %%i in ("temp.txt") do set size=%%~zi
if %size% gtr 0 (
  echo 檢測到本地更改，正在保存...
  git stash
  set "STASHED=true"
) else (
  set "STASHED=false"
)
del temp.txt

REM 拉取最新更改
echo 正在從 GitHub 拉取最新更改...
git pull origin main

REM 檢查拉取是否成功
if %errorlevel% equ 0 (
  echo 成功拉取最新的程式碼！
) else (
  echo 拉取時出現問題，請檢查錯誤訊息
)

REM 恢復之前的本地更改（如果有的話）
if "%STASHED%"=="true" (
  echo 正在恢復本地更改...
  git stash pop
  echo 本地更改已恢復
)

echo ===== 完成 =====
echo 若需要任何協助，請聯繫開發團隊

pause
