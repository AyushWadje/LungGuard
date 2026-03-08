@echo off
set ComSpec=C:\Windows\System32\cmd.exe
set SHELL=C:\Windows\System32\cmd.exe
cd /d "c:\Users\wadje\Downloads\PIH-2026_SYNTAX_GLITCH-main\aerolung-dashboard"
echo Starting Vite dev server... > dev_log.txt
node "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" run dev >> dev_log.txt 2>&1
