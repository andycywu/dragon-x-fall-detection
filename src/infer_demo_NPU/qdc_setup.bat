@echo off
setlocal enabledelayedexpansion

echo [INFO] QDC Windows 環境設置腳本開始執行...

rem 設置顏色
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "BLUE=[34m"
set "NC=[0m"

rem 獲取當前日期時間
for /f "tokens=2 delims==" %%a in ('wmic OS get LocalDateTime /value') do set dt=%%a
set "TIMESTAMP=%dt:~0,8%-%dt:~8,6%"

rem 設置工作目錄
set "WORK_DIR=%USERPROFILE%\qdc_workspace"
echo %YELLOW%[INFO]%NC% 工作目錄設置為: %WORK_DIR%

rem 創建工作目錄（如果不存在）
if not exist "%WORK_DIR%" (
    echo %YELLOW%[INFO]%NC% 創建工作目錄...
    mkdir "%WORK_DIR%"
    echo %GREEN%[SUCCESS]%NC% 工作目錄創建完成
) else (
    echo %BLUE%[INFO]%NC% 工作目錄已存在
)

rem 切換到工作目錄
cd /d "%WORK_DIR%"
echo %BLUE%[INFO]%NC% 當前工作目錄: %CD%

rem 檢查 Git 倉庫
if not exist "%WORK_DIR%\.git" (
    echo %YELLOW%[INFO]%NC% 初始化 Git 倉庫...
    git init
    echo %GREEN%[SUCCESS]%NC% Git 倉庫初始化完成
    
    echo %YELLOW%[INFO]%NC% 添加遠程倉庫...
    git remote add origin https://github.com/qualcomm-qai/qai-hub-examples.git
    echo %GREEN%[SUCCESS]%NC% 已添加遠程倉庫
    
    echo %YELLOW%[INFO]%NC% 下載倉庫內容...
    git fetch origin
    echo %GREEN%[SUCCESS]%NC% 已下載倉庫內容
    
    echo %YELLOW%[INFO]%NC% 切換到主分支...
    git checkout main
    echo %GREEN%[SUCCESS]%NC% 已切換到主分支
) else (
    echo %BLUE%[INFO]%NC% Git 倉庫已存在，更新到最新...
    git pull origin main
    echo %GREEN%[SUCCESS]%NC% Git 倉庫已更新
)

rem 設置 Python 虛擬環境
set "VENV_DIR=%WORK_DIR%\venv"
if not exist "%VENV_DIR%" (
    echo %YELLOW%[INFO]%NC% 創建 Python 虛擬環境...
    python -m venv "%VENV_DIR%"
    echo %GREEN%[SUCCESS]%NC% Python 虛擬環境創建完成
) else (
    echo %BLUE%[INFO]%NC% Python 虛擬環境已存在
)

rem 激活虛擬環境
echo %YELLOW%[INFO]%NC% 激活 Python 虛擬環境...
call "%VENV_DIR%\Scripts\activate.bat"
echo %GREEN%[SUCCESS]%NC% Python 虛擬環境已激活

rem 升級 pip
echo %YELLOW%[INFO]%NC% 升級 pip...
python -m pip install --upgrade pip
echo %GREEN%[SUCCESS]%NC% pip 已升級

rem 安裝 QAI Hub 及相關依賴
echo %YELLOW%[INFO]%NC% 安裝 QAI Hub 及相關依賴...
pip install qai-hub
pip install -r "%WORK_DIR%\requirements.txt"
echo %GREEN%[SUCCESS]%NC% QAI Hub 及相關依賴安裝完成

rem 配置 QAI Hub 客戶端
echo %YELLOW%[INFO]%NC% 配置 QAI Hub 客戶端...
python -m qai_hub.client config dev

rem 打印完成信息
echo.
echo %GREEN%=========================================%NC%
echo %GREEN%[SUCCESS] QDC 環境設置完成!%NC%
echo %GREEN%=========================================%NC%
echo.
echo %BLUE%[提示] 可以通過以下命令開始使用 QAI Hub:%NC%
echo.
echo cd "%WORK_DIR%"
echo call "%VENV_DIR%\Scripts\activate.bat"
echo python -c "import qai_hub as hub; print(hub.get_model_zoo())"
echo.

rem 等待用戶按任意鍵繼續
pause

endlocal
