@echo off
setlocal EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul

echo ==================================================
echo   Prompt Atelier 환경 설치
echo ==================================================
echo.

set "NEED_PYTHON=0"
set "NEED_NODE=0"

call :check_python
if errorlevel 1 (
  set "NEED_PYTHON=1"
  echo [필요] Python 3.10 이상이 설치되어 있지 않습니다.
) else (
  echo [완료] Python 3.10 이상이 설치되어 있습니다.
)

call :check_node
if errorlevel 1 (
  set "NEED_NODE=1"
  echo [필요] Node.js 18 이상이 설치되어 있지 않습니다.
) else (
  echo [완료] Node.js 18 이상이 설치되어 있습니다.
)

echo.
if "%NEED_PYTHON%%NEED_NODE%"=="00" goto :success

where winget >nul 2>nul
if errorlevel 1 goto :no_winget

if "%NEED_PYTHON%"=="1" (
  echo [설치 중] Python 3.12...
  winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
  if errorlevel 1 goto :install_failed
)

if "%NEED_NODE%"=="1" (
  echo [설치 중] Node.js LTS...
  winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
  if errorlevel 1 goto :install_failed
)

rem winget 설치 직후 현재 창에서도 새 프로그램을 찾도록 일반 설치 경로를 추가합니다.
set "PATH=%PATH%;%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%ProgramFiles%\nodejs"

echo.
echo 설치 결과를 다시 확인합니다...
call :check_python
if errorlevel 1 goto :restart_needed
call :check_node
if errorlevel 1 goto :restart_needed

goto :success

:check_python
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if not errorlevel 1 exit /b 0
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
exit /b %errorlevel%

:check_node
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 18 ? 0 : 1)" >nul 2>nul
exit /b %errorlevel%

:success
echo.
echo ==================================================
echo   준비가 완료되었습니다.
echo   이제 start.bat 을 더블클릭하세요.
echo ==================================================
pause
exit /b 0

:restart_needed
echo.
echo 설치는 완료됐지만 현재 창의 PATH가 아직 갱신되지 않았습니다.
echo 이 창을 닫고 install.bat을 한 번 더 실행해 확인해 주세요.
pause
exit /b 0

:no_winget
echo.
echo [오류] Windows 패키지 관리자 winget을 찾을 수 없습니다.
echo Microsoft Store에서 '앱 설치 관리자'를 설치한 뒤 다시 실행해 주세요.
echo https://apps.microsoft.com/detail/9NBLGGH4NNS1
pause
exit /b 1

:install_failed
echo.
echo [오류] 설치가 완료되지 않았습니다. 위 winget 오류 내용을 확인해 주세요.
pause
exit /b 1
