@echo off
chcp 65001 > nul
REM 在 Qualcomm Snapdragon X Elite 設備上強制 git pull 並覆蓋本地更改
REM 使用方法: git_pull_overwrite.bat

echo ===== 強制 git pull 並覆蓋本地更改 =====
echo 警告: 此操作將會丟失所有未提交的本地更改！
echo.

REM 確認用戶真的想要執行此操作
set /p CONFIRM=您確定要繼續嗎？這將會丟失所有未提交的本地更改！(y/n): 
if /i "%CONFIRM%" neq "y" (
  echo 操作已取消。
  exit /b 0
)

echo.
echo 正在執行強制 git pull...

REM 放棄所有本地更改
echo 放棄所有本地更改...
git reset --hard

REM 清理未跟踪的文件和目錄
echo 刪除所有未跟踪的文件...
git clean -fd

REM 拉取最新的代碼
echo 從遠程倉庫拉取最新代碼...
git pull origin main

REM 檢查操作是否成功
if %errorlevel% equ 0 (
  echo.
  echo ===== 操作成功完成 =====
  echo 已強制拉取最新代碼並覆蓋所有本地更改。
) else (
  echo.
  echo ===== 操作失敗 =====
  echo 拉取代碼時出錯，請檢查網絡連接或倉庫狀態。
)

echo.
pause
