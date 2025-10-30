# Quick script to kill UDP receiver processes by port
Write-Host "Killing UDP receiver processes..." -ForegroundColor Yellow

$ports = @(20777, 20778)

foreach ($port in $ports) {
    Write-Host "Checking port $port..." -ForegroundColor Cyan

    # Find process using the port (UDP)
    $netstatOutput = netstat -ano | Select-String ":$port "

    if ($netstatOutput) {
        foreach ($line in $netstatOutput) {
            # Extract PID from the last column
            if ($line -match '\s+(\d+)\s*$') {
                $processId = $matches[1]
                try {
                    $process = Get-Process -Id $processId -ErrorAction Stop
                    Write-Host "  Found process $($process.Name) (PID: $processId) on port $port" -ForegroundColor Yellow
                    Stop-Process -Id $processId -Force -ErrorAction Stop
                    Write-Host "  Killed process $processId on port $port" -ForegroundColor Green
                } catch {
                    Write-Host "  Could not kill process $processId : $_" -ForegroundColor Red
                }
            }
        }
    } else {
        Write-Host "  No process found on port $port" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
