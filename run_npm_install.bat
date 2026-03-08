@echo off
set ComSpec=C:\Windows\System32\cmd.exe
set SHELL=C:\Windows\System32\cmd.exe
cd /d "c:\Users\wadje\Downloads\PIH-2026_SYNTAX_GLITCH-main\aerolung-dashboard"
echo Starting npm install... > install_log.txt
node "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" install >> install_log.txt 2>&1
echo EXIT_CODE=%ERRORLEVEL% >> install_log.txt
echo DONE >> install_log.txt
