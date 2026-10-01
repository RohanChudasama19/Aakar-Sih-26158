function Get-DirSize {
    param ([string])
    if (Test-Path ) {
         = (Get-ChildItem -Path  -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        return if () {  } else { 0 }
    }
    return 0
}

 = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
 = .Size / 1GB
 = .FreeSpace / 1GB
 =  - 

Write-Host "C: Total: 0 GB"
Write-Host "C: Used: 0 GB"
Write-Host "C: Free: 0 GB"

 = "C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon"
 = @("data", "demo", "frontend", "web", "web_legacy_rc5", "tests", "logs", "imports")
Write-Host "
PROJECT DIRECTORIES:"
foreach ( in ) {
     = Join-Path  
     = Get-DirSize 
    Write-Host " = 0 GB"
}

Write-Host "
LARGEST JOBS:"
 = Join-Path  "data"
if (Test-Path ) {
    foreach ( in Get-ChildItem -Path  -Directory) {
         = Get-DirSize .FullName
        Write-Host " = 0 GB"
    }
}

Write-Host "
20 LARGEST DIRECTORIES:"
# This can be slow, but we'll try a fast approach using powershell
Get-ChildItem -Path  -Directory -Recurse -ErrorAction SilentlyContinue | 
    Where-Object { -not (.FullName -match '\\node_modules\\') -and -not (.FullName -match '\\\.git\\') } |
    ForEach-Object {
         = (Get-ChildItem -Path .FullName -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        if ( -gt 0) {
            [PSCustomObject]@{
                Path = .FullName.Replace(, "")
                SizeGB =  / 1GB
            }
        }
    } | Sort-Object SizeGB -Descending | Select-Object -First 20 | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "
30 LARGEST FILES:"
Get-ChildItem -Path  -File -Recurse -ErrorAction SilentlyContinue | 
    Sort-Object Length -Descending | Select-Object -First 30 | 
    ForEach-Object {
        Write-Host " = 0 GB"
    }

