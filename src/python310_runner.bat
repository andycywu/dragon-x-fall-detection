@echo off
echo Running Dragon X Fall Detection System with Python 3.10...

set PYTHON_PATH=C:\Users\HCKTest\AppData\Local\Programs\Python\Python310\python.exe
set PYTHONIOENCODING=utf-8
chcp 65001 > nul

REM Set QAI Hub variables to system level
setx QAI_API_KEY pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d /M
setx QAI_API_TOKEN pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d /M
setx QAI_HOST https://api.aihub.qualcomm.com /M
setx QAI_API_VERSION v1 /M
setx QAI_API_URL https://api.aihub.qualcomm.com /M

"%PYTHON_PATH%" C:\dragon-x-fall-detection\dragon_x_fall_detection_system.py

echo Program execution completed.
pause
