# PowerShell script to run frontend dev server
Set-Location "c:\Users\wadje\Downloads\PIH-2026_SYNTAX_GLITCH-main\aerolung-dashboard"
$env:PATH = "C:\Program Files\nodejs;$env:PATH"
Write-Host "Starting AeroLung Dashboard on http://localhost:5173" -ForegroundColor Green
& "C:\Program Files\nodejs\npm.cmd" run dev
