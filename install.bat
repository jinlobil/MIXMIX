@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Prompt Atelier - Environment Setup

echo ==================================================
echo   Prompt Atelier Environment Setup
echo ==================================================
echo.

set "NEED_PYTHON=0"
set "NEED_NODE=0"

call :check_python
if errorlevel 1 (
  set "NEED_PYTHON=1"
  echo [MISSING] Python 3.10 or newer
) else (
  echo [OK] Python 3.10 or newer
)

call :check_node
if errorlevel 1 (
  set "NEED_NODE=1"
  echo [MISSING] Node.js 18 or newer
) else (
  echo [OK] Node.js 18 or newer
)

echo.
if "%NEED_PYTHON%%NEED_NODE%"=="00" goto success

where winget >nul 2>nul
if errorlevel 1 goto no_winget

if "%NEED_PYTHON%"=="1" (
  echo [INSTALLING] Python 3.12...
  winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
  if errorlevel 1 goto install_failed
)

if "%NEED_NODE%"=="1" (
  echo [INSTALLING] Node.js LTS...
  winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
  if errorlevel 1 goto install_failed
)

set "PATH=%PATH%;%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%ProgramFiles%\nodejs"

echo.
echo Checking installed versions again...
call :check_python
if errorlevel 1 goto restart_needed
call :check_node
if errorlevel 1 goto restart_needed
goto success

:check_python
python "scripts\check-python.py" >nul 2>nul
if not errorlevel 1 exit /b 0
py -3 "scripts\check-python.py" >nul 2>nul
exit /b %errorlevel%

:check_node
node "scripts\check-node.js" >nul 2>nul
exit /b %errorlevel%

:success
echo.
echo ==================================================
echo   Setup complete. Double-click start.bat now.
echo ==================================================
pause
exit /b 0

:restart_needed
echo.
echo Installation finished, but Windows has not refreshed PATH yet.
echo Close this window and run install.bat one more time.
pause
exit /b 0

:no_winget
echo.
echo [ERROR] winget was not found.
echo Install "App Installer" from Microsoft Store, then retry:
echo https://apps.microsoft.com/detail/9NBLGGH4NNS1
pause
exit /b 1

:install_failed
echo.
echo [ERROR] Installation failed. Review the winget message above.
pause
exit /b 1
