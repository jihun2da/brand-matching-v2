# 🚀 배포 가이드

## GitHub에 업로드하기

### 1단계: GitHub 저장소 생성
1. [GitHub](https://github.com)에 로그인
2. 우측 상단 "+" 버튼 클릭 → "New repository" 선택
3. 저장소 이름: `brand-matching-v2` (또는 원하는 이름)
4. Public 선택 (Streamlit Cloud 무료 배포용)
5. "Create repository" 클릭

### 2단계: 로컬에서 GitHub에 푸시
```bash
# GitHub 저장소 URL을 원격으로 추가 (YOUR_USERNAME을 본인 GitHub 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/brand-matching-v2.git

# 코드를 GitHub에 푸시
git push -u origin main
```

## Streamlit Cloud에 배포하기

### 1단계: Streamlit Cloud 접속
1. [Streamlit Cloud](https://streamlit.io/cloud)에 접속
2. GitHub 계정으로 로그인

### 2단계: 앱 배포
1. "New app" 버튼 클릭
2. Repository: 방금 생성한 저장소 선택
3. Branch: `main`
4. Main file path: `streamlit_app.py`
5. "Deploy!" 클릭

### 3단계: 배포 확인
- 몇 분 후 앱이 자동으로 배포됩니다
- 제공된 URL을 통해 접속 가능합니다

## 주요 파일 설명

### Streamlit 관련 파일
- `streamlit_app.py`: 메인 Streamlit 애플리케이션
- `requirements.txt`: Python 패키지 의존성
- `packages.txt`: 시스템 패키지 의존성 (OpenCV용)
- `.streamlit/config.toml`: Streamlit 설정

### Flask 관련 파일 (참고용)
- `app.py`: Flask 애플리케이션 (로컬 테스트용)
- `templates/index.html`: Flask 웹 인터페이스
- `Procfile`: Heroku 배포용
- `vercel.json`: Vercel 배포용

## 문제 해결

### OpenCV 관련 오류
- `opencv-python-headless` 사용 (GUI 없는 버전)
- `packages.txt`에 시스템 라이브러리 추가

### 메모리 오류
- 이미지 크기 제한
- 처리할 이미지 수 제한

### 배포 실패
1. requirements.txt 확인
2. packages.txt 확인
3. 로그 확인 후 오류 수정

## 추가 기능 개발

### 새 브랜드 추가
`streamlit_app.py`의 `BRAND_DATABASE` 딕셔너리에 추가:

```python
"new_brand": {
    "name": "New Brand",
    "description": "Brand Description",
    "colors": ["#COLOR1", "#COLOR2"],
    "keywords": ["keyword1", "keyword2"]
}
```

### 알고리즘 개선
- `extract_features()` 함수 수정
- `match_brand()` 함수 수정
- 머신러닝 모델 통합

## 라이선스
MIT License 