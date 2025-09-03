# 🚄 Railway 배포 가이드 (Render 대안)

Railway는 Render보다 더 관대한 빌드 제한을 가지고 있어 pandas 컴파일이 성공할 가능성이 높습니다.

## 🚀 **Railway 배포 단계**

### **1단계: Railway 회원가입**
1. [Railway.app](https://railway.app) 방문
2. **"Login"** → **"Login with GitHub"** 클릭
3. GitHub 계정으로 로그인

### **2단계: 프로젝트 배포**
1. **"New Project"** 클릭
2. **"Deploy from GitHub repo"** 선택
3. **`brand-matching-system`** 저장소 선택
4. **"Deploy Now"** 클릭

### **3단계: 환경 설정**
1. 배포된 프로젝트 클릭
2. **"Variables"** 탭 클릭
3. 다음 환경변수 추가:
   ```
   PORT=8000
   PYTHONUNBUFFERED=1
   ```

### **4단계: 도메인 설정**
1. **"Settings"** 탭 클릭
2. **"Domains"** 섹션에서 **"Generate Domain"** 클릭
3. 생성된 URL 복사 (예: `https://brand-matching-system-production.up.railway.app`)

## ✅ **Railway 장점**
- 🔧 **더 관대한 빌드 제한** (pandas 컴파일 성공률 높음)
- ⚡ **빠른 빌드 속도**
- 🆓 **무료 플랜** (월 $5 크레딧)
- 🔄 **자동 배포** (GitHub 푸시시 자동 업데이트)

## 🔔 **예상 결과**
```
✅ Build successful
✅ Deployment live  
✅ Available at: https://your-app.up.railway.app
```

Railway가 Render보다 pandas 설치에 더 적합합니다! 