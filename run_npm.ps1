Set-Location "c:\Users\wadje\Downloads\PIH-2026_SYNTAX_GLITCH-main\aerolung-dashboard"
$env:PATH = "C:\Program Files\nodejs;$env:PATH"
& "C:\Program Files\nodejs\npm.cmd" install *> install_log.txt
Write-Host "npm install exit code: $LASTEXITCODE"
