@echo off
chcp 65001 > nul
REM 解決 Qualcomm Snapdragon X Elite 上的 git pull 衝突問題
REM 使用方法: fix_git_pull_conflicts.bat

echo ===== 解決 git pull 衝突並拉取最新代碼 =====

REM 檢查是否為 git 存儲庫
if not exist ".git" (
  echo 錯誤: 此目錄不是 git 存儲庫
  echo 請在正確的存儲庫目錄中運行此腳本
  exit /b 1
)

REM 創建備份目錄
echo 創建臨時備份目錄...
if not exist "backup_temp" mkdir backup_temp

REM 備份已修改的文件
echo 備份已修改的文件...
if exist "device_cloud_setup.py" copy device_cloud_setup.py backup_temp\

REM 備份未跟踪的文件
echo 備份未跟踪的文件...
if exist "device_cloud_launch.bat" copy device_cloud_launch.bat backup_temp\
if exist "device_cloud_setup_ascii.py" copy device_cloud_setup_ascii.py backup_temp\
if exist "device_cloud_setup_fixed.py" copy device_cloud_setup_fixed.py backup_temp\
if exist "install_packages.bat" copy install_packages.bat backup_temp\
if exist "qai_hub_config.json" copy qai_hub_config.json backup_temp\

REM 執行 git stash 儲存修改
echo 執行 git stash 保存修改...
git stash

REM 移動未跟踪的文件
echo 移動未跟踪的文件...
if exist "device_cloud_launch.bat" move device_cloud_launch.bat backup_temp\
if exist "device_cloud_setup_ascii.py" move device_cloud_setup_ascii.py backup_temp\
if exist "device_cloud_setup_fixed.py" move device_cloud_setup_fixed.py backup_temp\
if exist "install_packages.bat" move install_packages.bat backup_temp\
if exist "qai_hub_config.json" move qai_hub_config.json backup_temp\

REM 執行 git pull
echo 正在從 GitHub 拉取最新代碼...
git pull origin main

REM 檢查拉取是否成功
if %errorlevel% equ 0 (
  echo 成功拉取最新的代碼！
) else (
  echo 拉取時出現問題，請檢查錯誤訊息
  goto :restore_files
)

REM 恢復文件
:restore_files
echo 恢復備份的文件...

REM 檢查是否需要手動合併 device_cloud_setup.py
if exist "backup_temp\device_cloud_setup.py" (
  echo.
  echo === 注意: device_cloud_setup.py 已被修改 ===
  echo 1. 遠端版本已保存在當前目錄
  echo 2. 您的本地修改版本保存在 backup_temp 目錄
  echo 請手動比較並合併這兩個文件
  echo.
)

REM 恢復未跟踪的文件
echo 恢復未跟踪的文件...
if exist "backup_temp\device_cloud_launch.bat" copy backup_temp\device_cloud_launch.bat .\
if exist "backup_temp\device_cloud_setup_ascii.py" copy backup_temp\device_cloud_setup_ascii.py .\
if exist "backup_temp\device_cloud_setup_fixed.py" copy backup_temp\device_cloud_setup_fixed.py .\
if exist "backup_temp\install_packages.bat" copy backup_temp\install_packages.bat .\
if exist "backup_temp\qai_hub_config.json" copy backup_temp\qai_hub_config.json .\

REM 應用之前儲存的更改
echo 嘗試恢復之前的修改...
git stash pop

echo.
echo ===== 操作完成 =====
echo 1. 最新代碼已從 GitHub 拉取
echo 2. 您的本地修改和未跟踪的文件已還原
echo 3. 如果出現衝突，請手動解決
echo.
echo 備份目錄 backup_temp 保留以供參考
echo 確認一切正常後，您可以刪除備份目錄

pause
