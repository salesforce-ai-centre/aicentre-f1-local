@echo off
REM F1 Simulator System - Windows Batch Launcher
REM Alternative to PowerShell for compatibility

echo ================================
echo F1 Simulator System - Windows
echo ================================
echo.

cd /d "%~dp0\.."

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements if needed
if not exist "venv\Lib\site-packages\flask" (
    echo Installing dependencies...
    pip install -r config\requirements.txt
)

REM Create logs directory
if not exist "logs" mkdir logs

echo.
echo Starting F1 Simulator System...
echo.

REM Start Flask server in background
echo [1/3] Starting Flask Web Server (port 8080)...
start /B python src\app.py > logs\flask.log 2>&1

REM Wait for Flask to start
timeout /t 2 /nobreak > nul

REM Start UDP Receiver - Rig 1
echo [2/3] Starting UDP Receiver - Rig 1 (port 20777)...
start /B python src\receiver.py --url http://localhost:8080/data --driver "Rig 1" --port 20777 --rig 1 > logs\receiver-rig1.log 2>&1

REM Start UDP Receiver - Rig 2
echo [3/3] Starting UDP Receiver - Rig 2 (port 20778)...
start /B python src\receiver.py --url http://localhost:8080/data --driver "Rig 2" --port 20778 --rig 2 > logs\receiver-rig2.log 2>&1

echo.
echo ================================
echo System Started Successfully!
echo ================================
echo.
echo URLs:
echo   Dual Dashboard:  http://localhost:8080/dual
echo   Welcome Page:    http://localhost:8080/
echo.
echo Logs are in the logs\ directory
echo To stop: run scripts\stop_windows.bat
echo.
echo Press Ctrl+C to exit this window (services will keep running)
pause
