@echo off
chcp 65001 >nul
echo =========================================================
echo           QAI Hub 正確設定工具
echo =========================================================
echo.

echo 此工具將設定 QAI Hub 使用正確的網址
echo.

set config_dir=%USERPROFILE%\.qai_hub
set config_file=%config_dir%\client.ini

if not exist %config_dir% (
    mkdir %config_dir%
    echo 已創建配置目錄。
)

echo 步驟 1: 設定 QAI Hub 配置...
echo [default]> %config_file%
echo api_token=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
echo api_key=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d>> %config_file%
echo base_api_url=https://app.aihub.qualcomm.com>> %config_file%
echo web_url=https://app.aihub.qualcomm.com>> %config_file%

echo.
echo 步驟 2: 驗證 Python 環境...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 未找到 Python。請確保 Python 已安裝並添加到 PATH 環境變量中。
    echo 可從 https://www.python.org/downloads/ 下載安裝 Python。
    goto end
)

echo.
echo 步驟 3: 檢查 QAI Hub 安裝...
pip show qai-hub >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo QAI Hub 尚未安裝。是否要安裝 QAI Hub？(Y/N)
    set /p install_choice=
    if /i "%install_choice%"=="Y" (
        echo 正在安裝 QAI Hub...
        pip install qai-hub qai-hub-models
        echo QAI Hub 安裝完成。
    ) else (
        echo 跳過 QAI Hub 安裝。請手動安裝後再使用此工具。
        goto end
    )
)

echo.
echo 步驟 4: 檢查 Windows 長路徑支持...
reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled 2>nul | findstr "0x1" >nul
if %ERRORLEVEL% NEQ 0 (
    echo 警告: Windows 長路徑支持尚未啟用。
    echo 這可能導致安裝 QAI Hub 套件時出現錯誤。
    echo.
    echo 是否要啟用 Windows 長路徑支持？(Y/N)
    echo 注意: 這需要管理員權限。
    set /p longpath_choice=
    if /i "%longpath_choice%"=="Y" (
        echo 正在創建註冊表文件...
        echo Windows Registry Editor Version 5.00> enable_long_paths.reg
        echo.>> enable_long_paths.reg
        echo [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem]>> enable_long_paths.reg
        echo "LongPathsEnabled"=dword:00000001>> enable_long_paths.reg
        
        echo 請以管理員身份運行 enable_long_paths.reg 並重啟計算機。
        echo 重啟後再次運行此腳本完成設置。
    )
) else (
    echo Windows 長路徑支持已啟用。很好！
)

echo.
echo 配置已保存到: %config_file%
echo.

echo 步驟 5: 執行簡單測試驗證配置...
echo import qai_hub> verify_test.py
timeout /t 1 /nobreak >nul
python verify_test.py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo QAI Hub 導入成功！
    echo 基本配置有效。
) else (
    echo QAI Hub 導入失敗。
    echo 可能需要重新安裝 QAI Hub 或檢查 Python 環境。
)

del verify_test.py >nul 2>&1

echo.
echo =========================================================
echo                       後續步驟
echo =========================================================
echo.
echo 1. 請確認您有在 QAI Hub 官方網站註冊帳號並獲取有效的 API 令牌
echo 2. 只使用官方 URL: https://app.aihub.qualcomm.com
echo 3. 安裝正確版本的 QAI Hub 套件:
echo    - pip install qai-hub==0.31.0 qai-hub-models==0.31.0
echo 4. 確保您的網絡環境可以正常訪問 QAI Hub 服務
echo.

:end
echo 按任意鍵退出...
pause >nul
