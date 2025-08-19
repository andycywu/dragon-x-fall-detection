@echo off
echo Setting up QAI Hub environment variables...

REM Set environment variables for QAI Hub
set QAI_API_KEY=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
set QAI_API_TOKEN=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
set QAI_HOST=https://api.aihub.qualcomm.com
set QAI_API_VERSION=v1
set QAI_API_URL=https://api.aihub.qualcomm.com

echo QAI Hub environment variables set!
echo API Key: %QAI_API_KEY%
echo API URL: %QAI_API_URL%

REM Create client.ini file
echo Creating client.ini file...
if not exist "%USERPROFILE%\.qai_hub" mkdir "%USERPROFILE%\.qai_hub"
(
echo [default]
echo api_token = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
echo api_key = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
echo base_api_url = https://api.aihub.qualcomm.com
echo web_url = https://app.aihub.qualcomm.com
echo api_url = https://api.aihub.qualcomm.com
echo api_version = v1
echo user_info = 
) > "%USERPROFILE%\.qai_hub\client.ini"

echo client.ini file created at %USERPROFILE%\.qai_hub\client.ini

REM Run original file with environment variables set
echo Running Dragon X Fall Detection System...
"%~dp0python310_runner.bat"

echo Done!
pause
