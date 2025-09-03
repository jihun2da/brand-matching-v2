# 🔗 브랜드 매칭 시스템

Sheet1 형식의 엑셀 파일을 업로드하여 브랜드매칭시트와 자동 매칭을 수행하는 웹 애플리케이션입니다.

## ✨ 주요 기능

- 📁 **다중 파일 업로드**: 여러 엑셀 파일을 동시에 업로드 가능
- 🔄 **Sheet1 → Sheet2 변환**: 업로드된 파일을 Sheet2 형식으로 자동 변환
- 🎯 **브랜드 매칭**: 브랜드, 상품명, 사이즈 기반 정확한 매칭
- 📊 **실시간 통계**: 매칭 성공률과 처리 현황을 실시간으로 확인
- 📥 **결과 다운로드**: 매칭 완료된 데이터를 Excel 파일로 다운로드

## 🌐 **웹 배포 (추천)**

**5분만에 웹에 배포하기**: [`QUICK_DEPLOY.md`](QUICK_DEPLOY.md) 참조  
**자세한 배포 가이드**: [`GITHUB_DEPLOYMENT_GUIDE.md`](GITHUB_DEPLOYMENT_GUIDE.md) 참조

### 지원하는 플랫폼:
- 🎯 **Render** (추천 - 무료, 쉬움)
- 🚄 **Railway** (빠름, 좋은 성능)  
- 🏢 **Heroku** (안정적)
- ⚡ **Vercel** (서버리스)

---

## 🚀 로컬 실행

### 1. 필수 조건
- Python 3.8 이상
- pip (Python 패키지 관리자)

### 2. 설치
```bash
# 의존성 패키지 설치
pip install -r requirements.txt
```

### 3. 실행
```bash
# 웹 애플리케이션 시작
python brand_matching_web.py
```

### 4. 접속
브라우저에서 다음 주소로 접속:
```
http://localhost:5002
```

## 📖 사용 방법

### 1️⃣ 파일 업로드
- **지원 형식**: `.xlsx`, `.xls` (Sheet1 형식)
- **업로드 방법**: 
  - 클릭하여 파일 선택
  - 드래그 앤 드롭으로 업로드
- **다중 업로드**: 여러 파일을 한 번에 선택 가능

### 2️⃣ 데이터 변환
- 업로드된 Sheet1 형식 파일들이 자동으로 Sheet2 형식으로 변환
- 15개 컬럼 구조로 매핑:
  - A열(순번) ~ M열(메모)
  - N열(중도매명), O열(도매가격) - 매칭 결과

### 3️⃣ 브랜드 매칭
- **매칭 기준**:
  - **브랜드**: 정확히 일치
  - **상품명**: 포함 관계 (대소문자 무시)
  - **사이즈**: `사이즈{...}` 패턴에서 추출하여 포함 관계
- **매칭 소스**: [브랜드매칭시트](https://docs.google.com/spreadsheets/d/14Pmz5-bFVPSPbfoKi5BfQWa8qVMVNDqxEQVmhT9wyuU/edit?gid=1834709463#gid=1834709463)

### 4️⃣ 결과 확인 및 다운로드
- 매칭 성공률과 통계 확인
- Sheet2 형식의 Excel 파일로 다운로드

## 🎯 매칭 로직

### 사용자 제공 코드 기반
```python
def match_row(brand, product, size):
    # 1. 브랜드 정확히 일치 확인
    if brand != row['브랜드']:
        continue
    
    # 2. 상품명 포함 관계 확인 (소문자)
    if product.lower() not in row['상품명'].lower():
        continue
    
    # 3. 사이즈 포함 관계 확인
    size_pattern = extract_size(row['옵션입력'])  # 사이즈{...} 추출
    if size.lower() not in size_pattern.lower():
        continue
    
    # 매칭 성공시 반환
    return 공급가, 중도매, 브랜드상품명
```

## 📂 파일 구조

```
매칭2/
├── brand_matching_web.py      # 메인 웹 애플리케이션
├── brand_matching_system.py   # 매칭 로직
├── brand_sheets_api.py        # 구글 시트 API 연동
├── file_processor.py          # 파일 처리
├── requirements.txt           # 패키지 의존성
├── README.md                  # 사용 설명서
├── templates/
│   └── brand_matching_index.html  # 웹 인터페이스
├── uploads/                   # 업로드된 파일 저장소
└── results/                   # 처리 결과 파일 저장소
```

## 🔧 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|-------|------|
| `/` | GET | 메인 페이지 |
| `/api/upload` | POST | 파일 업로드 |
| `/api/process` | POST | 브랜드 매칭 처리 |
| `/api/files` | GET | 업로드된 파일 목록 |
| `/api/delete-file` | POST | 개별 파일 삭제 |
| `/api/clear-files` | POST | 모든 파일 삭제 |
| `/api/download/<filename>` | GET | 결과 파일 다운로드 |
| `/api/reload-brand-data` | POST | 브랜드 데이터 새로고침 |

## 📊 Sheet2 형식

| 컬럼 | 설명 |
|------|------|
| A열 | 순번 |
| B열 | 주문번호 |
| C열 | 주문일 |
| D열 | 고객명 |
| E열 | 수령인 |
| F열 | 브랜드 |
| G열 | 상품명 |
| H열 | 사이즈 |
| I열 | 수량 |
| J열 | 옵션가 |
| K열 | 전화번호 |
| L열 | 주소 |
| M열 | 메모 |
| **N열** | **중도매명** (매칭 결과) |
| **O열** | **도매가격** (매칭 결과) |

## 🛠 기술 스택

- **백엔드**: Python, Flask
- **데이터 처리**: Pandas, OpenPyXL
- **프론트엔드**: HTML5, CSS3, JavaScript, jQuery
- **API 연동**: Requests (구글 시트)

## ⚡ 성능 최적화

- **파일 처리**: 스트리밍 방식으로 대용량 파일 지원
- **매칭 알고리즘**: 효율적인 반복문과 조건 검사
- **메모리 관리**: 청크 단위 데이터 처리
- **캐싱**: 브랜드 데이터 메모리 캐싱

## 🔒 보안 기능

- **파일 검증**: 허용된 확장자만 업로드 가능
- **안전한 파일명**: 타임스탬프 기반 파일명 생성
- **크기 제한**: 100MB 파일 크기 제한
- **경로 보안**: 안전한 경로 처리

## 🐛 문제 해결

### 일반적인 문제들

1. **매칭률이 낮은 경우**
   - 브랜드명이 정확히 일치하는지 확인
   - 사이즈 정보가 `사이즈{...}` 형식인지 확인
   - 브랜드 데이터 새로고침 시도

2. **파일 업로드 실패**
   - 파일 형식이 `.xlsx` 또는 `.xls`인지 확인
   - 파일 크기가 100MB 이하인지 확인
   - 파일이 손상되지 않았는지 확인

3. **처리 시간이 오래 걸리는 경우**
   - 파일 크기와 데이터 양에 따라 처리 시간 증가
   - 큰 파일은 여러 개로 나누어 처리 권장

## 📞 지원

문제가 발생하거나 개선 사항이 있으시면 개발팀에 문의해주세요. 