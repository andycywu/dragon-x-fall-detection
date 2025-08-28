@echo off
REM start.bat - Windows launcher for infer_demo
REM Creates/activates a project-local virtualenv (.venv_infer) and runs the live demo.

setlocal

nSET SCRIPT_DIR=%~dp0
SET VENV_DIR=%SCRIPT_DIR%\.venv_infer
SET REQ_FILE=%SCRIPT_DIR%\requirements_infer.txt

necho [infer_demo] project: %SCRIPT_DIR%

nwhere python >nul 2>&1
if errorlevel 1 (
  echo 找不到 python，請先安裝 Python 3.8+ 並加入 PATH。
  exit /b 1
)

nREM Create venv if missing
if not exist "%VENV_DIR%\Scripts\activate.bat" (
  echo 建立虛擬環境: %VENV_DIR%
  python -m venv "%VENV_DIR%"
  echo 升級 pip, setuptools, wheel...
  "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
  if exist "%REQ_FILE%" (
    echo 安裝 requirements from %REQ_FILE%
    "%VENV_DIR%\Scripts\pip.exe" install -r "%REQ_FILE%"
  ) else (
    echo 找不到需求檔 %REQ_FILE%，請確認路徑。
  )
) else (
  echo 虛擬環境已存在: %VENV_DIR%
)

nREM Activate venv
call "%VENV_DIR%\Scripts\activate.bat"

nREM Ensure streamlit available
where streamlit >nul 2>&1
if errorlevel 1 (
  echo 在虛擬環境中找不到 streamlit，嘗試安裝...
  pip install streamlit
)

nSET LIVE_PY=%SCRIPT_DIR%src\infer_demo_Mac\live_demo_mac.py
if not exist "%LIVE_PY%" (
  echo 找不到 %LIVE_PY%，請確認 live demo 檔案路徑。
  exit /b 1
)

necho 啟動 live demo...
streamlit run "%LIVE_PY%" %*
endlocal
