@echo off
echo @echo off > %USERPROFILE%\qdc_auto_setup.bat
echo setlocal enabledelayedexpansion >> %USERPROFILE%\qdc_auto_setup.bat

echo echo [INFO] QDC 環境自動設置腳本開始執行... >> %USERPROFILE%\qdc_auto_setup.bat

echo REM 檢查 Git 是否已安裝 >> %USERPROFILE%\qdc_auto_setup.bat
echo echo [INFO] 檢查 Git 安裝狀態... >> %USERPROFILE%\qdc_auto_setup.bat
echo where git ^>nul 2^>^&1 >> %USERPROFILE%\qdc_auto_setup.bat
echo if %errorlevel% neq 0 ( >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [WARN] Git 未安裝，正在下載安裝程序... >> %USERPROFILE%\qdc_auto_setup.bat
echo     REM 下載 Git 安裝程序 >> %USERPROFILE%\qdc_auto_setup.bat
echo     powershell -Command "Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.40.0.windows.1/Git-2.40.0-64-bit.exe' -OutFile '%TEMP%\git-installer.exe'" >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [INFO] 正在安裝 Git，請稍候... >> %USERPROFILE%\qdc_auto_setup.bat
echo     %TEMP%\git-installer.exe /VERYSILENT /NORESTART >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [INFO] Git 安裝完成，請重新運行此腳本 >> %USERPROFILE%\qdc_auto_setup.bat
echo     exit /b 1 >> %USERPROFILE%\qdc_auto_setup.bat
echo ) else ( >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [SUCCESS] Git 已安裝:  >> %USERPROFILE%\qdc_auto_setup.bat
echo     git --version >> %USERPROFILE%\qdc_auto_setup.bat
echo ) >> %USERPROFILE%\qdc_auto_setup.bat

echo REM 檢查 Python 是否已安裝 >> %USERPROFILE%\qdc_auto_setup.bat
echo echo [INFO] 檢查 Python 安裝狀態... >> %USERPROFILE%\qdc_auto_setup.bat
echo where python ^>nul 2^>^&1 >> %USERPROFILE%\qdc_auto_setup.bat
echo if %errorlevel% neq 0 ( >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [WARN] Python 未安裝，正在下載安裝程序... >> %USERPROFILE%\qdc_auto_setup.bat
echo     REM 下載 Python 安裝程序 >> %USERPROFILE%\qdc_auto_setup.bat
echo     powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe' -OutFile '%TEMP%\python-installer.exe'" >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [INFO] 正在安裝 Python，請稍候... >> %USERPROFILE%\qdc_auto_setup.bat
echo     %TEMP%\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [INFO] Python 安裝完成，請重新運行此腳本 >> %USERPROFILE%\qdc_auto_setup.bat
echo     exit /b 1 >> %USERPROFILE%\qdc_auto_setup.bat
echo ) else ( >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [SUCCESS] Python 已安裝: >> %USERPROFILE%\qdc_auto_setup.bat
echo     python --version >> %USERPROFILE%\qdc_auto_setup.bat
echo ) >> %USERPROFILE%\qdc_auto_setup.bat

echo REM 克隆倉庫 >> %USERPROFILE%\qdc_auto_setup.bat
echo echo [INFO] 正在克隆 GitHub 倉庫... >> %USERPROFILE%\qdc_auto_setup.bat
echo if not exist "C:\dragon-x-fall-detection" ( >> %USERPROFILE%\qdc_auto_setup.bat
echo     cd C:\ >> %USERPROFILE%\qdc_auto_setup.bat
echo     git clone https://github.com/andycywu/dragon-x-fall-detection.git >> %USERPROFILE%\qdc_auto_setup.bat
echo     if %errorlevel% neq 0 ( >> %USERPROFILE%\qdc_auto_setup.bat
echo         echo [ERROR] 克隆倉庫失敗 >> %USERPROFILE%\qdc_auto_setup.bat
echo         exit /b 1 >> %USERPROFILE%\qdc_auto_setup.bat
echo     ) >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [SUCCESS] 倉庫克隆成功 >> %USERPROFILE%\qdc_auto_setup.bat
echo ) else ( >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [INFO] 倉庫已存在，正在更新... >> %USERPROFILE%\qdc_auto_setup.bat
echo     cd C:\dragon-x-fall-detection >> %USERPROFILE%\qdc_auto_setup.bat
echo     git pull >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [SUCCESS] 倉庫更新完成 >> %USERPROFILE%\qdc_auto_setup.bat
echo ) >> %USERPROFILE%\qdc_auto_setup.bat

