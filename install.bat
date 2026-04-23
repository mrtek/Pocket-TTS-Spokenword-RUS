@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Pocket-TTS Portable Installation
echo ========================================
echo.

:: Set portable paths
set "PORTABLE_ROOT=%~dp0"
set "PORTABLE_ROOT=%PORTABLE_ROOT:~0,-1%"
set "UV_TOOL_DIR=%PORTABLE_ROOT%\.portable\uv"
set "UV_CACHE_DIR=%PORTABLE_ROOT%\.portable\cache"
set "PYTHON_DIR=%PORTABLE_ROOT%\.portable\python"
set "VENV_DIR=%PORTABLE_ROOT%\.venv"

:: Create portable directories
if not exist "%PORTABLE_ROOT%\.portable" mkdir "%PORTABLE_ROOT%\.portable"
if not exist "%UV_TOOL_DIR%" mkdir "%UV_TOOL_DIR%"
if not exist "%UV_CACHE_DIR%" mkdir "%UV_CACHE_DIR%"

echo [1/5] Checking for uv package manager...
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo uv not found in system PATH. Installing portable uv...

    :: Download uv installer
    echo Downloading uv installer...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& {Invoke-WebRequest -Uri 'https://astral.sh/uv/install.ps1' -OutFile '%TEMP%\uv-install.ps1'}"

    if !errorlevel! neq 0 (
        echo ERROR: Failed to download uv installer
        pause
        exit /b 1
    )

    :: Install uv to portable directory
    echo Installing uv to portable directory...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& {$env:UV_INSTALL_DIR='%UV_TOOL_DIR%'; & '%TEMP%\uv-install.ps1'}"

    if !errorlevel! neq 0 (
        echo ERROR: Failed to install uv
        pause
        exit /b 1
    )

    del "%TEMP%\uv-install.ps1" >nul 2>&1
    set "PATH=%UV_TOOL_DIR%;%PATH%"
    echo uv installed successfully to portable directory
) else (
    echo uv found in system PATH
    echo Note: Using system uv, but Python and dependencies will be portable
)

echo.
echo [2/5] Installing Python and main dependencies...
echo This may take several minutes on first run...

:: Set environment variables for portable operation
set "UV_PYTHON_INSTALL_DIR=%PYTHON_DIR%"
set "UV_PROJECT_ENVIRONMENT=%VENV_DIR%"

:: Force Python 3.12 (3.13 has compatibility issues with numpy on Windows)
set "UV_PYTHON=3.12"

:: Run uv sync to install dependencies
"%UV_TOOL_DIR%\uv.exe" sync --cache-dir "%UV_CACHE_DIR%" --python 3.12
if %errorlevel% neq 0 (
    echo ERROR: Failed to install main dependencies with uv
    echo.
    echo Attempting to install with pip as fallback...

    :: Create venv with Python 3.12 if it doesn't exist
    if not exist "%VENV_DIR%\Scripts\python.exe" (
        echo Creating Python 3.12 virtual environment...
        "%UV_TOOL_DIR%\uv.exe" venv "%VENV_DIR%" --python 3.12 --cache-dir "%UV_CACHE_DIR%"
    )

    :: Install pip
    "%VENV_DIR%\Scripts\python.exe" -m ensurepip --upgrade
    "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip

    :: Install dependencies with pip, preferring binary wheels
    echo Installing dependencies with pip...
    "%VENV_DIR%\Scripts\python.exe" -m pip install --prefer-binary -e .

    if !errorlevel! neq 0 (
        echo ERROR: Installation failed with both uv and pip
        pause
        exit /b 1
    )
    echo Fallback installation completed successfully
)

echo Main dependencies installed successfully

echo.
echo [3/4] Creating portable configuration...

:: Create portable environment file
(
echo # Portable Environment Configuration
echo UV_TOOL_DIR=%UV_TOOL_DIR%
echo UV_CACHE_DIR=%UV_CACHE_DIR%
echo UV_PYTHON_INSTALL_DIR=%PYTHON_DIR%
echo UV_PROJECT_ENVIRONMENT=%VENV_DIR%
echo PORTABLE_ROOT=%PORTABLE_ROOT%
) > "%PORTABLE_ROOT%\.portable\env.txt"

echo Configuration saved

echo.
echo [4/4] Verifying installation...

:: Test if Python is available
"%VENV_DIR%\Scripts\python.exe" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Python verification failed
) else (
    echo Python: OK
)

:: Test if main packages are available
"%VENV_DIR%\Scripts\python.exe" -c "import torch; import transformers; import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Some packages may not be installed correctly
) else (
    echo Packages: OK
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo All files are contained in: %PORTABLE_ROOT%
echo.
echo To start the application, run: start.bat
echo.
echo NOTE: On first run, Silero TTS (~59 MB) and RuBERT (~100 MB)
echo models will be downloaded automatically from the internet.
echo.
pause
