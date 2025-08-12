@echo off
chcp 65001 > nul
REM 修復 QAI Hub client.ini 配置文件 - 全面強化版

echo ========================================================================
echo                Dragon X Fall Detection - QAI Hub 配置修復工具
echo ========================================================================
echo.

REM 設置顏色
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RESET=[0m"

REM 顯示系統信息
echo %BLUE%系統診斷:%RESET%
echo 操作系統: Windows
echo 用戶名: %USERNAME%
echo 用戶配置目錄: %USERPROFILE%
echo.

REM 設置 API 令牌
set API_TOKEN=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d

REM 檢查 QAI Hub 相關目錄
set QAI_CONFIG_DIR=%USERPROFILE%\.qai_hub
echo %BLUE%1) 檢查 QAI Hub 配置目錄...%RESET%
if not exist "%QAI_CONFIG_DIR%" (
    echo %YELLOW%QAI Hub 配置目錄不存在，正在創建...%RESET%
    mkdir "%QAI_CONFIG_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo %RED%錯誤: 無法創建 QAI Hub 配置目錄%RESET%
        goto :failed
    ) else (
        echo %GREEN%已成功創建 QAI Hub 配置目錄%RESET%
    )
) else (
    echo %GREEN%QAI Hub 配置目錄已存在%RESET%
)

REM 備份舊文件（如果存在）
set CLIENT_INI=%QAI_CONFIG_DIR%\client.ini
if exist "%CLIENT_INI%" (
    echo.
    echo %BLUE%備份現有 client.ini 文件...%RESET%
    copy "%CLIENT_INI%" "%CLIENT_INI%.bak" > nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo %YELLOW%警告: 無法備份現有 client.ini 文件%RESET%
    ) else (
        echo %GREEN%已備份現有 client.ini 文件到 %CLIENT_INI%.bak%RESET%
    )
)

REM 創建 client.ini 文件 - 確保格式正確
echo.
echo %BLUE%2) 創建 client.ini 文件...%RESET%
echo [DEFAULT] > "%CLIENT_INI%"
echo api_key = %API_TOKEN% >> "%CLIENT_INI%"

REM 設置環境變量 - 多種方式
echo.
echo %BLUE%3) 設置環境變量...%RESET%
setx QAI_HUB_API_TOKEN "%API_TOKEN%" > nul 2>&1
echo %GREEN%已設置 QAI_HUB_API_TOKEN 環境變量%RESET%

REM 同時使用 .env 文件
echo QAI_HUB_API_TOKEN=%API_TOKEN% > "%USERPROFILE%\.env"
echo %GREEN%已創建 .env 文件%RESET%

REM 設置當前會話的環境變量
set QAI_HUB_API_TOKEN=%API_TOKEN%
set QAI_API_KEY=%API_TOKEN%

REM 驗證配置文件
echo.
echo %BLUE%4) 驗證配置文件...%RESET%
if exist "%CLIENT_INI%" (
    echo %GREEN%✅ client.ini 文件已創建: %CLIENT_INI%%RESET%
    echo.
    echo %BLUE%client.ini 文件內容:%RESET%
    type "%CLIENT_INI%"
    echo.
) else (
    echo %RED%❌ client.ini 文件創建失敗%RESET%
    goto :failed
)

REM 檢查 Python 相關配置
echo.
echo %BLUE%5) 檢查 Python 環境...%RESET%
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %YELLOW%警告: Python 未安裝或不在 PATH 中%RESET%
) else (
    echo %GREEN%Python 已安裝%RESET%
    
    REM 檢查 QAI Hub SDK
    pip show qai-hub > nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo %YELLOW%警告: QAI Hub SDK 未安裝%RESET%
        echo 請安裝 QAI Hub SDK: pip install qai-hub
    ) else (
        echo %GREEN%QAI Hub SDK 已安裝%RESET%
    )
    
    REM 檢查 protobuf 版本
    pip show protobuf > nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo %YELLOW%警告: protobuf 未安裝%RESET%
        echo 請安裝 protobuf: pip install protobuf==4.25.3
    ) else (
        for /f "tokens=2" %%i in ('pip show protobuf ^| findstr Version') do set PROTOBUF_VERSION=%%i
        echo 當前 protobuf 版本: %PROTOBUF_VERSION%
        
        if "%PROTOBUF_VERSION%"=="4.25.3" (
            echo %GREEN%protobuf 版本正確 (4.25.3)%RESET%
        ) else (
            echo %YELLOW%警告: protobuf 版本可能不兼容，建議使用 4.25.3 版本%RESET%
            echo 請安裝 protobuf 4.25.3: pip install protobuf==4.25.3
        )
    )
    
    REM 嘗試執行 Python 修復工具
    if exist "fix_client_ini.py" (
        echo.
        echo %BLUE%6) 運行 Python 修復工具...%RESET%
        python fix_client_ini.py
    )
)

echo.
echo %GREEN%========================================================================%RESET%
echo %GREEN%                      修復操作完成!                                     %RESET%
echo %GREEN%========================================================================%RESET%
echo.
echo 請嘗試運行 device_cloud_launch.bat
echo.
echo 如果仍然有問題，請嘗試:
echo 1) 確認配置文件內容是否正確（必須包含 [DEFAULT] 和 api_key）
echo 2) 確認環境變量是否設置正確
echo 3) 安裝兼容的 protobuf 版本: pip install protobuf==4.25.3
echo 4) 重啟電腦後再試
echo 5) 檢查網絡連接
echo 6) 確保防火牆不阻止 Python 程序訪問網絡
goto :end

:failed
echo.
echo %RED%========================================================================%RESET%
echo %RED%                      修復操作失敗!                                     %RESET%
echo %RED%========================================================================%RESET%
echo.
echo 請嘗試以下操作:
echo 1) 以管理員身份運行此批處理文件
echo 2) 檢查您的用戶帳戶是否有寫入 %USERPROFILE% 目錄的權限
echo 3) 手動創建 %USERPROFILE%\.qai_hub\client.ini 文件，內容如下:
echo    [DEFAULT]
echo    api_key = h0eubh7un3kk64u6oxisg9rbt8bbgubs913bzls2
echo 4) 檢查防病毒軟件是否阻止了此操作

:end
echo.
echo 按任意鍵退出...
pause > nul
