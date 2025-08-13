@echo off
chcp 65001 >nul
echo =========================================================
echo            QAI Hub 簡易配置修復工具
echo =========================================================
echo.

echo 檢查 Python 安裝...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 錯誤: 未找到 Python。請安裝 Python 3.6 或更高版本。
    goto :END
)

echo Python 已安裝。
echo.

echo 創建/更新 QAI Hub 配置...
set config_dir=%USERPROFILE%\.qai_hub
set config_file=%config_dir%\client.ini

if not exist %config_dir% (
    echo 創建配置目錄...
    mkdir %config_dir%
)

echo 寫入新配置，使用最新的 API URL...
echo [default]> %config_file%
echo api_token=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
echo api_key=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
echo base_api_url=https://api.aihub.qualcomm.com>> %config_file%
echo web_url=https://app.aihub.qualcomm.com>> %config_file%

echo 配置文件已更新: %config_file%
echo.

echo 驗證 QAI Hub 安裝...
pip show qai-hub >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo QAI Hub 未安裝。是否要安裝？ (Y/N)
    set /p install_choice=
    if /i "%install_choice%"=="Y" (
        echo 正在安裝 QAI Hub...
        pip install qai-hub==0.31.0 qai-hub-models==0.31.0
    ) else (
        echo 跳過 QAI Hub 安裝。
    )
) else (
    echo QAI Hub 已安裝。
)
echo.

echo 創建簡單測試腳本...
echo import os> test_qai_simple.py
echo import sys>> test_qai_simple.py
echo print("Python 版本:", sys.version)>> test_qai_simple.py
echo print("Python 執行檔:", sys.executable)>> test_qai_simple.py
echo.>> test_qai_simple.py
echo config_path = os.path.expanduser("~/.qai_hub/client.ini")>> test_qai_simple.py
echo print("配置文件路徑:", config_path)>> test_qai_simple.py
echo print("配置文件存在:", os.path.exists(config_path))>> test_qai_simple.py
echo.>> test_qai_simple.py
echo if os.path.exists(config_path):>> test_qai_simple.py
echo     print("配置內容:")>> test_qai_simple.py
echo     with open(config_path, "r") as f:>> test_qai_simple.py
echo         print(f.read())>> test_qai_simple.py
echo.>> test_qai_simple.py
echo try:>> test_qai_simple.py
echo     import qai_hub>> test_qai_simple.py
echo     print("QAI Hub 版本:", qai_hub.__version__)>> test_qai_simple.py
echo     print("嘗試連接到 QAI Hub...")>> test_qai_simple.py
echo     try:>> test_qai_simple.py
echo         devices = qai_hub.get_devices()>> test_qai_simple.py
echo         print("可用設備:", devices)>> test_qai_simple.py
echo         print("成功: QAI Hub 連接正常!")>> test_qai_simple.py
echo     except Exception as e:>> test_qai_simple.py
echo         print("錯誤: 無法連接到 QAI Hub API")>> test_qai_simple.py
echo         print("錯誤詳情:", str(e))>> test_qai_simple.py
echo except Exception as e:>> test_qai_simple.py
echo     print("錯誤: 無法導入 QAI Hub")>> test_qai_simple.py
echo     print("錯誤詳情:", str(e))>> test_qai_simple.py

echo 測試腳本已創建: test_qai_simple.py
echo.

echo 運行測試腳本...
echo =========================================================
python test_qai_simple.py
echo =========================================================
echo.

echo 如果您仍然看到連接錯誤，請嘗試以下操作:
echo 1. 檢查您的網絡連接
echo 2. 檢查 QAI_HUB_TROUBLESHOOTING.md 文件獲取更多幫助
echo 3. 確認配置文件中使用正確的 URL:
echo    base_api_url=https://api.aihub.qualcomm.com
echo    web_url=https://app.aihub.qualcomm.com
echo.

:END
echo 按任意鍵退出...
pause >nul
