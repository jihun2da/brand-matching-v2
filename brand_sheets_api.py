#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브랜드매칭시트 API 연동 모듈
"""

import pandas as pd
import requests
import logging
from typing import Optional
from io import StringIO

logger = logging.getLogger(__name__)

class BrandSheetsAPI:
    """브랜드매칭시트 API를 사용한 데이터 읽기"""
    
    def __init__(self):
        # 브랜드매칭시트 ID
        self.brand_sheet_id = "14Pmz5-bFVPSPbfoKi5BfQWa8qVMVNDqxEQVmhT9wyuU"
        self.gid = "1834709463"  # 시트 탭 ID
        
    def read_brand_matching_data(self) -> pd.DataFrame:
        """브랜드매칭시트에서 매칭 데이터 읽기 (공개 시트)"""
        try:
            # 공개 구글시트 CSV 다운로드 URL
            csv_url = f"https://docs.google.com/spreadsheets/d/{self.brand_sheet_id}/export?format=csv&gid={self.gid}"
            
            logger.info(f"브랜드매칭시트에서 데이터 읽기 시도: {self.brand_sheet_id}")
            
            # CSV 데이터 다운로드 (인코딩 문제 해결)
            response = requests.get(csv_url, timeout=30)
            response.raise_for_status()
            
            # 인코딩 문제 해결을 위한 다중 시도
            try:
                # 방법 1: UTF-8로 디코딩
                response.encoding = 'utf-8'
                csv_content = response.text
            except:
                try:
                    # 방법 2: 바이트를 직접 UTF-8로 디코딩
                    csv_content = response.content.decode('utf-8')
                except:
                    # 방법 3: UTF-8-SIG (BOM 포함)
                    csv_content = response.content.decode('utf-8-sig')
            
            # 텍스트를 CSV로 읽기
            csv_data = StringIO(csv_content)
            df = pd.read_csv(csv_data)
            
            # 데이터 정리 및 검증
            if df.empty:
                logger.warning("브랜드매칭시트에서 빈 데이터를 읽었습니다")
                return self._get_fallback_data()
            
            # 컬럼명 확인 및 정리
            logger.info(f"읽어온 컬럼: {list(df.columns)}")
            logger.info(f"총 {len(df)} 행의 데이터를 읽었습니다")
            
            # 브랜드매칭시트 구조에 맞게 컬럼 매핑
            if len(df.columns) >= 5:  # 최소 5개 컬럼 필요 (브랜드, 상품명, 중도매, 공급가, 옵션입력)
                # 필요한 컬럼들 추출
                brand_data = pd.DataFrame()
                brand_data['브랜드'] = df.iloc[:, 0].fillna('').astype(str)  # A열: 브랜드
                brand_data['상품명'] = df.iloc[:, 1].fillna('').astype(str)  # B열: 상품명
                brand_data['중도매'] = df.iloc[:, 2].fillna('').astype(str)  # C열: 중도매
                brand_data['공급가'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)  # D열: 공급가
                brand_data['옵션입력'] = df.iloc[:, 4].fillna('').astype(str)  # E열: 옵션입력 (사이즈 정보 포함)
                
                # 빈 브랜드와 유효하지 않은 데이터 제거
                brand_data = brand_data[
                    (brand_data['브랜드'].str.strip() != '') & 
                    (brand_data['브랜드'] != 'nan') &
                    (brand_data['브랜드'] != '브랜드') &  # 헤더 제거
                    (brand_data['상품명'].str.strip() != '') &
                    (brand_data['상품명'] != '상품명')  # 헤더 제거
                ]
                
                # 중복 제거
                brand_data = brand_data.drop_duplicates(subset=['브랜드', '상품명', '옵션입력'], keep='first')
                
                logger.info(f"브랜드매칭시트에서 매칭용 데이터 준비 완료: {len(brand_data)}개 상품")
                logger.info(f"샘플 데이터: {brand_data.head(3).to_dict('records')}")
                return brand_data
            else:
                logger.warning("필요한 컬럼을 찾을 수 없습니다. 폴백 데이터를 사용합니다.")
                return self._get_fallback_data()
                
        except Exception as e:
            logger.error(f"브랜드매칭시트 읽기 실패: {e}")
            logger.info("폴백 데이터를 사용합니다")
            return self._get_fallback_data()
    
    def _get_fallback_data(self) -> pd.DataFrame:
        """브랜드매칭시트 읽기 실패 시 사용할 폴백 데이터"""
        fallback_data = pd.DataFrame({
            '브랜드': [
                '소예', '린도', '마마미', '로다제이', '바비',
                '보니토', '아르키드', '미미앤루', '니니벨로', '화이트스케치북',
                '키즈', '여름', '아동', '유아', '베이비'
            ],
            '상품명': [
                '테리헤어밴드', '세일러린넨바디수트', '클래식썸머셔츠', '코코넛슈트', '래쉬가드',
                '래쉬가드스윔세트', '슬립온', '티셔츠', '루비볼레로세트', '카고롱스커트',
                '래쉬가드', '원피스', '수영복', '티셔츠', '반바지'
            ],
            '옵션입력': [
                '사이즈{S,M,L}', '사이즈{80,90,100}', '사이즈{FREE}', '사이즈{S,M,L,XL}', '사이즈{5,7,9,11,13}',
                '사이즈{5,7,9,11,13}', '사이즈{150,160,170}', '사이즈{S,M,L}', '사이즈{90,100,110}', '사이즈{5,7,9,11,13}',
                '사이즈{5,7,9,11,13}', '사이즈{S,M,L}', '사이즈{90,100,110}', '사이즈{80,90,100}', '사이즈{S,M,L}'
            ],
            '공급가': [
                8000, 15000, 18000, 14000, 10000,
                20000, 30000, 12000, 16000, 8000,
                12000, 20000, 15000, 10000, 14000
            ],
            '중도매': [
                '소예패션', '린도키즈', '마마미브랜드', '로다제이', '바비브랜드',
                '보니토코리아', '아르키드', '미미앤루', '니니벨로', '화이트스케치북',
                '키즈패션', '여름브랜드', '아동복전문', '유아복몰', '베이비웨어'
            ]
        })
        
        logger.info(f"폴백 데이터 사용: {len(fallback_data)}개 상품")
        return fallback_data

# 전역 인스턴스
brand_sheets_api = BrandSheetsAPI() 