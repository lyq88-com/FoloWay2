@echo off
REM ===========================================
REM   One-click startup for liyeqing full stack (dev)
REM   Starts ALL THREE backends in separate windows:
REM     - Flask auth backend       (port 5000)
REM     - FastAPI business backend (port 8000)
REM     - Flask AI chat backend    (port 5001, ai_server.py)
REM   Frontend H5 (port 8080) must be started
REM   from HBuilderX: Run -> Run to Browser -> Built-in Browser
REM   NOTE: this file must stay pure ASCII (no Chinese)
REM   because cmd.exe parses .bat in ANSI codepage.
REM ===========================================
setlocal

set ROOT=%~dp0
set PYTHON=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

if not exist "%PYTHON%" (
    where python >nul 2>&1 && (set PYTHON=python) || (
        echo [ERROR] python.exe not found
        pause & exit /b 1
    )
)

echo ===========================================
echo   [1/3] Starting Flask auth backend (5000) ...
echo ===========================================
netstat -ano | findstr ":5000 " | findstr LISTENING >nul
if %errorlevel%==0 (
    echo   [OK] port 5000 already listening, skip
) else (
    start "Flask-Auth-5000" cmd /k "cd /d %ROOT%server-flask && %PYTHON% app.py"
)

echo ===========================================
echo   [2/3] Starting FastAPI backend (8000) ...
echo ===========================================
netstat -ano | findstr ":8000 " | findstr LISTENING >nul
if %errorlevel%==0 (
    echo   [OK] port 8000 already listening, skip
) else (
    start "FastAPI-8000" cmd /k "cd /d %ROOT%server && %PYTHON% -m app.main"
)

echo ===========================================
echo   [3/3] Starting Flask AI chat backend (5001) ...
echo ===========================================
netstat -ano | findstr ":5001 " | findstr LISTENING >nul
if %errorlevel%==0 (
    echo   [OK] port 5001 already listening, skip
) else (
    start "Flask-AI-5001" cmd /k "cd /d %ROOT%server-flask && %PYTHON% ai_server.py"
)

echo.
echo ===========================================
echo   Started services:
echo     Flask   : http://localhost:5000  (auth)
echo     FastAPI : http://localhost:8000  (business API)
echo     Flask AI: http://localhost:5001  (AI chat, zhipu glm-4-flash)
echo     H5      : http://localhost:8080  (run from HBuilderX)
echo.
echo   Health check URLs:
echo     http://localhost:5000/api/health
echo     http://localhost:8000/health
echo     http://localhost:5001/ai/health
echo.
echo   NEXT STEP (important):
echo     Start the frontend in HBuilderX:
echo       Run -^> Run to Browser -^> Built-in Browser
echo.
echo   To stop: close the three command windows
echo ===========================================
REM When launched from the Startup shortcut (arg "boot"),
REM skip the pause so the window closes automatically.
if /i not "%~1"=="boot" pause
