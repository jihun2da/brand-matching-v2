# 🚀 브랜드 매칭 시스템 배포 가이드

이 문서는 브랜드 매칭 웹 애플리케이션을 여러 사용자가 접근할 수 있도록 배포하는 방법을 설명합니다.

## 📋 시스템 요구사항

- **Python**: 3.8 이상
- **운영체제**: Windows, macOS, Linux
- **메모리**: 최소 2GB RAM
- **디스크**: 최소 1GB 여유 공간
- **네트워크**: 인터넷 연결 (Google Sheets API 접근용)

## 🔧 로컬 배포 (Local Deployment)

### 1. 필수 패키지 설치

```bash
# 1. 프로젝트 디렉토리로 이동
cd 매칭2

# 2. 필요한 패키지 설치
pip install -r requirements.txt

# 3. 설치 확인
python -c "import flask, pandas, requests; print('모든 패키지 설치 완료')"
```

### 2. 애플리케이션 실행

```bash
# 웹 애플리케이션 시작
python brand_matching_web.py
```

### 3. 접속 확인

- **로컬 접속**: http://localhost:5002
- **네트워크 내 다른 컴퓨터에서 접속**: http://[컴퓨터IP]:5002

### 4. IP 주소 확인 방법

**Windows:**
```cmd
ipconfig
```

**macOS/Linux:**
```bash
ifconfig
```

## 🌐 네트워크 배포 (Network Deployment)

### 방법 1: 로컬 네트워크 공유

1. **방화벽 설정**:
   - Windows Defender 방화벽에서 포트 5002 허용
   - 제어판 → 시스템 및 보안 → Windows Defender 방화벽 → 고급 설정
   - 인바운드 규칙 → 새 규칙 → 포트 → TCP → 5002 → 허용

2. **애플리케이션 설정 변경**:
```python
# brand_matching_web.py 파일의 마지막 줄 수정
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)
```

3. **접속 방법**:
   - 같은 네트워크의 다른 컴퓨터에서 http://[서버컴퓨터IP]:5002 로 접속

### 방법 2: 클라우드 배포

#### A. Heroku 배포

1. **Heroku CLI 설치**: https://devcenter.heroku.com/articles/heroku-cli

2. **배포 파일 준비**:
```bash
# Procfile 생성
echo "web: python brand_matching_web.py" > Procfile

# runtime.txt 생성 (선택사항)
echo "python-3.9.16" > runtime.txt
```

3. **Heroku 앱 생성 및 배포**:
```bash
heroku login
heroku create 브랜드매칭앱이름
git init
git add .
git commit -m "Initial commit"
heroku git:remote -a 브랜드매칭앱이름
git push heroku main
```

#### B. PythonAnywhere 배포

1. **PythonAnywhere 계정 생성**: https://www.pythonanywhere.com

2. **파일 업로드**: 모든 프로젝트 파일을 업로드

3. **웹 앱 설정**:
   - Dashboard → Web → Add a new web app
   - Framework: Flask
   - Python version: 3.9
   - Source code: 업로드한 파일 경로 지정

#### C. AWS EC2 배포

1. **EC2 인스턴스 생성**:
   - Ubuntu 20.04 LTS 선택
   - t2.micro (프리 티어) 사용 가능

2. **서버 설정**:
```bash
# 패키지 업데이트
sudo apt update && sudo apt upgrade -y

# Python 및 pip 설치
sudo apt install python3 python3-pip -y

# 프로젝트 파일 업로드 (SCP 또는 Git 사용)
git clone [저장소URL]
cd 매칭2

# 의존성 설치
pip3 install -r requirements.txt

# 백그라운드 실행
nohup python3 brand_matching_web.py &
```

## 🔐 보안 설정

### 1. 기본 보안 조치

```python
# brand_matching_web.py에 추가
import os
from werkzeug.security import generate_password_hash

# 세션 보안 키 설정
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# 파일 업로드 크기 제한
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# 허용 파일 확장자
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
```

### 2. 접근 제한 (선택사항)

```python
# 간단한 인증 추가
@app.before_request
def require_auth():
    # 특정 IP만 허용
    allowed_ips = ['192.168.1.0/24']  # 로컬 네트워크만
    
    # 또는 간단한 패스워드 인증
    if 'authenticated' not in session:
        return render_template('login.html')
```

## 📊 모니터링 및 로그

### 1. 로그 설정

```python
# brand_matching_web.py에 추가
import logging
from logging.handlers import RotatingFileHandler

# 로그 설정
if not app.debug:
    file_handler = RotatingFileHandler('brand_matching.log', 
                                       maxBytes=10240000, 
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('브랜드 매칭 시스템 시작')
```

### 2. 성능 모니터링

```python
# 처리 시간 추적
import time
from functools import wraps

def measure_time(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        app.logger.info(f'{f.__name__} 실행 시간: {end_time - start_time:.2f}초')
        return result
    return decorated_function
```

## 🔄 백업 및 복구

### 1. 자동 백업 설정

```python
# backup.py 파일 생성
import os
import shutil
from datetime import datetime

def backup_system():
    """시스템 백업"""
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 중요 파일들 백업
    important_files = [
        'brand_matching_system.py',
        'brand_sheets_api.py', 
        'file_processor.py',
        'requirements.txt',
        '상품명 바꾸기 키워드.xlsx'
    ]
    
    for file in important_files:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
    
    print(f"백업 완료: {backup_dir}")

if __name__ == "__main__":
    backup_system()
```

### 2. 정기 백업 스케줄링

**Windows (작업 스케줄러):**
```cmd
schtasks /create /tn "브랜드매칭백업" /tr "python backup.py" /sc daily /st 02:00
```

**Linux/macOS (crontab):**
```bash
# crontab -e
0 2 * * * /usr/bin/python3 /path/to/backup.py
```

## 🛠️ 문제 해결

### 자주 발생하는 문제

1. **포트 충돌**:
   ```bash
   # 포트 사용 확인
   netstat -an | findstr :5002
   
   # 다른 포트 사용
   python brand_matching_web.py --port 5003
   ```

2. **메모리 부족**:
   - 대용량 파일 처리 시 청크 단위로 처리
   - 가비지 컬렉션 강제 실행: `gc.collect()`

3. **Google Sheets API 오류**:
   - 네트워크 연결 확인
   - API 호출 제한 확인 (1분당 100회)

### 로그 확인

```bash
# 실시간 로그 모니터링
tail -f brand_matching.log

# 오류 로그만 확인
grep "ERROR" brand_matching.log
```

## 📞 지원 및 문의

- **시스템 관리자**: [관리자 연락처]
- **기술 지원**: [기술지원 연락처]
- **사용자 매뉴얼**: README.md 참조

## 🔄 업데이트 가이드

1. **시스템 중단**:
   ```bash
   # 실행 중인 프로세스 확인
   ps aux | grep brand_matching_web.py
   
   # 프로세스 종료
   kill [PID]
   ```

2. **파일 업데이트**: 새 버전 파일로 교체

3. **재시작**:
   ```bash
   python brand_matching_web.py
   ```

---

## ⚠️ 중요 참고사항

1. **데이터 보안**: 업로드된 파일에는 개인정보가 포함될 수 있으므로 적절한 보안 조치 필요
2. **성능**: 동시 사용자 10명 이하 권장 (단일 서버 기준)
3. **백업**: 정기적인 시스템 백업 필수
4. **모니터링**: 시스템 리소스 및 로그 정기 확인

배포 전 테스트 환경에서 충분한 검증을 거친 후 운영환경에 적용하세요. 