echo REM 安裝 Python 套件 >> %USERPROFILE%\qdc_auto_setup.bat
echo echo [INFO] 安裝 Python 套件... >> %USERPROFILE%\qdc_auto_setup.bat
echo cd C:\dragon-x-fall-detection >> %USERPROFILE%\qdc_auto_setup.bat
echo pip install numpy opencv-python onnxruntime >> %USERPROFILE%\qdc_auto_setup.bat
echo pip install -r requirements.txt >> %USERPROFILE%\qdc_auto_setup.bat
echo pip install -U qai-hub qai-hub-models "protobuf==4.25.3" >> %USERPROFILE%\qdc_auto_setup.bat

echo REM 設置 QAI Hub 配置 >> %USERPROFILE%\qdc_auto_setup.bat
echo echo [INFO] 設置 QAI Hub 配置... >> %USERPROFILE%\qdc_auto_setup.bat
echo if not exist "%USERPROFILE%\.qai_hub" mkdir "%USERPROFILE%\.qai_hub" >> %USERPROFILE%\qdc_auto_setup.bat
echo echo [default] ^> "%USERPROFILE%\.qai_hub\client.ini" >> %USERPROFILE%\qdc_auto_setup.bat
echo echo api_token = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d ^>^> "%USERPROFILE%\.qai_hub\client.ini" >> %USERPROFILE%\qdc_auto_setup.bat
echo echo api_key = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d ^>^> "%USERPROFILE%\.qai_hub\client.ini" >> %USERPROFILE%\qdc_auto_setup.bat
echo echo base_api_url = https://app.aihub.qualcomm.com ^>^> "%USERPROFILE%\.qai_hub\client.ini" >> %USERPROFILE%\qdc_auto_setup.bat
echo echo web_url = https://app.aihub.qualcomm.com ^>^> "%USERPROFILE%\.qai_hub\client.ini" >> %USERPROFILE%\qdc_auto_setup.bat

echo REM 測試 QAI Hub 連接 >> %USERPROFILE%\qdc_auto_setup.bat
echo echo [INFO] 測試 QAI Hub 連接... >> %USERPROFILE%\qdc_auto_setup.bat
echo python -c "import qai_hub as hub; print('可用設備:', [d.name for d in hub.get_devices()])" 2^>nul >> %USERPROFILE%\qdc_auto_setup.bat
echo if %errorlevel% neq 0 ( >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [WARN] QAI Hub 連接失敗，請手動檢查配置 >> %USERPROFILE%\qdc_auto_setup.bat
echo ) else ( >> %USERPROFILE%\qdc_auto_setup.bat
echo     echo [SUCCESS] QAI Hub 連接成功 >> %USERPROFILE%\qdc_auto_setup.bat
echo ) >> %USERPROFILE%\qdc_auto_setup.bat

echo echo. >> %USERPROFILE%\qdc_auto_setup.bat
echo echo [SUCCESS] 環境設置完成！ >> %USERPROFILE%\qdc_auto_setup.bat
echo echo. >> %USERPROFILE%\qdc_auto_setup.bat
echo echo [INFO] 現在您可以運行: >> %USERPROFILE%\qdc_auto_setup.bat
echo echo     cd C:\dragon-x-fall-detection >> %USERPROFILE%\qdc_auto_setup.bat
echo echo     python dragon_x_fall_detection_system.py >> %USERPROFILE%\qdc_auto_setup.bat
echo echo. >> %USERPROFILE%\qdc_auto_setup.bat

echo endlocal >> %USERPROFILE%\qdc_auto_setup.bat
