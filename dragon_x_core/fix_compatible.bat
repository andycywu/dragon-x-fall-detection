@echo off
REM 跨平台兼容版本修復腳本

echo ========================================
echo    Dragon X 跌倒檢測系統 - 修復工具
echo ========================================
echo.

echo 檢查跨平台兼容版檔案...

REM 檢查 main_compatible.py 是否存在
if not exist main_compatible.py (
    echo 錯誤: 找不到 main_compatible.py 文件！
    pause
    exit /b 1
)

REM 檢查 detectors 目錄是否存在
if not exist detectors (
    echo 錯誤: 找不到 detectors 目錄！
    pause
    exit /b 1
)

REM 檢查 fall_detector_opencv.py 是否存在
if not exist detectors\fall_detector_opencv.py (
    echo 錯誤: 找不到 fall_detector_opencv.py 文件！
    pause
    exit /b 1
)

echo 修復導入路徑...
powershell -Command "(Get-Content main_compatible.py) -replace 'from fall_detector_opencv import FallDetector', 'from detectors.fall_detector_opencv import FallDetector' | Set-Content main_compatible.py"
powershell -Command "(Get-Content main_compatible.py) -replace 'from detectors.fall_detector_opencv import OpenCVFallDetector as FallDetector', 'from detectors.fall_detector_opencv import FallDetector' | Set-Content main_compatible.py"

echo 檢查 sounddevice 模組...
python -c "import sounddevice" 2>NUL
if %ERRORLEVEL% neq 0 (
    echo 安裝 sounddevice 模組...
    pip install sounddevice
)

echo 修復完成！現在您可以運行跨平台兼容版系統了。
echo 請使用 start_windows.bat 並選擇選項 3 啟動系統。
pause
