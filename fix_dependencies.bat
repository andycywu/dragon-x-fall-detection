@echo off
chcp 65001 > nul
REM 修復相依性問題腳本

echo === Dragon X Fall Detection System - 相依性修復工具 ===
echo ======================================================

setlocal

REM 檢查是否在虛擬環境中
if exist .venv (
  echo 使用虛擬環境...
  call .venv\Scripts\activate
) else (
  echo 使用系統 Python...
)

echo 1) 修復 protobuf 版本衝突
echo 安裝 protobuf 4.25.3 (MediaPipe 相容版本)...
pip install protobuf==4.25.3

echo 2) 修復 QAI Hub 相依性
echo 重新安裝 QAI Hub (指定相容版本)...
pip install qai-hub==0.31.0 qai-hub-models==0.33.1

echo 3) 設置 QAI Hub 認證
echo 設置 API 令牌環境變數...
setx QAI_HUB_API_TOKEN "h0eubh7un3kk64u6oxisg9rbt8bbgubs913bzls2" >nul
echo QAI_HUB_API_TOKEN=h0eubh7un3kk64u6oxisg9rbt8bbgubs913bzls2 > "%USERPROFILE%\.env"

echo 設置 QAI Hub 認證...
python setup_qai_hub.py --token h0eubh7un3kk64u6oxisg9rbt8bbgubs913bzls2 --force

echo 4) 修復 QAI Hub client.ini 配置（重點）
echo 創建 .qai_hub 目錄...
if not exist "%USERPROFILE%\.qai_hub" mkdir "%USERPROFILE%\.qai_hub"

echo 創建 client.ini 文件...
echo [DEFAULT] > "%USERPROFILE%\.qai_hub\client.ini"
echo api_key = h0eubh7un3kk64u6oxisg9rbt8bbgubs913bzls2 >> "%USERPROFILE%\.qai_hub\client.ini"

echo 驗證 client.ini 文件...
if exist "%USERPROFILE%\.qai_hub\client.ini" (
  echo 成功: client.ini 文件已創建
  type "%USERPROFILE%\.qai_hub\client.ini"
) else (
  echo 錯誤: client.ini 文件創建失敗
)

echo 運行專用修復工具...
python fix_client_ini.py

echo 5) 測試 MediaPipe 相容性
python -c "import mediapipe as mp; print('MediaPipe 版本:', mp.__version__); print('MediaPipe 初始化成功')" 2>nul
if %errorlevel% neq 0 (
  echo [警告] MediaPipe 測試失敗，嘗試重新安裝...
  pip install mediapipe==0.10.14
) else (
  echo MediaPipe 測試成功
)

echo ✅ 相依性修復完成！
echo 建議重新啟動系統並執行 device_cloud_launch.bat

if exist .venv (
  call .venv\Scripts\deactivate
)

endlocal
