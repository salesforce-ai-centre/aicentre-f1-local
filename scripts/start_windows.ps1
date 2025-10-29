# F1 Simulator System - Windows Launcher
# PowerShell script to start Flask server and both UDP receivers

# Get script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "================================" -ForegroundColor Green
Write-Host "F1 Simulator System - Windows" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Change to project root
Set-Location $ProjectRoot

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install requirements if needed
if (-not (Test-Path "venv\Lib\site-packages\flask")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r config\requirements.txt
}

Write-Host "Checking for existing processes..." -ForegroundColor Yellow

# Kill any existing processes on required ports
$ports = @(8080, 20777, 20778)
foreach ($port in $ports) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($connections) {
            foreach ($conn in $connections) {
                $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "Killing process $($process.Name) (PID: $($process.Id)) on port $port" -ForegroundColor Yellow
                    Stop-Process -Id $process.Id -Force
                }
            }
        }
    } catch {
        # Port not in use, continue
    }
}

Start-Sleep -Seconds 1

Write-Host ""
Write-Host "Starting F1 Simulator System..." -ForegroundColor Green
Write-Host ""

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Start Flask server
Write-Host "[1/3] Starting Flask Web Server (port 8080)..." -ForegroundColor Yellow
$flask = Start-Process python -ArgumentList "src\app.py" -RedirectStandardOutput "logs\flask.log" -RedirectStandardError "logs\flask_error.log" -PassThru -WindowStyle Hidden
Write-Host "       Flask PID: $($flask.Id)" -ForegroundColor Green

# Wait a moment for Flask to start
Start-Sleep -Seconds 2

# Start UDP Receiver - Rig 1
Write-Host "[2/3] Starting UDP Receiver - Rig 1 (port 20777)..." -ForegroundColor Yellow
$rig1 = Start-Process python -ArgumentList "src\receiver.py --url http://localhost:8080/data --driver `"Rig 1`" --port 20777 --rig 1" -RedirectStandardOutput "logs\receiver-rig1.log" -RedirectStandardError "logs\receiver-rig1_error.log" -PassThru -WindowStyle Hidden
Write-Host "       Rig 1 Receiver PID: $($rig1.Id)" -ForegroundColor Green

# Start UDP Receiver - Rig 2
Write-Host "[3/3] Starting UDP Receiver - Rig 2 (port 20778)..." -ForegroundColor Yellow
$rig2 = Start-Process python -ArgumentList "src\receiver.py --url http://localhost:8080/data --driver `"Rig 2`" --port 20778 --rig 2" -RedirectStandardOutput "logs\receiver-rig2.log" -RedirectStandardError "logs\receiver-rig2_error.log" -PassThru -WindowStyle Hidden
Write-Host "       Rig 2 Receiver PID: $($rig2.Id)" -ForegroundColor Green

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "System Started Successfully!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Save PIDs to file for stop script
@{
    Flask = $flask.Id
    Rig1 = $rig1.Id
    Rig2 = $rig2.Id
} | ConvertTo-Json | Out-File -FilePath ".pids.json" -Encoding UTF8

Write-Host "Process IDs:"
Write-Host "  Flask Server:    " -NoNewline
Write-Host $flask.Id -ForegroundColor Green
Write-Host "  Rig 1 Receiver:  " -NoNewline
Write-Host $rig1.Id -ForegroundColor Green
Write-Host "  Rig 2 Receiver:  " -NoNewline
Write-Host $rig2.Id -ForegroundColor Green
Write-Host ""

Write-Host "URLs:"
Write-Host "  Welcome Page:    " -NoNewline
Write-Host "http://localhost:8080/" -ForegroundColor Green
Write-Host "  Sim 1 Attract:   " -NoNewline
Write-Host "http://localhost:8080/attract?rig=1" -ForegroundColor Green
Write-Host "  Sim 2 Attract:   " -NoNewline
Write-Host "http://localhost:8080/attract?rig=2" -ForegroundColor Green
Write-Host "  Dual Dashboard:  " -NoNewline
Write-Host "http://localhost:8080/dual" -ForegroundColor Green
Write-Host ""

Write-Host "Logs:"
Write-Host "  Flask:           " -NoNewline
Write-Host "Get-Content logs\flask.log -Wait" -ForegroundColor Yellow
Write-Host "  Rig 1 Receiver:  " -NoNewline
Write-Host "Get-Content logs\receiver-rig1.log -Wait" -ForegroundColor Yellow
Write-Host "  Rig 2 Receiver:  " -NoNewline
Write-Host "Get-Content logs\receiver-rig2.log -Wait" -ForegroundColor Yellow
Write-Host ""

Write-Host "Press Ctrl+C to stop (or run .\scripts\stop_windows.ps1)" -ForegroundColor Yellow
Write-Host ""

# Keep script running
Write-Host "Monitoring processes... (Press Ctrl+C to exit)" -ForegroundColor Cyan
try {
    while ($true) {
        Start-Sleep -Seconds 5

        # Check if processes are still running
        $flaskRunning = Get-Process -Id $flask.Id -ErrorAction SilentlyContinue
        $rig1Running = Get-Process -Id $rig1.Id -ErrorAction SilentlyContinue
        $rig2Running = Get-Process -Id $rig2.Id -ErrorAction SilentlyContinue

        if (-not $flaskRunning) {
            Write-Host "WARNING: Flask server has stopped!" -ForegroundColor Red
            break
        }
        if (-not $rig1Running) {
            Write-Host "WARNING: Rig 1 receiver has stopped!" -ForegroundColor Red
        }
        if (-not $rig2Running) {
            Write-Host "WARNING: Rig 2 receiver has stopped!" -ForegroundColor Red
        }
    }
} catch {
    Write-Host ""
    Write-Host "Stopping all services..." -ForegroundColor Yellow
    & "$ScriptDir\stop_windows.ps1"
}
