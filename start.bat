@echo off
setlocal EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul

echo ==================================================
echo   Prompt Atelier 실행
echo ==================================================
echo.

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 goto :missing

node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 18 ? 0 : 1)" >nul 2>nul
if errorlevel 1 goto :missing

rem 서버가 켜진 뒤 기본 브라우저를 자동으로 엽니다.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:4173'"

echo 웹사이트 주소: http://127.0.0.1:4173
echo 종료하려면 이 창에서 Ctrl+C를 누르세요.
echo.
npm start
if errorlevel 1 goto :run_failed
exit /b 0

:missing
echo [오류] Python 3.10 이상 또는 Node.js 18 이상이 필요합니다.
echo 먼저 install.bat을 더블클릭해 주세요.
echo.
pause
exit /b 1

:run_failed
echo.
echo [오류] 서버가 정상적으로 실행되지 않았습니다.
echo 위에 표시된 오류 내용을 확인해 주세요.
pause
exit /b 1
