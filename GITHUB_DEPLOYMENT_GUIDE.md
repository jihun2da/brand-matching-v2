# 🌐 GitHub를 통한 웹 배포 가이드

브랜드 매칭 시스템을 GitHub를 통해 웹상에 무료로 배포하는 방법을 안내합니다.

## 📋 **배포 전 준비사항**

### 1. GitHub 저장소 생성

```bash
# 1. 로컬에서 Git 초기화
git init

# 2. 모든 파일 추가
git add .

# 3. 첫 번째 커밋
git commit -m "Initial commit: Brand Matching System"

# 4. GitHub 저장소와 연결 (GitHub에서 저장소 생성 후)
git remote add origin https://github.com/사용자명/brand-matching-system.git

# 5. 메인 브랜치로 푸시
git branch -M main
git push -u origin main
```

### 2. 필수 파일 확인

다음 파일들이 프로젝트에 포함되어 있는지 확인하세요:
- ✅ `requirements.txt` - Python 패키지 의존성
- ✅ `Procfile` - Heroku 배포용
- ✅ `render.yaml` - Render 배포용
- ✅ `railway.toml` - Railway 배포용
- ✅ `.github/workflows/deploy.yml` - GitHub Actions

## 🚀 **배포 방법 선택**

### **방법 1: Render (추천 - 가장 쉬움)**

**장점**: 무료, GitHub 자동 연동, 간단한 설정

**단계**:
1. [Render](https://render.com) 회원가입
2. "New +" → "Web Service" 선택
3. GitHub 저장소 연결
4. 설정값:
   - **Name**: `brand-matching-system`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python brand_matching_web.py`
5. "Create Web Service" 클릭
6. 자동 배포 완료 (약 5-10분 소요)

**결과**: `https://brand-matching-system-xxxx.onrender.com` 형태의 URL 제공

---

### **방법 2: Railway**

**장점**: 빠른 배포, 좋은 성능, GitHub 자동 연동

**단계**:
1. [Railway](https://railway.app) 회원가입
2. "New Project" → "Deploy from GitHub repo" 선택
3. GitHub 저장소 선택
4. 자동 배포 시작
5. 환경변수 설정 (필요시):
   - `FLASK_ENV`: `production`

**결과**: `https://your-app-name.up.railway.app` 형태의 URL 제공

---

### **방법 3: Heroku**

**장점**: 안정적, 많은 기능

**단계**:
1. [Heroku](https://heroku.com) 회원가입
2. Heroku CLI 설치
3. 터미널에서 배포:
```bash
# Heroku 로그인
heroku login

# 앱 생성
heroku create brand-matching-system

# GitHub 저장소 연결
heroku git:remote -a brand-matching-system

# 배포
git push heroku main

# 앱 열기
heroku open
```

**결과**: `https://brand-matching-system.herokuapp.com` 형태의 URL 제공

---

### **방법 4: Vercel (서버리스)**

**장점**: CDN, 빠른 응답속도

**단계**:
1. [Vercel](https://vercel.com) 회원가입
2. GitHub 저장소 import
3. Framework Preset: `Other` 선택
4. Build Command: `pip install -r requirements.txt`
5. Output Directory: 비워둠
6. Install Command: `pip install -r requirements.txt`

---

## ⚙️ **환경변수 설정**

각 플랫폼에서 다음 환경변수를 설정하세요:

| 변수명 | 값 | 설명 |
|--------|----|----- |
| `FLASK_ENV` | `production` | 프로덕션 모드 |
| `PORT` | (자동설정) | 포트 번호 |

## 🔄 **자동 배포 설정 (GitHub Actions)**

`.github/workflows/deploy.yml` 파일이 자동 배포를 처리합니다:

- **main 브랜치에 push시 자동 배포**
- **테스트 실행 후 배포**
- **실패시 알림**

### Render 자동 배포 설정:
1. Render 대시보드에서 Deploy Hook URL 복사
2. GitHub 저장소 → Settings → Secrets and variables → Actions
3. New repository secret:
   - Name: `RENDER_DEPLOY_HOOK`
   - Value: 복사한 URL

## 🔧 **배포 후 설정**

### 1. 도메인 설정 (선택사항)
- Render: Settings → Custom Domains
- Railway: Settings → Domains  
- Heroku: Settings → Domains

### 2. SSL 인증서
- 모든 플랫폼에서 자동으로 Let's Encrypt SSL 제공

### 3. 모니터링
```bash
# 로그 확인 (Heroku 예시)
heroku logs --tail -a brand-matching-system
```

## 📊 **성능 최적화**

### 1. Gunicorn 사용 (프로덕션 권장)

`requirements.txt`에 추가:
```txt
gunicorn==21.2.0
```

`Procfile` 수정:
```
web: gunicorn -w 2 -b 0.0.0.0:$PORT brand_matching_web:app
```

### 2. 캐싱 설정
```python
# brand_matching_web.py에 추가
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=300)  # 5분 캐싱
def get_brand_data():
    return brand_sheets_api.read_brand_matching_data()
```

## 🛠️ **문제 해결**

### 자주 발생하는 문제:

1. **모듈 import 오류**:
   ```bash
   # requirements.txt 업데이트
   pip freeze > requirements.txt
   git add requirements.txt
   git commit -m "Update requirements"
   git push
   ```

2. **포트 오류**:
   - 환경변수 `PORT` 확인
   - `app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5002)))`

3. **타임아웃 오류**:
   - Google Sheets API 호출 최적화
   - 캐싱 구현

4. **메모리 부족**:
   - 대용량 파일 처리 로직 최적화
   - 청크 단위 처리 구현

## 📱 **모바일 최적화**

이미 구현된 반응형 디자인으로 모바일에서도 잘 작동합니다.

## 🔒 **보안 설정**

### 1. 환경변수로 민감정보 관리
```python
import os

# 설정
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
```

### 2. CORS 설정 (필요시)
```python
from flask_cors import CORS
CORS(app, origins=['https://yourdomain.com'])
```

## 📈 **사용량 모니터링**

### 무료 티어 제한:
- **Render**: 750시간/월, 100GB 대역폭
- **Railway**: 5$ 크레딧/월
- **Heroku**: 550-1000 시간/월
- **Vercel**: 100GB 대역폭, 함수 실행시간 제한

## 🔄 **업데이트 배포**

```bash
# 코드 수정 후
git add .
git commit -m "Update: 새로운 기능 추가"
git push origin main

# 자동 배포됨 (약 2-5분 소요)
```

## 📞 **지원 및 문의**

배포 중 문제가 발생하면:
1. 각 플랫폼의 로그 확인
2. GitHub Issues 활용
3. 플랫폼별 문서 참조

---

## 🎉 **배포 완료 확인**

배포가 성공하면 다음을 확인하세요:
1. ✅ 웹사이트 접속 가능
2. ✅ 파일 업로드 기능 동작
3. ✅ 매칭 프로세스 정상 작동
4. ✅ 결과 다운로드 가능

**축하합니다! 🎊 브랜드 매칭 시스템이 성공적으로 배포되었습니다.**

이제 전 세계 어디서나 인터넷을 통해 시스템을 사용할 수 있습니다! 