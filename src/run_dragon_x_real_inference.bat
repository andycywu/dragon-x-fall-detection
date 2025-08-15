@echo off
echo Dragon X Fall Detection System - Real QAI Hub Inference
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

REM Check if the Python script exists
if not exist "C:\dragon-x-fall-detection\dragon_x_real_inference.py" (
    echo Error: dragon_x_real_inference.py not found
    goto :exit
)

REM Use the correct Python path
echo Running Python script with correct Python path...
C:\Users\HCKTest\AppData\Local\Programs\Python\Python310\python.exe C:\dragon-x-fall-detection\dragon_x_real_inference.py

:exit
echo.
echo Fall Detection System execution completed
pause
