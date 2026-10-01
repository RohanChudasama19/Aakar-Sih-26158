$ErrorActionPreference = "Continue"

Write-Host "Stopping AAKAR Worker processes..."
Get-WmiObject Win32_Process -Filter "CommandLine LIKE '%app.worker%' OR CommandLine LIKE '%rqworker%'" | ForEach-Object {
    Write-Host "Stopping process $($_.ProcessId)"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "Stopping AAKAR API processes..."
Get-WmiObject Win32_Process -Filter "CommandLine LIKE '%uvicorn app.main:app%' OR CommandLine LIKE '%uvicorn.exe%app.main:app%'" | ForEach-Object {
    Write-Host "Stopping process $($_.ProcessId)"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "AAKAR stopped successfully." -ForegroundColor Green
