@echo off
echo Dragon X Fall Detection System - Real QAI Hub Inference (ASCII Fixed)
echo =============================================================
echo.

REM Do not set legacy QAI_* env vars; rely on %USERPROFILE%\.qai_hub\client.ini
echo Using client.ini in %USERPROFILE%\.qai_hub for QAI Hub configuration
echo.

REM Python and CLI paths
set PY310=C:\Users\HCKTest\AppData\Local\Programs\Python\Python310\python.exe
set REPO_DIR=C:\dragon-x-fall-detection
set QAI_CLI_EXE=C:\Users\HCKTest\AppData\Local\Programs\Python\Python310\Scripts\qai-hub.exe

REM Resolve QAI Hub CLI path
if exist "%QAI_CLI_EXE%" (
    set QAI_CLI="%QAI_CLI_EXE%"
) else (
    set QAI_CLI=qai-hub
)

REM If user requested QAI Hub CLI workflows, route accordingly
if /I "%1"=="help" goto :help
if /I "%1"=="list-devices" goto :list_devices
if /I "%1"=="list-frameworks" goto :list_frameworks
if /I "%1"=="upload-model" goto :upload_model
if /I "%1"=="compile" goto :compile_job
if /I "%1"=="profile" goto :profile_job
if /I "%1"=="link" goto :link_job
if /I "%1"=="cap" goto :compile_and_profile
if /I "%1"=="inference" goto :profile_job
if /I "%1"=="run-app" goto :run_app

REM Default: run the app
goto :run_app

:help
echo Usage:
echo   %~nx0 run-app [--camera-index N] [--onnx-model PATH] [--video PATH] [--upgrade-sdk]
echo   %~nx0 list-devices
echo   %~nx0 list-frameworks
echo   %~nx0 upload-model ^<args...^>             ^(wraps: qai-hub upload-model^)
echo   %~nx0 compile ^<args...^>                   ^(wraps: qai-hub submit-compile-job^)
echo   %~nx0 profile ^<args...^>                   ^(wraps: qai-hub submit-profile-job^)
echo   %~nx0 link ^<args...^>                      ^(wraps: qai-hub submit-link-job^)
echo   %~nx0 cap ^<args...^>                       ^(wraps: qai-hub submit-compile-and-profile-jobs^)
echo.
echo Notes:
echo  - This uses QAI Hub CLI: %QAI_CLI%
echo  - Provide required arguments per your AI Hub model/device settings.
goto :exit

:list_devices
%QAI_CLI% list-devices
goto :exit

:list_frameworks
%QAI_CLI% list-frameworks
goto :exit

:upload_model
shift
%QAI_CLI% upload-model %*
goto :exit

:compile_job
shift
%QAI_CLI% submit-compile-job %*
goto :exit

:profile_job
shift
%QAI_CLI% submit-profile-job %*
goto :exit

:link_job
shift
%QAI_CLI% submit-link-job %*
goto :exit

:compile_and_profile
shift
%QAI_CLI% submit-compile-and-profile-jobs %*
goto :exit

:run_app
REM Check if the Python script exists
if not exist "%REPO_DIR%\dragon_x_real_inference_ascii_fixed.py" (
        echo Error: dragon_x_real_inference_ascii_fixed.py not found in %REPO_DIR%
        goto :exit
)

echo Running Python script with correct Python path...
REM Forward all CLI args after 'run-app' to Python
setlocal ENABLEDELAYEDEXPANSION
set ARGS=
if /I "%1"=="run-app" (
    shift
    set ARGS=%*
)
"%PY310%" "%REPO_DIR%\dragon_x_real_inference_ascii_fixed.py" --camera-index 1 !ARGS!
endlocal

:exit
echo.
echo Fall Detection System execution completed
pause
