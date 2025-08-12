@echo off
echo =========================================================
echo           QAI Hub URL Switcher Tool
echo =========================================================
echo.

echo This tool will test both API URLs and use the one that works.
echo.

set config_dir=%USERPROFILE%\.qai_hub
set config_file=%config_dir%\client.ini

if not exist %config_dir% (
    mkdir %config_dir%
    echo Created configuration directory.
)

echo Testing both QAI Hub API URLs...
echo.

echo Setting up temporary test files...
echo import qai_hub> test_old_url.py
echo print("Old URL test successful")>> test_old_url.py

echo import qai_hub> test_new_url.py
echo print("New URL test successful")>> test_new_url.py

echo Step 1: Setting up QAI Hub configuration...
echo [default]> %config_file%
echo api_token=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
echo api_key=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
echo base_api_url=https://app.aihub.qualcomm.com>> %config_file%
echo web_url=https://app.aihub.qualcomm.com>> %config_file%

timeout /t 2 /nobreak >nul
python test_new_url.py >nul 2>&1
set new_url_result=%ERRORLEVEL%

if %new_url_result% EQU 0 (
    echo New API URL works!
    set working_url=new
) else (
    echo New API URL not working, trying old URL...
    
    echo Step 2: Checking if QAI Hub is installed correctly...
    echo [default]> %config_file%
    echo api_token=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
    echo api_key=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
    echo base_api_url=https://app.aihub.qualcomm.com>> %config_file%
    echo web_url=https://app.aihub.qualcomm.com>> %config_file%
    
    timeout /t 2 /nobreak >nul
    python test_old_url.py >nul 2>&1
    set old_url_result=%ERRORLEVEL%
    
    if %old_url_result% EQU 0 (
        echo Old API URL works!
        set working_url=old
    ) else (
        echo Old API URL not working either.
        set working_url=none
    )
)

echo.
echo Cleaning up test files...
del test_old_url.py test_new_url.py >nul 2>&1

echo.
if %new_url_result% EQU 0 (
    echo Configuration successful!
    
    echo [default]> %config_file%
    echo api_token=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
    echo api_key=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
    echo base_api_url=https://app.aihub.qualcomm.com>> %config_file%
    echo web_url=https://app.aihub.qualcomm.com>> %config_file%
) else (
    echo QAI Hub configuration may need additional setup.
    
    echo [default]> %config_file%
    echo api_token=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
    echo api_key=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
    echo base_api_url=https://app.aihub.qualcomm.com>> %config_file%
    echo web_url=https://app.aihub.qualcomm.com>> %config_file%
) else (
    echo No working API URL found.
    echo Please check your internet connection and QAI Hub installation.
    echo.
    echo Would you like to update your QAI Hub installation? (Y/N)
    set /p update_choice=
    if /i "%update_choice%"=="Y" (
        echo Updating QAI Hub...
        pip install -U qai-hub qai-hub-models
        echo QAI Hub update complete.
    )
)

echo.
echo Configuration saved to: %config_file%
echo.

echo Running a simple test to verify configuration...
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
