@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Prompt Atelier

echo ==================================================
echo   Prompt Atelier
echo ==================================================
echo.

call :check_python
if errorlevel 1 goto missing
call :check_node
if errorlevel 1 goto missing

start "" /b powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:4173'"

echo Website: http://127.0.0.1:4173
echo Press Ctrl+C to stop.
echo.
npm start
if errorlevel 1 goto run_failed
exit /b 0

:check_python
python "scripts\check-python.py"
if not errorlevel 1 exit /b 0
py -3 "scripts\check-python.py"
exit /b %errorlevel%

:check_node
node "scripts\check-node.js"
exit /b %errorlevel%

:missing
echo.
echo [ERROR] Python 3.10+ and Node.js 18+ are required.
echo Double-click install.bat first.
pause
exit /b 1

:run_failed
echo.
echo [ERROR] The server stopped unexpectedly. Review the message above.
pause
exit /b 1
