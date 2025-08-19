@echo off
chcp 65001 >nul
echo =========================================================
echo           QAI Hub API URL 和令牌修復工具
echo =========================================================
echo.

echo 此工具將幫助您修復 QAI Hub 配置問題。
echo.

set config_dir=%USERPROFILE%\.qai_hub
set config_file=%config_dir%\client.ini

echo 步驟 1: 檢查現有配置...
if exist "%config_file%" (
    echo 在以下位置找到現有配置文件：
    echo %config_file%
    echo.
    echo 目前配置：
    type "%config_file%"
    echo.
) else (
    echo 未找到現有配置。
    echo 正在創建新的配置目錄...
    if not exist "%config_dir%" mkdir "%config_dir%"
)

echo 步驟 2: 檢查 QAI Hub 安裝...
python -c "import qai_hub; print('QAI Hub 版本:', qai_hub.__version__)" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo QAI Hub 未安裝或無法導入。
    echo 是否要安裝或更新 QAI Hub？ (Y/N)
    set /p install_choice=
    if /i "%install_choice%"=="Y" (
        echo 正在安裝 QAI Hub...
        pip install qai-hub==0.31.0 qai-hub-models==0.31.0
        echo 安裝完成。
    ) else (
        echo 跳過安裝。您需要手動安裝 QAI Hub。
    )
)

echo.
echo 步驟 3: 輸入您的 QAI Hub API 令牌（或按 Enter 使用預設值）
echo         （預設令牌：pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d）
set /p user_token=API 令牌: 

if "%user_token%"=="" (
    set api_token=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
) else (
    set api_token=%user_token%
)

echo.
echo 步驟 4: 設置正確的 API URL...
echo.
echo [default]> "%config_file%"
echo api_token=%api_token%>> "%config_file%"
echo api_key=%api_token%>> "%config_file%"
echo base_api_url=https://app.aihub.qualcomm.com>> "%config_file%"
echo web_url=https://app.aihub.qualcomm.com>> "%config_file%"
echo 使用官方 URL: https://app.aihub.qualcomm.com

echo.
echo 步驟 5: 檢查 Windows 長路徑支持...
reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled 2>nul | findstr "0x1" >nul
if %ERRORLEVEL% NEQ 0 (
    echo 警告：Windows 長路徑支持未啟用。
    echo 這可能會導致安裝 QAI Hub 套件時出現問題。
    echo.
    echo 是否要啟用 Windows 長路徑支持？ (Y/N)
    echo 注意：這需要管理員權限。
    set /p longpath_choice=
    if /i "%longpath_choice%"=="Y" (
        echo 正在創建註冊表文件...
        echo Windows Registry Editor Version 5.00> enable_long_paths.reg
        echo.>> enable_long_paths.reg
        echo [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem]>> enable_long_paths.reg
        echo "LongPathsEnabled"=dword:00000001>> enable_long_paths.reg
        
        echo 請以管理員身份運行 enable_long_paths.reg 並重啟計算機。
        echo 重啟後，再次運行此腳本完成設置。
    )
) else (
    echo Windows 長路徑支持已啟用。很好！
)

echo.
echo 配置已保存到: %config_file%
echo.

echo 步驟 6: 運行簡單測試以驗證配置...
echo import qai_hub as hub> verify_test.py
echo print("QAI Hub 版本:", hub.__version__)>> verify_test.py
echo try:>> verify_test.py
echo     devices = hub.get_devices()>> verify_test.py
echo     print("可用設備:", devices)>> verify_test.py
echo     print("QAI Hub 配置正常工作！")>> verify_test.py
echo except Exception as e:>> verify_test.py
echo     print("測試 QAI Hub 時出錯:", e)>> verify_test.py

echo.
echo 測試結果：
echo =========================================================
python verify_test.py
echo =========================================================
echo.

del verify_test.py >nul 2>&1

echo =========================================================
echo                       後續步驟
echo =========================================================
echo.
echo 1. 如果測試顯示「QAI Hub 配置正常工作！」，則設置成功！
echo 2. 如果仍有錯誤，請考慮：
echo    - 更新您的 QAI Hub 安裝：
echo      pip install -U qai-hub qai-hub-models
echo    - 嘗試與您的專案相容的特定版本：
echo      pip install qai-hub==0.31.0 qai-hub-models==0.31.0
echo    - 查看故障排除指南 (QAI_HUB_TROUBLESHOOTING.md)
echo.

echo 按任意鍵退出...
pause >nul
