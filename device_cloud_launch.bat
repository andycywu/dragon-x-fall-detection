@echo off
chcp 65001 > nul
REM Qualcomm Device Cloud啟動腳本 - 增強版

echo ========================================================================
echo                Dragon X Fall Detection System - 啟動腳本
echo ========================================================================
echo.

REM 設置顏色
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "BOLD=[1m"
set "RESET=[0m"

REM 設置環境變量
set QAI_HUB_API_TOKEN=h0eubh7un3kk64u6oxisg9rbt8bbgubs913bzls2
set PYTHONPATH=%PYTHONPATH%;%CD%

REM 檢查 client.ini 文件是否存在
echo %BLUE%檢查 QAI Hub client.ini 配置...%RESET%
if not exist "%USERPROFILE%\.qai_hub\client.ini" (
    echo %YELLOW%警告: 未找到 client.ini 文件，嘗試修復...%RESET%
    if exist "fix_qai_hub_client.bat" (
        echo %BLUE%運行修復工具...%RESET%
        call fix_qai_hub_client.bat
    ) else (
        echo %RED%錯誤: 修復工具 fix_qai_hub_client.bat 不存在%RESET%
        echo %YELLOW%嘗試手動創建配置文件...%RESET%
        
        REM 創建目錄和配置文件
        if not exist "%USERPROFILE%\.qai_hub" mkdir "%USERPROFILE%\.qai_hub"
        echo [DEFAULT] > "%USERPROFILE%\.qai_hub\client.ini"
        echo api_key = %QAI_HUB_API_TOKEN% >> "%USERPROFILE%\.qai_hub\client.ini"
        
        if exist "%USERPROFILE%\.qai_hub\client.ini" (
            echo %GREEN%成功: 已創建 client.ini 文件%RESET%
        ) else (
            echo %RED%錯誤: 無法創建 client.ini 文件%RESET%
            echo 請先手動運行 fix_qai_hub_client.bat 或手動創建配置文件
            pause
            exit /b 1
        )
    )
) else (
    echo %GREEN%client.ini 文件已存在%RESET%
)

REM 檢測CPU架構
echo.
echo %BLUE%檢測系統架構...%RESET%
for /f "tokens=2 delims==" %%i in ('wmic os get osarchitecture /value') do set ARCH=%%i
echo 檢測到系統架構: %ARCH%

REM 檢查是否是ARM64
set IS_ARM64=0
echo %ARCH% | findstr /i "ARM" > nul && set IS_ARM64=1

if %IS_ARM64%==1 (
    echo %GREEN%檢測到ARM64架構，啟用Snapdragon優化...%RESET%
    set ONNXRUNTIME_PROVIDER_PRIORITY=QNNExecutionProvider,DirectMLExecutionProvider,CPUExecutionProvider
    set ORT_LOGGING_LEVEL=2
    set OPTIMIZATION_FLAG=--optimize_for_arm64
) else (
    echo %YELLOW%未檢測到ARM64架構，使用標準配置...%RESET%
    set OPTIMIZATION_FLAG=
)

REM 檢查系統信息
echo.
echo %BLUE%硬件狀態檢查:%RESET%
systeminfo | findstr /i "processor"
wmic cpu get name | findstr /i "qualcomm" > nul
if %errorlevel%==0 (
    echo %GREEN%檢測到Qualcomm Snapdragon平台%RESET%
) else (
    echo %YELLOW%未檢測到Qualcomm Snapdragon平台%RESET%
)

REM 檢查環境狀態
echo.
echo %BLUE%套件狀態檢查:%RESET%
python -c "import numpy; print('NumPy版本:', numpy.__version__)" 2>nul
if %errorlevel%==0 (
    echo %GREEN%NumPy已安裝%RESET%
) else (
    echo %RED%NumPy未安裝，請先運行install_packages.bat%RESET%
    pause
    exit /b 1
)

