@echo off
REM QAI Hub 環境檢查與修復彙總批處理腳本
REM 此腳本執行所有診斷工具，提供全面的狀態報告

echo.
echo =========================================================
echo             QAI Hub 環境檢查與修復彙總工具               
echo =========================================================
echo.

REM 檢查操作系統
echo 檢測操作系統...
set OS=Windows
echo 檢測到 Windows 系統

REM 創建臨時目錄存放報告
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set REPORT_DIR=qai_hub_diagnostic_report_%TIMESTAMP%
mkdir "%REPORT_DIR%"

echo 診斷報告將保存在: %REPORT_DIR%
echo.

REM 步驟 1: 檢查 Python 環境
echo 步驟 1: 檢查 Python 環境...
python --version > NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 錯誤: 未找到 Python
    echo 請安裝 Python 3.7 或更高版本
    exit /b 1
)

for /f "tokens=*" %%a in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PYTHON_VERSION=%%a
echo 已找到 Python 版本: %PYTHON_VERSION%

REM 檢查 pip
pip --version > NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 錯誤: 未找到 pip
    echo 請安裝 pip
    exit /b 1
)
echo 已找到 pip
echo.

REM 步驟 2: 檢查 QAI Hub 狀態
echo 步驟 2: 檢查 QAI Hub 狀態...
echo 運行 QAI Hub 狀態檢查...
python check_qai_hub_status.py > "%REPORT_DIR%\qai_hub_status.txt" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo QAI Hub 狀態檢查完成
    echo 報告已保存到 %REPORT_DIR%\qai_hub_status.txt
) else (
    echo QAI Hub 狀態檢查失敗
    echo 請查看 %REPORT_DIR%\qai_hub_status.txt 獲取詳細信息
)

REM 步驟 3: 執行 API 連接測試
echo.
echo 步驟 3: 測試 QAI Hub API 連接...
echo 運行 Windows 版 API 測試工具...
python test_qai_hub_api_windows.py > "%REPORT_DIR%\api_test.txt" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo API 連接測試成功
    echo 測試結果已保存到 %REPORT_DIR%\api_test.txt
) else (
    echo API 連接測試失敗
    echo 請查看 %REPORT_DIR%\api_test.txt 獲取詳細信息
)

REM 步驟 4: 修復配置 (如果需要)
echo.
echo 步驟 4: 檢查是否需要修復配置...

REM 嘗試導入 qai_hub 模塊
python -c "import qai_hub" > NUL 2>&1
if %ERRORLEVEL% EQU 0 (
    echo qai_hub 模塊可以正常導入，配置可能已經正確
    set NEEDS_FIX=false
) else (
    echo qai_hub 模塊無法正常導入，可能需要修復配置
    set NEEDS_FIX=true
)

REM 根據前面的測試結果判斷是否需要修復
findstr /C:"總體狀態: 需要修復" "%REPORT_DIR%\qai_hub_status.txt" > NUL
if %ERRORLEVEL% EQU 0 (
    echo 根據狀態檢查，配置需要修復
    set NEEDS_FIX=true
)

if "%NEEDS_FIX%"=="true" (
    echo 嘗試修復 QAI Hub 配置...
    
    echo 運行 Windows 修復工具...
    if exist fix_qai_hub_client.bat (
        call fix_qai_hub_client.bat > "%REPORT_DIR%\fix_results.txt" 2>&1
    ) else (
        python fix_client_ini_windows.py > "%REPORT_DIR%\fix_results.txt" 2>&1
    )
    
    echo 修復嘗試完成
    echo 修復結果已保存到 %REPORT_DIR%\fix_results.txt
) else (
    echo 配置似乎正常，無需修復
)

REM 步驟 5: 檢查 QAI Hub 離線模式
echo.
echo 步驟 5: 測試 QAI Hub 離線模式...
if exist qai_hub_demo_offline.py (
    echo 測試離線演示模式功能...
    python qai_hub_demo_offline.py --test-all > "%REPORT_DIR%\offline_mode_test.txt" 2>&1
    
    if %ERRORLEVEL% EQU 0 (
        echo 離線模式測試成功
        echo 測試結果已保存到 %REPORT_DIR%\offline_mode_test.txt
    ) else (
        echo 離線模式測試失敗
        echo 請查看 %REPORT_DIR%\offline_mode_test.txt 獲取詳細信息
    )
) else (
    echo 未找到離線演示模式腳本，跳過此步驟
)

