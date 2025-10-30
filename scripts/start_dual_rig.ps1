# F1 Dual-Rig Telemetry Dashboard - Windows Launcher
# PowerShell script to start the dual-rig Flask server with SocketIO

# Get script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "====================================" -ForegroundColor Green
Write-Host "F1 Dual-Rig Telemetry Dashboard" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Change to project root
Set-Location $ProjectRoot

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    py -m venv venv
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

# Kill any existing processes on required ports using kill_udp.ps1
if (Test-Path "kill_udp.ps1") {
    & ".\kill_udp.ps1"
} else {
    # Fallback: Kill processes on ports manually
    $ports = @(8080, 20777, 20778)
    foreach ($port in $ports) {
        $netstatOutput = netstat -ano | Select-String ":$port "
        if ($netstatOutput) {
            foreach ($line in $netstatOutput) {
                if ($line -match '\s+(\d+)\s*$') {
                    $processId = $matches[1]
                    try {
                        Stop-Process -Id $processId -Force -ErrorAction Stop
                        Write-Host "  Killed process $processId on port $port" -ForegroundColor Green
                    } catch {
                        Write-Host "  Could not kill process $processId" -ForegroundColor Red
                    }
                }
            }
        }
    }
}

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Starting Dual-Rig Dashboard..." -ForegroundColor Green
Write-Host ""

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Start Flask server with SocketIO (dual-rig app)
Write-Host "Starting Flask Web Server with SocketIO (port 8080)..." -ForegroundColor Yellow
$flask = Start-Process py -ArgumentList "src\app_dual_rig.py" -RedirectStandardOutput "logs\dual_rig_flask.log" -RedirectStandardError "logs\dual_rig_flask_error.log" -PassThru -NoNewWindow
Write-Host "  Flask PID: $($flask.Id)" -ForegroundColor Green

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "System Started Successfully!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Save PID to file for stop script
@{
    Flask = $flask.Id
} | ConvertTo-Json | Out-File -FilePath ".dual_rig_pids.json" -Encoding UTF8

Write-Host "Process ID:"
Write-Host "  Flask Server: " -NoNewline
Write-Host $flask.Id -ForegroundColor Green
Write-Host ""

Write-Host "Dashboard URL:"
Write-Host "  " -NoNewline
Write-Host "http://localhost:8080/" -ForegroundColor Cyan
Write-Host ""

Write-Host "Logs:"
Write-Host "  Flask:        " -NoNewline
Write-Host "Get-Content logs\dual_rig_flask.log -Wait" -ForegroundColor Yellow
Write-Host "  Flask Errors: " -NoNewline
Write-Host "Get-Content logs\dual_rig_flask_error.log -Wait" -ForegroundColor Yellow
Write-Host ""

Write-Host "The dashboard listens for F1 telemetry on:"
Write-Host "  Rig A (Red):  UDP port 20777" -ForegroundColor Red
Write-Host "  Rig B (Blue): UDP port 20778" -ForegroundColor Cyan
Write-Host ""

Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Keep script running and monitor the process
Write-Host "Monitoring Flask server... (Press Ctrl+C to exit)" -ForegroundColor Cyan
try {
    while ($true) {
        Start-Sleep -Seconds 5

        # Check if Flask is still running
        $flaskRunning = Get-Process -Id $flask.Id -ErrorAction SilentlyContinue

        if (-not $flaskRunning) {
            Write-Host ""
            Write-Host "WARNING: Flask server has stopped!" -ForegroundColor Red
            Write-Host "Check logs for errors: Get-Content logs\dual_rig_flask_error.log" -ForegroundColor Yellow
            break
        }
    }
} catch {
    Write-Host ""
    Write-Host "Stopping Flask server..." -ForegroundColor Yellow
    Stop-Process -Id $flask.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped." -ForegroundColor Green
}
