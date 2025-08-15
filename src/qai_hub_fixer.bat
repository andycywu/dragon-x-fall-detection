@echo off
chcp 65001 >nul
echo =========================================================
echo           QAI Hub API URL and Token Fixer
echo =========================================================
echo.

echo This tool will help you fix QAI Hub configuration issues.
echo.

set config_dir=%USERPROFILE%\.qai_hub
set config_file=%config_dir%\client.ini

echo Step 1: Checking for existing configuration...
if exist "%config_file%" (
    echo Found existing configuration file at:
    echo %config_file%
    echo.
    echo Current configuration:
    type "%config_file%"
    echo.
) else (
    echo No existing configuration found.
    echo Creating new configuration directory...
    if not exist "%config_dir%" mkdir "%config_dir%"
)

echo Step 2: Checking QAI Hub installation...
python -c "import qai_hub; print('QAI Hub version:', qai_hub.__version__)" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo QAI Hub is not installed or cannot be imported.
    echo Would you like to install or update QAI Hub? (Y/N)
    set /p install_choice=
    if /i "%install_choice%"=="Y" (
        echo Installing QAI Hub...
        pip install -U qai-hub qai-hub-models
        echo Installation complete.
    ) else (
        echo Skipping installation. You'll need to install QAI Hub manually.
    )
)

echo.
echo Step 3: Enter your QAI Hub API token (or press Enter to use default)
echo         (Default token: pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d)
set /p user_token=API Token: 

if "%user_token%"=="" (
    set api_token=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
) else (
    set api_token=%user_token%
)

echo.
echo Step 4: Setting up correct API URL...
echo.
echo [default]> "%config_file%"
echo api_token=%api_token%>> "%config_file%"
echo api_key=%api_token%>> "%config_file%"
echo base_api_url=https://app.aihub.qualcomm.com>> "%config_file%"
echo web_url=https://app.aihub.qualcomm.com>> "%config_file%"
echo Using official URL: https://app.aihub.qualcomm.com

echo.
echo Step 5: Checking Windows long path support...
reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled 2>nul | findstr "0x1" >nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Windows long path support is not enabled.
    echo This may cause installation problems with QAI Hub packages.
    echo.
    echo Would you like to enable Windows long path support? (Y/N)
    echo NOTE: This requires administrator privileges.
    set /p longpath_choice=
    if /i "%longpath_choice%"=="Y" (
        echo Creating registry file...
        echo Windows Registry Editor Version 5.00> enable_long_paths.reg
        echo.>> enable_long_paths.reg
        echo [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem]>> enable_long_paths.reg
        echo "LongPathsEnabled"=dword:00000001>> enable_long_paths.reg
        
        echo Please run enable_long_paths.reg as administrator and restart your computer.
        echo After restart, run this script again to complete the setup.
    )
) else (
    echo Windows long path support is already enabled. Good!
)

echo.
echo Configuration saved to: %config_file%
echo.

echo Step 6: Running a simple test to verify configuration...
echo import qai_hub as hub> verify_test.py
echo print("QAI Hub version:", hub.__version__)>> verify_test.py
echo try:>> verify_test.py
echo     devices = hub.get_devices()>> verify_test.py
echo     print("Available devices:", devices)>> verify_test.py
echo     print("QAI Hub configuration is working!")>> verify_test.py
echo except Exception as e:>> verify_test.py
echo     print("Error testing QAI Hub:", e)>> verify_test.py

echo.
echo Test results:
echo =========================================================
python verify_test.py
echo =========================================================
echo.

del verify_test.py >nul 2>&1

echo =========================================================
echo                       Next Steps
echo =========================================================
echo.
echo 1. If the test shows "QAI Hub configuration is working!", you're all set!
echo 2. If errors persist, consider:
echo    - Updating your QAI Hub installation:
echo      pip install -U qai-hub qai-hub-models
echo    - Trying a specific version compatible with your project:
echo      pip install qai-hub==0.31.0 qai-hub-models==0.31.0
echo    - Check the troubleshooting guide (QAI_HUB_TROUBLESHOOTING.md)
echo.

echo Press any key to exit...
pause >nul
