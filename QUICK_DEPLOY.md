# ⚡ 빠른 배포 가이드 (5분 완성)

가장 간단하게 웹에 배포하는 방법을 안내합니다.

## 🚀 **1단계: GitHub 저장소 만들기**

1. [GitHub](https://github.com) 로그인
2. **"New repository"** 클릭
3. Repository name: `brand-matching-system`
4. **"Create repository"** 클릭

## 💻 **2단계: 코드 업로드**

터미널에서 다음 명령어 실행:

```bash
# Git 초기화
git init

# 모든 파일 추가
git add .

# 첫 커밋
git commit -m "브랜드 매칭 시스템 초기 버전"

# GitHub와 연결 (본인의 username으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/brand-matching-system.git

# 업로드
git branch -M main
git push -u origin main
```

## 🌐 **3단계: Render에서 배포 (추천)**

1. [Render.com](https://render.com) 회원가입
2. **"New +"** → **"Web Service"** 클릭
3. **"Connect a repository"** → GitHub 계정 연결
4. `brand-matching-system` 저장소 선택
5. 설정:
   - **Name**: `brand-matching-system`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python brand_matching_web.py`
6. **"Create Web Service"** 클릭

## ✅ **완료!**

5-10분 후 `https://brand-matching-system-xxxx.onrender.com` 형태의 URL로 접속 가능합니다.

---

## 🔧 **대안: Railway 배포**

더 빠른 배포를 원한다면:

1. [Railway.app](https://railway.app) 회원가입
2. **"New Project"** → **"Deploy from GitHub repo"**
3. 저장소 선택 → 자동 배포 완료

---

## 📱 **접속 확인**

배포 완료 후 다음 기능들이 정상 작동하는지 확인:
- ✅ 파일 업로드
- ✅ 매칭 처리
- ✅ 결과 다운로드

문제가 있다면 `GITHUB_DEPLOYMENT_GUIDE.md`를 참조하세요.

**🎉 축하합니다! 웹 배포가 완료되었습니다!** 