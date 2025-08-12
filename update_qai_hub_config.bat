@echo off
REM QAI Hub 配置更新工具（Windows 版本）
REM 此批處理文件執行 Python 更新腳本來修復 QAI Hub 配置

echo.
echo ==========================================================
echo              QAI Hub 配置更新工具             
echo ==========================================================
echo.

setlocal EnableDelayedExpansion

REM 定義 ANSI 顏色代碼（Windows 10 及以上支持）
set "ESC="
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set "ESC=%%b"
)

REM 檢查 Python 是否可用
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo !ESC![91m錯誤: 未找到 Python。請安裝 Python 3.6 或更高版本。!ESC![0m
    goto :END
)

REM 確認 Python 版本
python --version | findstr /i "Python 3" >nul
if %ERRORLEVEL% NEQ 0 (
    echo !ESC![93m警告: 可能不是 Python 3。QAI Hub 需要 Python 3.6 或更高版本。!ESC![0m
)

REM 檢查 Windows 長路徑支援
echo !ESC![36m檢查 Windows 長路徑支援...!ESC![0m
reg query "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled 2>nul | find "0x1" >nul
if %ERRORLEVEL% NEQ 0 (
    echo !ESC![93m警告: Windows 長路徑支援未啟用!ESC![0m
    echo !ESC![93m安裝某些 Python 套件時可能會遇到路徑過長錯誤!ESC![0m
    echo !ESC![36m要啟用長路徑支援，請以管理員身份執行以下命令:!ESC![0m
    echo !ESC![92m   reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f!ESC![0m
    echo !ESC![36m然後重新啟動電腦!ESC![0m
    echo.
    echo !ESC![36m或者可以使用短路徑的虛擬環境:!ESC![0m
    echo !ESC![92m   python -m venv C:\qai_env!ESC![0m
    echo !ESC![92m   C:\qai_env\Scripts\activate!ESC![0m
    echo.
) else (
    echo !ESC![92mWindows 長路徑支援已啟用!ESC![0m
)

echo !ESC![36m檢測到 Python，準備更新 QAI Hub 配置...!ESC![0m
echo.

REM 詢問用戶是否需要設置 API token
echo !ESC![92m是否需要設置 QAI Hub API Token? (Y/N)!ESC![0m
set /p NEED_TOKEN=

if /i "%NEED_TOKEN%"=="Y" (
    echo.
    echo !ESC![92m請輸入您的 QAI Hub API Token:!ESC![0m
    set /p API_TOKEN=
    echo.
    echo !ESC![36m使用提供的 Token 更新配置...!ESC![0m
    python update_qai_hub_config.py --token "%API_TOKEN%"
) else (
    echo.
    echo !ESC![36m使用現有 Token 更新配置...!ESC![0m
    python update_qai_hub_config.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo !ESC![91m更新過程中發生錯誤。!ESC![0m
    echo !ESC![93m請查看上面的錯誤信息，或嘗試手動更新配置文件。!ESC![0m
) else (
    echo.
    echo !ESC![92m配置更新過程完成。!ESC![0m
)

echo.
echo !ESC![36m如需了解更多信息，請參考 QAI_HUB_CONFIG_FIX.md 文件。!ESC![0m
echo.

:END
echo !ESC![36m按任意鍵退出...!ESC![0m
pause >nul
