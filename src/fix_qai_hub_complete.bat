@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM Define ANSI color codes
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set "ESC=%%b"
)

echo !ESC![36m=========================================================!ESC![0m
echo !ESC![36m            QAI Hub Enhanced Repair Tool                 !ESC![0m
echo !ESC![36m=========================================================!ESC![0m
echo.

REM Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo !ESC![93mWarning: This script is not running as administrator.!ESC![0m
    echo !ESC![93mSome operations may require admin privileges.!ESC![0m
    echo.
)

REM Check Windows Long Path support
echo !ESC![32mChecking Windows Long Path support...!ESC![0m
reg query "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled 2>nul | find "0x1" >nul
if %ERRORLEVEL% NEQ 0 (
    echo !ESC![93mWarning: Windows Long Path support is not enabled!!ESC![0m
    echo !ESC![93mThis may cause installation issues with deep directory structures.!ESC![0m
    echo !ESC![36mTo enable Long Path support, run as administrator:!ESC![0m
    echo !ESC![92m   reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f!ESC![0m
    echo !ESC![36mThen restart your computer!ESC![0m
    echo.
) else (
    echo !ESC![92mWindows Long Path support is enabled!ESC![0m
)
echo.

REM Check Python installation
echo !ESC![32mChecking Python installation...!ESC![0m
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo !ESC![91mError: Python not found. Please install Python 3.10 or higher.!ESC![0m
    goto :END
)

REM Identify Python version and installation type
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo !ESC![92mDetected Python version: %python_version%!ESC![0m

REM Check if Python is from Microsoft Store
python -c "import sys; print('Microsoft' if 'WindowsApps' in sys.executable else 'Standard')" > python_type.txt
set /p python_type=<python_type.txt
del python_type.txt

if "%python_type%"=="Microsoft" (
    echo !ESC![93mWarning: Using Microsoft Store Python (%python_type%)!ESC![0m
    echo !ESC![93mThis may cause permission issues with package installation.!ESC![0m
    echo !ESC![36mConsider installing Python from python.org instead.!ESC![0m
) else (
    echo !ESC![92mPython installation type: %python_type%!ESC![0m
)
echo.

REM Create backup of existing config
echo !ESC![32mCreating backup of existing QAI Hub configuration (if any)...!ESC![0m
set config_dir=%USERPROFILE%\.qai_hub
set config_file=%config_dir%\client.ini
set backup_file=%config_dir%\client.ini.backup

if not exist %config_dir% (
    mkdir %config_dir%
    echo !ESC![92mCreated configuration directory: %config_dir%!ESC![0m
)

if exist %config_file% (
    copy %config_file% %backup_file% >nul
    echo !ESC![92mBackup created: %backup_file%!ESC![0m
) else (
    echo !ESC![93mNo existing configuration found.!ESC![0m
)
echo.

REM Create new configuration file
echo !ESC![32mCreating new configuration file...!ESC![0m
echo !ESC![36mPlease enter your QAI Hub API Token (press Enter to use a default token):!ESC![0m
set /p api_token=

if "!api_token!"=="" (
    set api_token=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
    echo !ESC![93mUsing default token. Please replace with your actual token later.!ESC![0m
)

REM Write both API URL options to try both
echo !ESC![36mCreating two configuration files to test both API URLs...!ESC![0m

REM Create configuration for new API URL
echo [default]> %config_file%.new
echo api_token=%api_token%>> %config_file%.new
echo api_key=%api_token%>> %config_file%.new
echo base_api_url=https://api.aihub.qualcomm.com>> %config_file%.new
echo web_url=https://app.aihub.qualcomm.com>> %config_file%.new

REM Create configuration for old API URL
echo [default]> %config_file%.old
echo api_token=%api_token%>> %config_file%.old
echo api_key=%api_token%>> %config_file%.old
echo base_api_url=https://api.qai-hub.qualcomm.com>> %config_file%.old
echo web_url=https://app.aihub.qualcomm.com>> %config_file%.old

echo !ESC![92mConfiguration files created!ESC![0m
echo.

REM Test which API URL works
echo !ESC![32mTesting both API URLs to determine which one works...!ESC![0m

REM Test new URL
copy %config_file%.new %config_file% >nul
echo !ESC![36mTesting new URL: https://api.aihub.qualcomm.com!ESC![0m
python -c "import qai_hub as hub; print('API URL Test (New): Success')" > new_url_test.txt 2>&1
set new_url_status=%ERRORLEVEL%

if %new_url_status% EQU 0 (
    echo !ESC![92mNew API URL works!!ESC![0m
    set working_url=new
) else (
    echo !ESC![93mNew API URL failed!ESC![0m
    type new_url_test.txt
)

REM Test old URL if new failed
if %new_url_status% NEQ 0 (
    copy %config_file%.old %config_file% >nul
    echo !ESC![36mTesting old URL: https://api.qai-hub.qualcomm.com!ESC![0m
    python -c "import qai_hub as hub; print('API URL Test (Old): Success')" > old_url_test.txt 2>&1
    set old_url_status=%ERRORLEVEL%
    
    if %old_url_status% EQU 0 (
        echo !ESC![92mOld API URL works!!ESC![0m
        set working_url=old
    ) else (
        echo !ESC![93mOld API URL failed!ESC![0m
        type old_url_test.txt
        set working_url=none
    )
)

REM Set the working configuration
if "%working_url%"=="new" (
    copy %config_file%.new %config_file% >nul
    echo !ESC![92mUsing new API URL: https://api.aihub.qualcomm.com!ESC![0m
) else if "%working_url%"=="old" (
    copy %config_file%.old %config_file% >nul
    echo !ESC![92mUsing old API URL: https://api.qai-hub.qualcomm.com!ESC![0m
) else (
    echo !ESC![91mNeither API URL worked. There may be other issues.!ESC![0m
)

REM Clean up temporary files
del %config_file%.new %config_file%.old new_url_test.txt old_url_test.txt 2>nul

REM Check for missing dependencies
echo.
echo !ESC![32mChecking for QAI Hub dependencies...!ESC![0m
pip show qai-hub >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo !ESC![93mQAI Hub not installed. Attempting to install...!ESC![0m
    pip install qai-hub==0.31.0 qai-hub-models==0.31.0
    if %ERRORLEVEL% NEQ 0 (
        echo !ESC![91mInstallation failed. Trying another approach...!ESC![0m
        echo !ESC![36mAttempting to install with --no-cache-dir option...!ESC![0m
        pip install --no-cache-dir qai-hub==0.31.0 qai-hub-models==0.31.0
    )
) else (
    echo !ESC![92mQAI Hub is already installed!ESC![0m
)

REM Create test script
echo.
echo !ESC![32mCreating test script to verify QAI Hub configuration...!ESC![0m
echo import sys> test_qai_hub.py
echo print(f"Python version: {sys.version}")>> test_qai_hub.py
echo print(f"Python path: {sys.executable}")>> test_qai_hub.py
echo.>> test_qai_hub.py
echo try:>> test_qai_hub.py
echo     import qai_hub as hub>> test_qai_hub.py
echo     print(f"QAI Hub version: {hub.__version__}")>> test_qai_hub.py
echo     print("Attempting to connect to QAI Hub...")>> test_qai_hub.py
echo     print("Config file:", hub._config._get_config_file_path())>> test_qai_hub.py
echo     try:>> test_qai_hub.py
echo         devices = hub.get_devices()>> test_qai_hub.py
echo         print(f"Available devices: {devices}")>> test_qai_hub.py
echo         print("Configuration successful!")>> test_qai_hub.py
echo     except Exception as e:>> test_qai_hub.py
echo         print(f"API Connection Error: {e}")>> test_qai_hub.py
echo except Exception as e:>> test_qai_hub.py
echo     print(f"Error: {e}")>> test_qai_hub.py
echo     print("Check if QAI Hub is installed correctly")>> test_qai_hub.py

echo !ESC![92mTest script created: test_qai_hub.py!ESC![0m
echo.

REM Run test script
echo !ESC![32mRunning QAI Hub test script...!ESC![0m
python test_qai_hub.py
echo.

REM Show configuration information
echo !ESC![36m=========================================================!ESC![0m
echo !ESC![36m                    Summary                              !ESC![0m
echo !ESC![36m=========================================================!ESC![0m
echo.
echo !ESC![36mConfiguration file: %config_file%!ESC![0m
echo !ESC![36mAPI Token: %api_token:~0,5%...!ESC![0m
if "%working_url%"=="new" (
    echo !ESC![36mAPI URL: https://api.aihub.qualcomm.com (new)!ESC![0m
) else if "%working_url%"=="old" (
    echo !ESC![36mAPI URL: https://api.qai-hub.qualcomm.com (old)!ESC![0m
) else (
    echo !ESC![36mAPI URL: Could not determine working URL!ESC![0m
)
echo.

REM Next steps
echo !ESC![32mNext steps:!ESC![0m
echo !ESC![32m1. If the test was successful, you're all set!!ESC![0m
echo !ESC![32m2. If issues persist, try installing different versions:!ESC![0m
echo !ESC![36m   pip install qai-hub==0.30.0 qai-hub-models==0.30.0!ESC![0m
echo !ESC![32m3. Or try the latest versions:!ESC![0m
echo !ESC![36m   pip install -U qai-hub qai-hub-models!ESC![0m
echo !ESC![32m4. Check troubleshooting guide: QAI_HUB_TROUBLESHOOTING.md!ESC![0m
echo.

:END
echo !ESC![36mPress any key to exit...!ESC![0m
pause >nul
