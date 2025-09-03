#!/bin/bash

echo "==================================="
echo "브랜드 매칭 시스템 시작"
echo "==================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3이 설치되지 않았습니다."
    echo "Python 3.8 이상을 설치하고 다시 시도하십시오."
    exit 1
fi

# Check if required packages are installed
echo "[1/3] 필수 패키지 확인 중..."
python3 -c "import flask, pandas, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[INFO] 필수 패키지를 설치합니다..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: 패키지 설치 실패"
        exit 1
    fi
else
    echo "[OK] 필수 패키지 확인 완료"
fi

# Check if directories exist
echo "[2/3] 디렉토리 구조 확인 중..."
mkdir -p uploads results
if [ ! -d "templates" ]; then
    echo "ERROR: templates 디렉토리가 없습니다."
    exit 1
fi
echo "[OK] 디렉토리 구조 확인 완료"

# Get IP address for network access
echo "[3/3] 네트워크 정보 확인 중..."
if command -v ifconfig &> /dev/null; then
    IP=$(ifconfig | grep -E "inet.*broadcast" | awk '{print $2}' | head -1)
elif command -v ip &> /dev/null; then
    IP=$(ip route get 1 | awk '{print $7; exit}')
else
    IP="[IP 확인 불가]"
fi

echo "[INFO] 로컬 접속: http://localhost:5002"
echo "[INFO] 네트워크 접속: http://${IP}:5002"

echo
echo "==================================="
echo "웹 애플리케이션을 시작합니다..."
echo "종료하려면 Ctrl+C를 누르세요"
echo "==================================="
echo

# Start the web application
python3 brand_matching_web.py

echo
echo "애플리케이션이 종료되었습니다." 