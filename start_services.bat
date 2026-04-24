@echo off
REM T10 AIRPS - Complete Startup Script for Windows

echo.
echo ==========================================
echo T10 AI Incident Response System
echo Starting All Services...
echo ==========================================
echo.

REM Get the directory of this script
for /f %%i in ('cd') do set SCRIPT_DIR=%%i

REM Create logs directory
if not exist "%SCRIPT_DIR%\logs" mkdir "%SCRIPT_DIR%\logs"

echo 1. Installing backend dependencies...
cd /d "%SCRIPT_DIR%\major_project\backend"
pip install -q -r requirements.txt

echo 2. Installing frontend dependencies...
cd /d "%SCRIPT_DIR%\major_project\frontend"
call npm install > nul 2>&1

echo.
echo 3. Starting Backend Server (port 8000)...
cd /d "%SCRIPT_DIR%\major_project\backend"
start "T10-Backend" python -m uvicorn main:app --host 0.0.0.0 --port 8000

echo.
echo 4. Waiting for backend to initialize...
timeout /t 3 /nobreak

echo.
echo 5. Starting Frontend Server (port 5173)...
cd /d "%SCRIPT_DIR%\major_project\frontend"
start "T10-Frontend" cmd /k npm run dev

echo.
echo ==========================================
echo T10 System Started Successfully!
echo ==========================================
echo.
echo Access Points:
echo   Web UI:        http://localhost:5173
echo   API:           http://localhost:8000
echo   API Docs:      http://localhost:8000/api/docs
echo   Health Check:  http://localhost:8000/api/health
echo.
echo Default Credentials:
echo   Username: admin
echo   Password: Admin@1234
echo.
echo Logs:
echo   Backend:  %SCRIPT_DIR%\logs\backend.log
echo   Frontend: %SCRIPT_DIR%\logs\frontend.log
echo.
echo The web UI is loading in your browser...
echo To stop services, close the command windows.
echo.

timeout /t 3 /nobreak

REM Open web browser
start http://localhost:5173

pause
