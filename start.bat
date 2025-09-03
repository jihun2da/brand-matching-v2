@echo off
echo ===================================
echo 브랜드 매칭 시스템 시작
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python이 설치되지 않았습니다.
    echo Python 3.8 이상을 설치하고 다시 시도하십시오.
    pause
    exit /b 1
)

REM Check if required packages are installed
echo [1/3] 필수 패키지 확인 중...
python -c "import flask, pandas, requests" >nul 2>&1
if errorlevel 1 (
    echo [INFO] 필수 패키지를 설치합니다...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: 패키지 설치 실패
        pause
        exit /b 1
    )
) else (
    echo [OK] 필수 패키지 확인 완료
)

REM Check if directories exist
echo [2/3] 디렉토리 구조 확인 중...
if not exist "uploads" mkdir uploads
if not exist "results" mkdir results
if not exist "templates" (
    echo ERROR: templates 디렉토리가 없습니다.
    pause
    exit /b 1
)
echo [OK] 디렉토리 구조 확인 완료

REM Get IP address for network access
echo [3/3] 네트워크 정보 확인 중...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do set ip=%%a
set ip=%ip: =%
echo [INFO] 로컬 접속: http://localhost:5002
echo [INFO] 네트워크 접속: http://%ip%:5002

echo.
echo ===================================
echo 웹 애플리케이션을 시작합니다...
echo 종료하려면 Ctrl+C를 누르세요
echo ===================================
echo.

REM Start the web application
python brand_matching_web.py

echo.
echo 애플리케이션이 종료되었습니다.
pause 