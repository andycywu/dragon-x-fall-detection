@echo off
echo Starting QAI Hub Real Inference Fall Detection System
echo =====================================================
echo.

REM Set QAI Hub environment variables
set QAI_API_KEY=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
set QAI_API_TOKEN=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
set QAI_HOST=https://api.aihub.qualcomm.com
set QAI_API_URL=https://api.aihub.qualcomm.com
set QAI_API_VERSION=v1

echo QAI Hub environment variables have been set
echo.

REM Run the real inference system with Python 3.10
C:\Python310\python.exe qai_hub_real_inference.py

echo.
echo Fall Detection System execution completed
pause
