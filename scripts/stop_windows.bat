@echo off
REM F1 Simulator System - Windows Stop Script

echo ================================
echo Stopping F1 Simulator System
echo ================================
echo.

REM Kill Python processes using ports
echo Stopping processes on ports 8080, 20777, 20778...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":20777" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":20778" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul

echo.
echo ================================
echo All services stopped
echo ================================
