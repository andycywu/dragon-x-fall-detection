@echo off
chcp 65001 >nul
echo =========================================================
echo           QAI Hub URL 設定工具
echo =========================================================
echo.

echo 此工具將設定 QAI Hub 使用正確的 URL
echo.

set config_dir=%USERPROFILE%\.qai_hub
set config_file=%config_dir%\client.ini

if not exist %config_dir% (
    mkdir %config_dir%
    echo 已創建配置目錄。
)

echo 正在設置臨時測試文件...
echo import qai_hub> test_url.py
echo print("URL 測試成功")>> test_url.py

echo 步驟 1: 設定 QAI Hub 配置...
echo [default]> %config_file%
echo api_token=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
echo api_key=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
echo base_api_url=https://app.aihub.qualcomm.com>> %config_file%
echo web_url=https://app.aihub.qualcomm.com>> %config_file%

timeout /t 2 /nobreak >nul
python test_url.py >nul 2>&1
set url_test_result=%ERRORLEVEL%

echo.
echo 清理臨時文件...
del test_url.py >nul 2>&1

echo.
if %url_test_result% EQU 0 (
    echo 配置成功！
) else (
    echo QAI Hub 配置可能需要額外設置。
    echo.
    echo 是否要更新您的 QAI Hub 安裝？ (Y/N)
    set /p update_choice=
    if /i "%update_choice%"=="Y" (
        echo 正在更新 QAI Hub...
        pip install qai-hub==0.31.0 qai-hub-models==0.31.0
        echo QAI Hub 更新完成。
    )
)

echo.
echo 配置已保存到: %config_file%
echo.

echo 運行簡單測試以驗證配置...
echo import qai_hub as hub> verify_test.py
echo print("QAI Hub 版本:", hub.__version__)>> verify_test.py
echo try:>> verify_test.py
echo     devices = hub.get_devices()>> verify_test.py
echo     print("可用設備:", devices)>> verify_test.py
echo     print("QAI Hub 配置正常工作！")>> verify_test.py
echo except Exception as e:>> verify_test.py
echo     print("測試 QAI Hub 時出錯:", e)>> verify_test.py

echo.
echo 測試結果:
echo =========================================================
python verify_test.py
echo =========================================================
echo.

del verify_test.py >nul 2>&1

echo =========================================================
echo                       後續步驟
echo =========================================================
echo.
echo 1. 如果測試顯示「QAI Hub 配置正常工作！」，則設定成功！
echo 2. 如果仍有錯誤，請考慮：
echo    - 更新您的 QAI Hub 安裝：
echo      pip install -U qai-hub qai-hub-models
echo    - 嘗試與您的項目相容的特定版本：
echo      pip install qai-hub==0.31.0 qai-hub-models==0.31.0
echo    - 查看故障排除指南 (QAI_HUB_TROUBLESHOOTING.md)
echo.

echo 按任意鍵退出...
pause >nul
