@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM Define ANSI color codes
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set "ESC=%%b"
)

echo !ESC![36m=========================================================!ESC![0m
echo !ESC![36m              QAI Hub Diagnostic Tool (English)          !ESC![0m
echo !ESC![36m=========================================================!ESC![0m
echo.

REM Create timestamp and report directory
set timestamp=%date:~0,3%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%
set report_dir=qai_hub_diagnostic_report_%timestamp%
mkdir %report_dir% 2>nul

echo !ESC![32mRunning diagnostics...!ESC![0m
echo !ESC![32mDetected OS: Windows!ESC![0m
echo !ESC![32mDiagnostic report folder: %report_dir%!ESC![0m
echo.

REM Step 1: Check Python environment
echo !ESC![33mStep 1: Checking Python environment...!ESC![0m
python --version > %report_dir%\python_version.txt 2>&1
for /f "tokens=2" %%i in (%report_dir%\python_version.txt) do set python_version=%%i
echo Detected Python version: %python_version%
where pip > %report_dir%\pip_path.txt 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python pip is available
) else (
    echo !ESC![91mWarning: pip not found!ESC![0m
)
echo.

REM Step 2: Check QAI Hub installation
echo !ESC![33mStep 2: Checking QAI Hub modules...!ESC![0m
echo Checking QAI Hub installation...
python -c "import pkg_resources; print('QAI Hub version:', pkg_resources.get_distribution('qai-hub').version)" > %report_dir%\qai_hub_status.txt 2>&1
if %ERRORLEVEL% EQU 0 (
    echo QAI Hub is installed
    type %report_dir%\qai_hub_status.txt
) else (
    echo !ESC![91mQAI Hub is not installed or has issues!ESC![0m
    echo "Error importing QAI Hub. See %report_dir%\qai_hub_status.txt for details."
)
echo.

REM Step 3: Test API connection
echo !ESC![33mStep 3: Testing QAI Hub API connection...!ESC![0m
echo Checking API connection...
python -c "import qai_hub as hub; print('Available devices:', hub.get_devices())" > %report_dir%\api_test.txt 2>&1
if %ERRORLEVEL% EQU 0 (
    echo !ESC![32mAPI connection successful!ESC![0m
    type %report_dir%\api_test.txt
) else (
    echo !ESC![91mAPI connection failed!ESC![0m
    echo "Failed to connect to QAI Hub API. See %report_dir%\api_test.txt for details."
)
echo.

REM Step 4: Check configuration file
echo !ESC![33mStep 4: Checking configuration file...!ESC![0m
echo Checking QAI Hub configuration...
python -c "import os, qai_hub; config_path = os.path.expanduser('~/.qai_hub/client.ini'); print('Config file path:', config_path); print('Config exists:', os.path.exists(config_path)); print('Content:'); print(open(config_path, 'r').read() if os.path.exists(config_path) else 'File not found')" > %report_dir%\config_check.txt 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Configuration file checked
    type %report_dir%\config_check.txt
) else (
    echo !ESC![91mCould not check configuration file!ESC![0m
    echo "Error checking configuration. See %report_dir%\config_check.txt for details."
)
echo.

REM Step 5: Test offline mode
echo !ESC![33mStep 5: Testing offline mode functionality...!ESC![0m
echo Checking for offline mode support...
if exist qai_hub_demo_offline.py (
    echo Offline demo file found
    echo "Offline mode support is available" > %report_dir%\offline_mode_test.txt
) else (
    echo !ESC![93mOffline demo file not found!ESC![0m
    echo "The offline mode demo file (qai_hub_demo_offline.py) was not found." > %report_dir%\offline_mode_test.txt
)
echo.

REM Step 6: Generate report summary
echo !ESC![33mStep 6: Generating report summary...!ESC![0m
echo.

echo Diagnostic Summary: > %report_dir%\diagnostic_summary.txt
findstr /C:"QAI Hub version" %report_dir%\qai_hub_status.txt >> %report_dir%\diagnostic_summary.txt 2>nul
findstr /C:"Available devices" %report_dir%\api_test.txt >> %report_dir%\diagnostic_summary.txt 2>nul
findstr /C:"Config file path" %report_dir%\config_check.txt >> %report_dir%\diagnostic_summary.txt 2>nul
findstr /C:"Config exists" %report_dir%\config_check.txt >> %report_dir%\diagnostic_summary.txt 2>nul
echo Offline mode: >> %report_dir%\diagnostic_summary.txt
type %report_dir%\offline_mode_test.txt >> %report_dir%\diagnostic_summary.txt

echo !ESC![36m=========================================================!ESC![0m
echo !ESC![36m            QAI Hub Diagnostic Report Summary            !ESC![0m
echo !ESC![36m=========================================================!ESC![0m
echo.
type %report_dir%\diagnostic_summary.txt
echo.
echo !ESC![32mNext steps:!ESC![0m
echo !ESC![32m1. Review detailed diagnostic report (%report_dir%)!ESC![0m
echo !ESC![32m2. Refer to troubleshooting guide (QAI_HUB_TROUBLESHOOTING.md)!ESC![0m
echo !ESC![32m3. Try fixing the configuration using fix_qai_hub_api_url.bat!ESC![0m
echo.
echo !ESC![36m=========================================================!ESC![0m

pause
