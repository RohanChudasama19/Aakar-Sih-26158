$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

$Python = ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $Python)) {
    Write-Host "Error: Virtual environment not found at .venv" -ForegroundColor Red
    exit 1
}

$env:REDIS_URL = "redis://127.0.0.1:6379/0"

Write-Host "Checking Redis/Memurai service on port 6379..."
$RedisUp = $false
try {
    $tcpConnection = Test-NetConnection -ComputerName "127.0.0.1" -Port 6379 -InformationLevel Quiet
    $RedisUp = $tcpConnection
} catch {
    $RedisUp = $false
}

if (-Not $RedisUp) {
    Write-Host "Redis/Memurai not listening on 6379. Attempting to start Memurai service..." -ForegroundColor Yellow
    try {
        Start-Service -Name "Memurai" -ErrorAction Stop
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "Failed to start Memurai service. Ensure Memurai is installed and you are running as Administrator if the service is stopped." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Verifying Redis with memurai-cli ping..."
$PingResult = memurai-cli ping 2>$null
if ($PingResult -notmatch "PONG") {
    Write-Host "Error: Redis/Memurai did not respond with PONG. Got: $PingResult" -ForegroundColor Red
    exit 1
}
Write-Host "Redis: OK" -ForegroundColor Green

Write-Host "Starting Worker..."
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$ProjectRoot'; `$env:REDIS_URL='redis://127.0.0.1:6379/0'; & '.\.venv\Scripts\python.exe' -m app.worker`"" -WindowStyle Normal -PassThru | Out-Null

Write-Host "Starting API..."
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$ProjectRoot'; `$env:REDIS_URL='redis://127.0.0.1:6379/0'; & '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --host 127.0.0.1 --port 8000`"" -WindowStyle Normal -PassThru | Out-Null

Write-Host "Waiting for API to respond on port 8000..."
$timeout = 30
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$apiUp = $false
while ($stopwatch.Elapsed.TotalSeconds -lt $timeout) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000" -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $apiUp = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-Not $apiUp) {
    Write-Host "Error: API did not respond within $timeout seconds." -ForegroundColor Red
    exit 1
}

Write-Host "Opening UI in default browser..."
Start-Process "http://127.0.0.1:8000"

Write-Host "`n================================================"
Write-Host "AERORECON READY" -ForegroundColor Cyan
Write-Host "Redis: OK"
Write-Host "Worker: STARTED"
Write-Host "API: STARTED"
Write-Host "UI: http://127.0.0.1:8000"
Write-Host "================================================`n"