python -c "import cv2; print('OpenCV版本:', cv2.__version__)" 2>nul
if %errorlevel%==0 (
    echo %GREEN%OpenCV已安裝%RESET%
) else (
    echo %RED%OpenCV未安裝，請先運行install_packages.bat%RESET%
    pause
    exit /b 1
)

REM 檢查 QAI Hub SDK
python -c "import qai_hub; print('QAI Hub SDK版本:', getattr(qai_hub, '__version__', '未知'))" 2>nul
if %errorlevel%==0 (
    echo %GREEN%QAI Hub SDK已安裝%RESET%
) else (
    echo %RED%QAI Hub SDK未安裝，請先運行install_packages.bat%RESET%
    pause
    exit /b 1
)

REM 檢查 protobuf 版本
python -c "import pkg_resources; print('Protobuf版本:', pkg_resources.get_distribution('protobuf').version)" 2>nul
if %errorlevel%==0 (
    python -c "import pkg_resources; ver=pkg_resources.get_distribution('protobuf').version; print('需要 4.25.3，當前版本:', ver); exit(0 if ver=='4.25.3' else 1)" 2>nul
    if %errorlevel%==0 (
        echo %GREEN%Protobuf版本正確 (4.25.3)%RESET%
    ) else (
        echo %YELLOW%警告: Protobuf版本可能不兼容，建議使用 4.25.3%RESET%
    )
) else (
    echo %YELLOW%警告: 無法檢查 Protobuf 版本%RESET%
)

REM 設置QAI Hub認證
echo.
echo %BLUE%設置QAI Hub認證...%RESET%
echo QAI_HUB_API_TOKEN=%QAI_HUB_API_TOKEN% > "%USERPROFILE%\.env"

REM 運行設置腳本並捕獲輸出
python setup_qai_hub.py --token %QAI_HUB_API_TOKEN% > qai_hub_setup.log 2>&1
if %errorlevel% NEQ 0 (
    echo %RED%QAI Hub認證設置失敗，但仍將嘗試啟動系統%RESET%
    echo %YELLOW%請確認：%RESET%
    echo %YELLOW% 1. .qai_hub 目錄是否存在於 %USERPROFILE% 目錄下%RESET%
    echo %YELLOW% 2. client.ini 文件是否包含正確的API密鑰%RESET%
    echo %YELLOW% 3. 手動運行 python -c "import qai_hub as hub; print(hub.get_devices())" 測試連接%RESET%
    
    echo.
    echo %BLUE%嘗試測試 QAI Hub 連接...%RESET%
    python -c "import qai_hub as hub; print('可用設備:', [d.name for d in hub.get_devices()])" 2>nul
    if %errorlevel% NEQ 0 (
        echo %RED%QAI Hub 連接測試失敗%RESET%
        echo %YELLOW%自動嘗試修復...%RESET%
        python fix_client_ini.py
    ) else (
        echo %GREEN%QAI Hub 連接測試成功，繼續啟動%RESET%
    )
) else (
    echo %GREEN%QAI Hub認證設置成功%RESET%
)

echo.
echo %BLUE%========================================================================%RESET%
echo %BLUE%%BOLD%                    啟動 Dragon X AI 檢測系統                        %RESET%
echo %BLUE%========================================================================%RESET%
echo.

REM 檢查主程序文件
if exist "unified_ai_detector.py" (
    REM 啟動AI檢測系統
    echo %GREEN%啟動AI檢測系統...%RESET%
    python unified_ai_detector.py --device snapdragon %OPTIMIZATION_FLAG%
) else if exist "dragon_x_fall_detection_system.py" (
    REM 啟動Dragon X專用系統
    echo %GREEN%啟動Dragon X Fall Detection系統...%RESET%
    python dragon_x_fall_detection_system.py
) else (
    echo %RED%錯誤: 找不到主程序文件%RESET%
    pause
    exit /b 1
)

echo.
echo %GREEN%========================================================================%RESET%
echo %GREEN%                      系統啟動完成！                                     %RESET%
echo %GREEN%========================================================================%RESET%
echo.
