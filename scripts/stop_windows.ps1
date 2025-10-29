# F1 Simulator System - Windows Stop Script
# Stops Flask server and both UDP receivers

# Get script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "================================" -ForegroundColor Red
Write-Host "Stopping F1 Simulator System" -ForegroundColor Red
Write-Host "================================" -ForegroundColor Red
Write-Host ""

# Change to project root
Set-Location $ProjectRoot

# Try to read PIDs from file
$pids = @{}
if (Test-Path ".pids.json") {
    try {
        $pids = Get-Content ".pids.json" | ConvertFrom-Json
        Write-Host "Found PID file, stopping processes..." -ForegroundColor Yellow

        # Stop each process
        foreach ($name in @("Flask", "Rig1", "Rig2")) {
            $pid = $pids.$name
            if ($pid) {
                try {
                    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($process) {
                        Write-Host "Stopping $name (PID: $pid)..." -ForegroundColor Yellow
                        Stop-Process -Id $pid -Force
                        Write-Host "  ✓ Stopped" -ForegroundColor Green
                    }
                } catch {
                    Write-Host "  ! Process $pid not found" -ForegroundColor Gray
                }
            }
        }

        # Remove PID file
        Remove-Item ".pids.json" -ErrorAction SilentlyContinue

    } catch {
        Write-Host "Could not read PID file, searching for processes..." -ForegroundColor Yellow
    }
} else {
    Write-Host "No PID file found, searching for processes..." -ForegroundColor Yellow
}

# Kill by port as backup
Write-Host ""
Write-Host "Checking ports for any remaining processes..." -ForegroundColor Yellow

$ports = @(8080, 20777, 20778)
$killed = $false

foreach ($port in $ports) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($connections) {
            foreach ($conn in $connections) {
                $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "Killing process $($process.Name) (PID: $($process.Id)) on port $port" -ForegroundColor Yellow
                    Stop-Process -Id $process.Id -Force
                    $killed = $true
                }
            }
        }
    } catch {
        # Port not in use
    }
}

if (-not $killed) {
    Write-Host "  No processes found on ports 8080, 20777, 20778" -ForegroundColor Gray
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "All services stopped" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
