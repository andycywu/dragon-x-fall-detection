@echo off
chcp 65001 > nul
REM Qualcomm Device Cloud啟動腳本

echo === Dragon X Fall Detection System ===
echo ==================================

REM 設置環境變量
set QAI_HUB_API_TOKEN=h0eubh7un3kk64u6oxisg9rbt8bbgubs913bzls2
set PYTHONPATH=%PYTHONPATH%;%CD%

REM 檢測CPU架構
echo === 檢測系統架構...
for /f "tokens=2 delims==" %%i in ('wmic os get osarchitecture /value') do set ARCH=%%i
echo 檢測到系統架構: %ARCH%

REM 檢查是否是ARM64
set IS_ARM64=0
echo %ARCH% | findstr /i "ARM" > nul && set IS_ARM64=1

if %IS_ARM64%==1 (
    echo === 檢測到ARM64架構，啟用Snapdragon優化...
    set ONNXRUNTIME_PROVIDER_PRIORITY=QNNExecutionProvider,DirectMLExecutionProvider,CPUExecutionProvider
    set ORT_LOGGING_LEVEL=2
    set OPTIMIZATION_FLAG=--optimize_for_arm64
) else (
    echo === 未檢測到ARM64架構，使用標準配置...
    set OPTIMIZATION_FLAG=
)

REM 檢查系統信息
echo === 硬件狀態檢查:
systeminfo | findstr /i "processor"
wmic cpu get name | findstr /i "qualcomm" > nul
if %errorlevel%==0 (
    echo 檢測到Qualcomm Snapdragon平台
) else (
    echo 未檢測到Qualcomm Snapdragon平台
)

REM 檢查環境狀態
echo === 套件狀態檢查:
python -c "import numpy; print('NumPy版本:', numpy.__version__)" 2>nul
if %errorlevel%==0 (
    echo NumPy已安裝
) else (
    echo NumPy未安裝，請先運行install_packages.bat
    goto :EOF
)

python -c "import cv2; print('OpenCV版本:', cv2.__version__)" 2>nul
if %errorlevel%==0 (
    echo OpenCV已安裝
) else (
    echo OpenCV未安裝，請先運行install_packages.bat
    goto :EOF
)

REM 設置QAI Hub認證
echo === 設置QAI Hub認證...
python setup_qai_hub.py
if %errorlevel% NEQ 0 (
    echo !!! QAI Hub認證設置失敗，但仍將嘗試啟動系統
)

REM 啟動AI檢測系統
echo === 啟動AI檢測系統...
python unified_ai_detector.py --device snapdragon %OPTIMIZATION_FLAG%

REM 或者啟動Dragon X專用系統
REM python dragon_x_fall_detection_system.py

echo === 系統啟動完成！
