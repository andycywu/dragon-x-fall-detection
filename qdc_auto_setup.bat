@echo off
setlocal EnableDelayedExpansion

echo ==========================================
echo QDC Auto Setup Tool
echo ==========================================

echo Checking environment...

REM Check Git installation
where git >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Git is installed.
    for /f "tokens=*" %%i in ('git --version') do set GIT_VERSION=%%i
    echo Version: !GIT_VERSION!
) else (
    echo WARNING: Git is not installed or not in PATH.
)

REM Check Python installation
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python is installed.
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo Version: !PYTHON_VERSION!
) else (
    echo WARNING: Python is not installed or not in PATH.
)

echo Checking repository...
if not exist "C:\dragon-x-fall-detection" (
    echo Cloning repository...
    cd C:\
    git clone https://github.com/andycywu/dragon-x-fall-detection.git
    if %ERRORLEVEL% EQU 0 (
        echo Repository cloned successfully.
    ) else (
        echo ERROR: Failed to clone repository.
        goto :error
    )
) else (
    echo Repository exists, updating...
    cd C:\dragon-x-fall-detection
    git pull
    if %ERRORLEVEL% EQU 0 (
        echo Repository updated successfully.
    ) else (
        echo ERROR: Failed to update repository.
        goto :error
    )
)

echo Checking QAI Hub configuration...
if not exist "%USERPROFILE%\.qai_hub\client.ini" (
    echo Creating QAI Hub configuration...
    if not exist "%USERPROFILE%\.qai_hub" mkdir "%USERPROFILE%\.qai_hub"
    (
        echo [default]
        echo api_token = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
        echo api_key = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
        echo base_api_url = https://app.aihub.qualcomm.com
        echo web_url = https://app.aihub.qualcomm.com
    ) > "%USERPROFILE%\.qai_hub\client.ini"
    echo QAI Hub configuration created successfully.
) else (
    echo QAI Hub configuration already exists.
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Checking Python packages...
    python -c "import numpy; print('OK')" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo Core Python packages are installed.
    ) else (
        echo Python packages may be missing.
        set /p INSTALL_PACKAGES=Install Python packages? (y/n): 
        if /i "!INSTALL_PACKAGES!"=="y" (
            echo Installing Python packages...
            cd C:\dragon-x-fall-detection
            pip install numpy opencv-python onnxruntime
            pip install -r requirements.txt
            pip install -U qai-hub qai-hub-models "protobuf==4.25.3"
            if %ERRORLEVEL% EQU 0 (
                echo Python packages installed successfully.
            ) else (
                echo ERROR: Failed to install Python packages.
                goto :error
            )
        ) else (
            echo Skipping Python package installation.
        )
    )
)

echo ==========================================
echo Setup completed successfully!
echo ==========================================
goto :end

:error
echo ==========================================
echo Setup failed!
echo ==========================================
exit /b 1

:end
echo You can now run Python scripts from C:\dragon-x-fall-detection
echo Example: cd C:\dragon-x-fall-detection && python final_qai_hub_onnx_system.py
endlocal
