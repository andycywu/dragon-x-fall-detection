@echo off
chcp 65001 >nul
echo =========================================================
echo            QAI Hub Simple Config Fix Tool
echo =========================================================
echo.

echo Checking Python installation...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.6 or higher.
    goto :END
)

echo Python is installed.
echo.

echo Creating/updating QAI Hub configuration...
set config_dir=%USERPROFILE%\.qai_hub
set config_file=%config_dir%\client.ini

if not exist %config_dir% (
    echo Creating config directory...
    mkdir %config_dir%
)

echo Writing new configuration with the new API URL...
echo [default]> %config_file%
echo api_token=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
echo api_key=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
echo base_api_url=https://api.aihub.qualcomm.com>> %config_file%
echo web_url=https://app.aihub.qualcomm.com>> %config_file%

echo Configuration file updated at: %config_file%
echo.

echo Verifying QAI Hub installation...
pip show qai-hub >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo QAI Hub not installed. Would you like to install it? (Y/N)
    set /p install_choice=
    if /i "%install_choice%"=="Y" (
        echo Installing QAI Hub...
        pip install qai-hub==0.31.0 qai-hub-models==0.31.0
    ) else (
        echo Skipping QAI Hub installation.
    )
) else (
    echo QAI Hub is already installed.
)
echo.

echo Creating a simple test script...
echo import os> test_qai_simple.py
echo import sys>> test_qai_simple.py
echo print("Python version:", sys.version)>> test_qai_simple.py
echo print("Python executable:", sys.executable)>> test_qai_simple.py
echo.>> test_qai_simple.py
echo config_path = os.path.expanduser("~/.qai_hub/client.ini")>> test_qai_simple.py
echo print("Config file path:", config_path)>> test_qai_simple.py
echo print("Config exists:", os.path.exists(config_path))>> test_qai_simple.py
echo.>> test_qai_simple.py
echo if os.path.exists(config_path):>> test_qai_simple.py
echo     print("Config content:")>> test_qai_simple.py
echo     with open(config_path, "r") as f:>> test_qai_simple.py
echo         print(f.read())>> test_qai_simple.py
echo.>> test_qai_simple.py
echo try:>> test_qai_simple.py
echo     import qai_hub>> test_qai_simple.py
echo     print("QAI Hub version:", qai_hub.__version__)>> test_qai_simple.py
echo     print("Trying to connect to QAI Hub...")>> test_qai_simple.py
echo     try:>> test_qai_simple.py
echo         devices = qai_hub.get_devices()>> test_qai_simple.py
echo         print("Available devices:", devices)>> test_qai_simple.py
echo         print("SUCCESS: QAI Hub connection works!")>> test_qai_simple.py
echo     except Exception as e:>> test_qai_simple.py
echo         print("ERROR: Could not connect to QAI Hub API")>> test_qai_simple.py
echo         print("Error details:", str(e))>> test_qai_simple.py
echo except Exception as e:>> test_qai_simple.py
echo     print("ERROR: Could not import QAI Hub")>> test_qai_simple.py
echo     print("Error details:", str(e))>> test_qai_simple.py

echo Test script created: test_qai_simple.py
echo.

echo Running test script...
echo =========================================================
python test_qai_simple.py
echo =========================================================
echo.

echo If you still see connection errors, try the following:
echo 1. Check your internet connection
echo 2. Try the old API URL by editing %config_file% and changing:
echo    base_api_url=https://api.aihub.qualcomm.com
echo    to:
echo    base_api_url=https://api.qai-hub.qualcomm.com
echo 3. Check the QAI_HUB_TROUBLESHOOTING.md file for more help
echo.

:END
echo Press any key to exit...
pause >nul