REM 步驟 6: 總結診斷結果
echo.
echo 步驟 6: 總結診斷結果...

REM 創建總結報告
set SUMMARY_FILE=%REPORT_DIR%\diagnostic_summary.txt
echo QAI Hub 診斷彙總報告 > "%SUMMARY_FILE%"
echo ====================== >> "%SUMMARY_FILE%"
echo 時間: %date% %time% >> "%SUMMARY_FILE%"
echo 操作系統: Windows >> "%SUMMARY_FILE%"
echo Python 版本: %PYTHON_VERSION% >> "%SUMMARY_FILE%"
echo. >> "%SUMMARY_FILE%"

REM 檢查狀態
findstr /C:"總體狀態: 良好" "%REPORT_DIR%\qai_hub_status.txt" > NUL
if %ERRORLEVEL% EQU 0 (
    echo QAI Hub 狀態: 良好 ^✓ >> "%SUMMARY_FILE%"
    set STATUS_OK=true
) else (
    echo QAI Hub 狀態: 需要修復 ^✗ >> "%SUMMARY_FILE%"
    set STATUS_OK=false
)

REM 檢查 API 測試
findstr /C:"全部成功" "%REPORT_DIR%\api_test.txt" > NUL
if %ERRORLEVEL% EQU 0 (
    echo API 連接: 成功 ^✓ >> "%SUMMARY_FILE%"
    set API_OK=true
) else (
    echo API 連接: 失敗 ^✗ >> "%SUMMARY_FILE%"
    set API_OK=false
)

REM 總體診斷
echo. >> "%SUMMARY_FILE%"
echo 總體診斷: >> "%SUMMARY_FILE%"

if "%STATUS_OK%"=="true" if "%API_OK%"=="true" (
    echo QAI Hub 環境正常，可以正常使用 >> "%SUMMARY_FILE%"
    set FINAL_STATUS=PASS
) else if exist "%REPORT_DIR%\fix_results.txt" (
    REM 檢查修復後的狀態
    echo 已嘗試修復配置，請重新運行診斷工具檢查修復結果 >> "%SUMMARY_FILE%"
    set FINAL_STATUS=NEEDS_RECHECK
) else (
    echo QAI Hub 環境存在問題，請參考以下建議: >> "%SUMMARY_FILE%"
    echo 1. 查看詳細診斷報告 ^(%REPORT_DIR%\qai_hub_status.txt^) >> "%SUMMARY_FILE%"
    echo 2. 參考故障排除指南 ^(QAI_HUB_TROUBLESHOOTING.md^) >> "%SUMMARY_FILE%"
    echo 3. 如果問題持續存在，可以使用離線模式 ^(python qai_hub_demo_offline.py^) >> "%SUMMARY_FILE%"
    set FINAL_STATUS=FAIL
)

REM 顯示總結
if "%FINAL_STATUS%"=="PASS" (
    echo.
    echo 診斷完成: QAI Hub 環境正常，可以正常使用 ^✓
) else if "%FINAL_STATUS%"=="NEEDS_RECHECK" (
    echo.
    echo 診斷完成: 已嘗試修復配置，請重新運行診斷工具檢查修復結果
) else (
    echo.
    echo 診斷完成: QAI Hub 環境存在問題 ^✗
    echo 請參考以下建議:
    echo 1. 查看詳細診斷報告 ^(%REPORT_DIR%\qai_hub_status.txt^)
    echo 2. 參考故障排除指南 ^(QAI_HUB_TROUBLESHOOTING.md^)
    echo 3. 如果問題持續存在，可以使用離線模式 ^(python qai_hub_demo_offline.py^)
)

echo.
echo 診斷報告已保存在: %REPORT_DIR%\diagnostic_summary.txt
echo 完整的診斷數據已保存在: %REPORT_DIR%

echo.
echo =========================================================
echo             QAI Hub 環境檢查與修復彙總工具完成           
echo =========================================================
echo.

pause
