@echo off
REM Set environment variables for QAI Hub
SET QAI_API_KEY=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
SET QAI_API_TOKEN=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
SET QAI_HOST=https://api.aihub.qualcomm.com
SET QAI_API_URL=https://api.aihub.qualcomm.com
SET QAI_API_VERSION=v1

echo QAI Hub environment variables have been set.
echo.

REM Run completely fixed Dragon X system with Python 3.10
echo Running completely fixed Dragon X Fall Detection System with Python 3.10...
"C:\Users\HCKTest\AppData\Local\Programs\Python\Python310\python.exe" C:\dragon-x-fall-detection\dragon_x_completely_fixed.py

echo.
echo Press any key to exit...
pause > nul
