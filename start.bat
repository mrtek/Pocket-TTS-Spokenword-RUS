@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Set portable paths
set "PORTABLE_ROOT=%~dp0"
set "PORTABLE_ROOT=%PORTABLE_ROOT:~0,-1%"
set "UV_TOOL_DIR=%PORTABLE_ROOT%\.portable\uv"
set "UV_CACHE_DIR=%PORTABLE_ROOT%\.portable\cache"
set "PYTHON_DIR=%PORTABLE_ROOT%\.portable\python"
set "VENV_DIR=%PORTABLE_ROOT%\.venv"

:: Check if installation exists
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo ERROR: Installation not found!
    echo Please run install.bat first
    echo.
    pause
    exit /b 1
)

:: Set environment variables for portable operation
set "UV_PYTHON_INSTALL_DIR=%PYTHON_DIR%"
set "UV_PROJECT_ENVIRONMENT=%VENV_DIR%"
set "UV_CACHE_DIR=%UV_CACHE_DIR%"
set "PATH=%UV_TOOL_DIR%;%VENV_DIR%\Scripts;%PATH%"

:: Change to project directory
cd /d "%PORTABLE_ROOT%"

echo ========================================
echo Starting Pocket-TTS Audiobook Generator
echo ========================================
echo.

:: Check if uv is available
where uv >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%UV_TOOL_DIR%\uv.exe" (
        set "PATH=%UV_TOOL_DIR%;%PATH%"
    ) else (
        echo WARNING: uv not found, using direct Python execution
        goto :direct_run
    )
)

:: Run using uv (preferred method)
echo Launching GUI application...
uv run python launch_gui.py
goto :end

:direct_run
:: Fallback: run directly with venv Python
echo Launching GUI application (direct mode)...
"%VENV_DIR%\Scripts\python.exe" launch_gui.py

:end
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application failed to start
    echo Error code: %errorlevel%
    echo.
    pause
    exit /b %errorlevel%
)

exit /b 0
