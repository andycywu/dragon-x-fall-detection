@echo off
REM Qualcomm Snapdragon 套件安裝腳本（加速版：優先離線 / ARM64 原生）

setlocal ENABLEDELAYEDEXPANSION

echo === Dragon X Fall Detection System - 套件安裝器 ===
echo =====================================================

REM 0) Python / pip 檢查
where python >nul 2>nul || (
  echo [ERROR] 未找到 python。請先安裝 Python 3.10+ 並加入 PATH。
  exit /b 1
)
where pip >nul 2>nul || (
  echo [ERROR] 未找到 pip。請確認 Python 已正確安裝。
  exit /b 1
)

REM 1) 檢測 CPU 架構
for /f "tokens=2 delims==" %%i in ('wmic os get osarchitecture /value') do set ARCH=%%i
echo 檢測到系統架構: %ARCH%

set IS_ARM64=0
set IS_X64=0
echo %ARCH% | findstr /i "ARM" >nul && set IS_ARM64=1
echo %ARCH% | findstr /i "64"  >nul && set IS_X64=1

REM 2) 建立虛擬環境（強烈建議）
if not exist .venv (
  echo === 建立 Python 虛擬環境 .venv ...
  python -m venv .venv || (
    echo [WARN] 建立 venv 失敗，將改用系統 Python。
  )
)
if exist .venv (
  call .venv\Scripts\activate
  if errorlevel 1 (
    echo [WARN] 啟用 venv 失敗，將改用系統 Python。
  ) else (
    echo 已啟用 venv
  )
)

REM 3) PIP 參數：優先使用離線 wheelhouse，其次才上網
set PIP_EXTRA=
set PIP_SRC_FLAGS=--prefer-binary --only-binary=:all: --timeout 60 --retries 3
if exist wheelhouse\NUL (
  echo === 偵測到 wheelhouse/，採用離線安裝（不連網）...
  set PIP_EXTRA=--no-index --find-links=wheelhouse
) else (
  echo === 未偵測到 wheelhouse/，將連網安裝，並強制優先二進位套件...
  set PIP_EXTRA=%PIP_SRC_FLAGS%
)

REM 4) 升級 pip（若離線則略過升級）
if not "%PIP_EXTRA%"=="--no-index --find-links=wheelhouse" (
  python -m pip install -U pip %PIP_SRC_FLAGS%
)

REM 5) 共同必備套件（盡量選用有 wheel 的版本）
echo === 安裝共同必備套件 ===
REM * 避免用 opencv-python，改用 headless 減少體積
pip install %PIP_EXTRA% numpy==1.26.4 opencv-python-headless==4.10.0.84 requests>=2.25.0 Pillow>=8.0.0 streamlit>=1.28.0 || goto :pip_error

REM 6) ONNX Runtime 與加速器
pip install %PIP_EXTRA% onnxruntime==1.18.0 || goto :pip_error

if %IS_ARM64%==1 (
  echo === 檢測到 ARM64 ：啟用 QNN / DirectML 優先順序 ===
  REM 這兩個套件需有預建 wheel 才能快；若無將失敗並跳過（不嘗試從原始碼編譯）
  pip install %PIP_EXTRA% onnxruntime-directml==1.18.0 || echo [WARN] onnxruntime-directml 安裝失敗（略過）
  pip install %PIP_EXTRA% onnxruntime-qnn==1.18.0     || echo [WARN] onnxruntime-qnn 安裝失敗（略過）
) else (
  echo === x64/其他架構：維持 CPU/DirectML ===
  pip install %PIP_EXTRA% onnxruntime-directml==1.18.0 || echo [WARN] onnxruntime-directml 安裝失敗（略過）
)

REM 7) MediaPipe（僅安裝有 wheel 的版本；若失敗則略過以免觸發編譯）
echo === 安裝 MediaPipe（有 wheel 才裝，失敗將略過） ===
pip install %PIP_EXTRA% mediapipe==0.10.14 || echo [WARN] mediapipe 安裝失敗（略過）

REM 8) 語音/轉譯加速：改用 faster-whisper（ARM 友善；免裝 torch）
echo === 安裝語音推論工具（faster-whisper / ctranslate2） ===
pip install %PIP_EXTRA% ctranslate2==4.5.0 faster-whisper==1.0.0 || goto :pip_error

REM 9) （可選）PyTorch 與 TorchVision
REM * Windows on ARM 的官方 wheel 供應仍在演進中。若你確定需要，請先把相容 wheel 放進 wheelhouse 再啟用下列兩行。
REM if %IS_ARM64%==0 (
REM   pip install %PIP_EXTRA% torch==2.3.1 torchvision==0.18.1 || echo [WARN] PyTorch/TorchVision 安裝失敗（略過）
REM )

REM 10) QAI Hub SDK
pip install %PIP_EXTRA% qai-hub qai-hub-models || goto :pip_error

REM 10.1) 安裝和設置 QAI Hub 認證（新增）
echo === 設置 QAI Hub 認證 ===
python setup_qai_hub.py
if errorlevel 1 (
  echo [WARN] QAI Hub 認證設置失敗。請稍後手動執行 python setup_qai_hub.py
) else (
  echo QAI Hub 認證設置成功！
)

REM 11) 設定環境變數（僅 ARM64 ）
if %IS_ARM64%==1 (
  echo === 設置 ARM64 優化環境變數 ===
  setx ONNXRUNTIME_PROVIDER_PRIORITY "QNNExecutionProvider,DirectMLExecutionProvider,CPUExecutionProvider" >nul
  setx ORT_LOGGING_LEVEL "2" >nul
  echo ARM64 優化環境變數設置完成！
)

echo.
echo === 所有套件安裝完成！ ===
echo 若要獲得**最快**安裝：請在本機先執行 `pip download -r requirements.txt -d wheelhouse --only-binary=:all: --prefer-binary`，
echo 然後將 wheelhouse/ 連同專案一起上傳到裝置。

echo 請運行 device_cloud_launch.bat 啟動系統
exit /b 0

:pip_error
echo.
echo [ERROR] 有套件安裝失敗（已中止以避免從原始碼編譯）。
echo 1) 建議先在本機建立 wheelhouse 離線安裝；2) 確認所需版本在 ARM64 上有預建 wheel。
exit /b 2

endlocal
