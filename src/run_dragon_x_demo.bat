@echo off
echo Starting Dragon X Demo using Python 3.10...

set PYTHON_PATH=C:\Users\HCKTest\AppData\Local\Programs\Python\Python310\python.exe
set PYTHONIOENCODING=utf-8
chcp 65001 > nul

"%PYTHON_PATH%" C:\dragon-x-fall-detection\dragon_x_demo.py

echo Program execution completed.
pause
