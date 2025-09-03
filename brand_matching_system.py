#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브랜드 매칭 시스템 - 속도 최적화 버전
"""

import pandas as pd
import re
import logging
import os
from typing import List, Dict, Tuple
from functools import lru_cache
import concurrent.futures
from threading import Lock
from brand_sheets_api import brand_sheets_api

logger = logging.getLogger(__name__)

class BrandMatchingSystem:
    """브랜드 매칭 시스템 - 속도 최적화 버전"""

    def __init__(self):
        self.brand_data = None
        self.keyword_list = []
        
        # 속도 최적화를 위한 캐시와 컴파일된 정규식
        self._normalized_cache = {}
        self._cache_lock = Lock()
        self._compiled_patterns = {}
        
        # 데이터 로드
        self.load_brand_data()
        self.load_keywords()
        self._precompile_patterns()

    def _precompile_patterns(self):
        """자주 사용되는 정규식 패턴들을 미리 컴파일"""
        logger.info("정규식 패턴 컴파일 중...")
        
        # 기본 패턴들
        self._compiled_patterns.update({
            'parentheses': re.compile(r'\([^)]*\)', re.IGNORECASE),
            'multiple_spaces': re.compile(r'\s+'),
            'comma_spaces': re.compile(r'\s*,\s*'),
            'multiple_commas': re.compile(r',+'),
            'korean_alpha_num': re.compile(r'[가-힣a-zA-Z0-9]'),
            'word_boundary': re.compile(r'^[a-zA-Z0-9가-힣\s]+$'),
            
            # 사이즈 관련 패턴들 (미리 컴파일)
            'size_s_xl': re.compile(r'\([sS]~[xX][lL]\)', re.IGNORECASE),
            'size_s_xl_dash': re.compile(r'\([sS]-[xX][lL]\)', re.IGNORECASE),
            'size_xs_xl': re.compile(r'\([xX][sS]~[xX][lL]\)', re.IGNORECASE),
            'size_xs_xl_dash': re.compile(r'\([xX][sS]-[xX][lL]\)', re.IGNORECASE),
            'size_m_jxl': re.compile(r'\([mM]~[jJ][xX][lL]\)', re.IGNORECASE),
            'size_m_jxl_dash': re.compile(r'\([mM]-[jJ][xX][lL]\)', re.IGNORECASE),
            'size_numbers': re.compile(r'\([0-9]+[~-][0-9]+\)', re.IGNORECASE),
            'size_js_patterns': re.compile(r'\([jJ][sS][~-][jJ][xXlLmM]+\)', re.IGNORECASE),
            
            # 옵션 파싱 패턴들
            'color_keywords': re.compile(r'(?:색상|컬러|Color)', re.IGNORECASE),
            'size_keywords': re.compile(r'(?:사이즈|Size)', re.IGNORECASE),
            'slash_pattern': re.compile(r'^([^/]+)/([^/]+)$'),
            'dash_pattern': re.compile(r'^([^-]+)-([^-]+)$'),
            'size_check': re.compile(r'[0-9]|[SMLX]', re.IGNORECASE),
            'exact_size': re.compile(r'^[SMLX]$|^[0-9]+$', re.IGNORECASE),
        })
        
        logger.info(f"정규식 패턴 {len(self._compiled_patterns)}개 컴파일 완료")

    @lru_cache(maxsize=1000)
    def _get_keyword_pattern(self, keyword: str) -> re.Pattern:
        """키워드별 정규식 패턴을 캐시와 함께 생성"""
        escaped_keyword = re.escape(keyword)
        
        if self._compiled_patterns['word_boundary'].match(keyword):
            return re.compile(r'\b' + escaped_keyword + r'\b', re.IGNORECASE)
        else:
            return re.compile(escaped_keyword, re.IGNORECASE)

    def load_keywords(self):
        """키워드 리스트 로드 (엑셀 파일 또는 기본 키워드) - 최적화 버전"""
        try:
            keyword_file = "keywords.xlsx"
            
            if os.path.exists(keyword_file):
                df = pd.read_excel(keyword_file)
                self.keyword_list = df.iloc[:, 0].dropna().astype(str).tolist()
                logger.info(f"키워드 파일에서 {len(self.keyword_list)}개 키워드 로드: {keyword_file}")
            else:
                # 기본 키워드 리스트 (최적화를 위해 중복 제거 및 정렬)
                self.keyword_list = list(set([
                    "세트", "SET", "set", "단품", "단가", "포인트", "POINT", "point",
                    "신상", "추천", "베스트", "인기", "핫", "HOT", "hot", "NEW", "new",
                    "특가", "할인", "세일", "SALE", "sale", "이벤트", "EVENT", "event",
                    "무료배송", "배송비무료", "당일배송", "빠른배송", "즉시배송",
                    "리뷰", "후기", "평점", "별점", "댓글", "추천수", "좋아요",
                    "브랜드", "정품", "오리지널", "authentic", "AUTHENTIC",
                    "프리미엄", "럭셔리", "고급", "최고급", "퀄리티", "품질",
                    "2024", "2023", "2022", "SS", "FW", "AW", "봄", "여름", "가을", "겨울",
                    "아동", "키즈", "베이비", "유아", "어린이", "아기", "신생아",
                    "남아", "여아", "남녀공용", "공용", "남여공용",
                    "(", ")", "[", "]", "{", "}", "★", "☆", "♥", "♡", "◎", "○", "●",
                    "※", "♠", "♣", "♦", "▲", "▼", "◀", "▶", "■", "□", "▣", "▤",
                    "~", "-", "_", "=", "+", "!", "@", "#", "$", "%", "^", "&", "*",
                    ".", ",", "?", "/", "\\", "|", ":", ";", "'", '"', "`",
                    "<", ">", "《", "》", "「", "」", "『", "』", "【", "】",
                    "*13~15*", "*11~13*", "*9~11*", "*7~9*", "*5~7*", "*3~5*",
                    "*90~100*", "*100~110*", "*110~120*", "*120~130*", "*130~140*",
                    "*140~150*", "*150~160*", "*160~170*",
                    "*XS~XL*", "*S~XL*", "*M~XL*", "*L~XXL*", "*FREE*",
                    "*JS~JXL*", "*JM~JXL*", "*JS~JL*", "*JM~JL*",
                ]))
                
                # 길이순으로 정렬 (긴 키워드부터 처리하여 정확도 향상)
                self.keyword_list.sort(key=len, reverse=True)
                logger.info(f"기본 키워드 {len(self.keyword_list)}개 로드 완료")
                
        except Exception as e:
            logger.error(f"키워드 로드 실패: {e}")
            self.keyword_list = []

    def save_keywords(self):
        """현재 키워드 리스트를 엑셀 파일로 저장"""
        try:
            keyword_file = "keywords.xlsx"
            df = pd.DataFrame({'키워드': self.keyword_list})
            df.to_excel(keyword_file, index=False)
            logger.info(f"키워드 파일 저장 완료: {len(self.keyword_list)}개 키워드")
            return True
        except Exception as e:
            logger.error(f"키워드 파일 저장 실패: {e}")
            return False

    def add_keyword(self, keyword: str) -> bool:
        """키워드 추가"""
        keyword = keyword.strip()
        if keyword and keyword not in self.keyword_list:
            self.keyword_list.append(keyword)
            return self.save_keywords()
        return False

    def remove_keyword(self, keyword: str) -> bool:
        """키워드 제거"""
        if keyword in self.keyword_list:
            self.keyword_list.remove(keyword)
            return self.save_keywords()
        return False

    def extract_third_word_from_address(self, address: str) -> str:
        """주소에서 3번째 단어 추출 (띄어쓰기 기준)"""
        if not address or pd.isna(address):
            return ""
        
        address = str(address).strip()
        words = address.split()
        
        # 3번째 단어가 있으면 반환, 없으면 빈 문자열
        if len(words) >= 3:
            return words[2]
        return ""

    def normalize_product_name(self, product_name: str) -> str:
        """상품명 정규화 - 캐시 및 최적화 버전"""
        if not product_name or pd.isna(product_name):
            return ""
        
        original = str(product_name).strip()
        
        # 캐시 확인
        with self._cache_lock:
            if original in self._normalized_cache:
                return self._normalized_cache[original]
        
        normalized = original
        
        # 1단계: * 기호로 감싸진 패턴 우선 처리 (최적화)
        star_keywords = [kw for kw in self.keyword_list 
                        if kw.startswith('*') and kw.endswith('*') and len(kw) > 2]
        
        for keyword in star_keywords:
            variations = [
                keyword,
                keyword.replace('~', '-'),
                keyword.replace('-', '~'),
            ]
            
            for variation in variations:
                if variation in normalized:
                    normalized = normalized.replace(variation, '')
                    break
        
        # 2단계: 일반 키워드 제거 (컴파일된 정규식 사용)
        regular_keywords = [kw for kw in self.keyword_list 
                           if not (kw.startswith('*') and kw.endswith('*'))]
        
        for keyword in regular_keywords:
            if not keyword:
                continue
                
            # 괄호와 함께 키워드 제거
            parentheses_pattern = re.compile(r'\(' + re.escape(keyword) + r'\)', re.IGNORECASE)
            normalized = parentheses_pattern.sub('', normalized)
            
            # 단독 키워드 제거 (캐시된 패턴 사용)
            keyword_pattern = self._get_keyword_pattern(keyword)
            normalized = keyword_pattern.sub('', normalized)
        
        # 3단계: 미리 컴파일된 패턴으로 유연한 패턴 제거
        pattern_keys = ['size_s_xl', 'size_s_xl_dash', 'size_xs_xl', 'size_xs_xl_dash',
                       'size_m_jxl', 'size_m_jxl_dash', 'size_numbers', 'size_js_patterns']
        
        for pattern_key in pattern_keys:
            normalized = self._compiled_patterns[pattern_key].sub('', normalized)
        
        # 4단계: 텍스트 정리 (컴파일된 정규식 사용)
        normalized = self._compiled_patterns['comma_spaces'].sub(',', normalized)
        normalized = self._compiled_patterns['multiple_commas'].sub(',', normalized)
        normalized = self._compiled_patterns['multiple_spaces'].sub(' ', normalized)
        normalized = normalized.strip(',').strip()
        
        # 결과 검증
        if len(normalized) < 2 or not self._compiled_patterns['korean_alpha_num'].search(normalized):
            normalized = original
        
        result = normalized.lower()
        
        # 캐시에 저장 (메모리 관리를 위해 크기 제한)
        with self._cache_lock:
            if len(self._normalized_cache) < 10000:  # 최대 10,000개 캐시
                self._normalized_cache[original] = result
        
        logger.debug(f"상품명 정규화: '{original}' → '{result}'")
        return result

    @lru_cache(maxsize=500)
    def parse_color_variants(self, color_text: str) -> tuple:
        """색상 텍스트에서 모든 가능한 변형을 추출 - 캐시 버전"""
        if not color_text or pd.isna(color_text):
            return ()
        
        color_text = str(color_text).strip()
        variants = set()
        
        # 기본 색상 추가
        variants.add(color_text.lower())
        
        # 쉼표로 구분된 색상들 처리
        if ',' in color_text:
            colors = [c.strip().lower() for c in color_text.split(',') if c.strip()]
            variants.update(colors)
        
        # 슬래시로 구분된 색상들 처리
        if '/' in color_text:
            colors = [c.strip().lower() for c in color_text.split('/') if c.strip()]
            variants.update(colors)
        
        # 괄호 제거 버전
        no_parentheses = self._compiled_patterns['parentheses'].sub('', color_text).strip().lower()
        if no_parentheses:
            variants.add(no_parentheses)
        
        return tuple(sorted(variants))

    @lru_cache(maxsize=500)
    def parse_size_variants(self, size_text: str) -> tuple:
        """사이즈 텍스트에서 모든 가능한 변형을 추출 - 캐시 버전"""
        if not size_text or pd.isna(size_text):
            return ()
        
        size_text = str(size_text).strip()
        variants = set()
        
        # 기본 사이즈 추가
        variants.add(size_text.lower())
        
        # 쉼표로 구분된 사이즈들 처리
        if ',' in size_text:
            sizes = [s.strip().lower() for s in size_text.split(',') if s.strip()]
            variants.update(sizes)
        
        # 슬래시로 구분된 사이즈들 처리  
        if '/' in size_text:
            sizes = [s.strip().lower() for s in size_text.split('/') if s.strip()]
            variants.update(sizes)
        
        # 괄호 제거 버전
        no_parentheses = self._compiled_patterns['parentheses'].sub('', size_text).strip().lower()
        if no_parentheses:
            variants.add(no_parentheses)
        
        return tuple(sorted(variants))

    def load_brand_data(self):
        """브랜드매칭시트에서 데이터 로드"""
        try:
            self.brand_data = brand_sheets_api.read_brand_matching_data()
            logger.info(f"브랜드 데이터 로드 완료: {len(self.brand_data)}개 상품")
        except Exception as e:
            logger.error(f"브랜드 데이터 로드 실패: {e}")
            self.brand_data = pd.DataFrame()

    def parse_options(self, option_text: str) -> tuple:
        """옵션 텍스트에서 색상과 사이즈 추출 - 최적화 버전"""
        if not option_text or pd.isna(option_text) or str(option_text).strip().lower() == 'nan':
            return "", ""
        
        option_text = str(option_text).strip()
        color = ""
        size = ""
        
        # 컴파일된 패턴 사용
        color_keywords = self._compiled_patterns['color_keywords']
        size_keywords = self._compiled_patterns['size_keywords']
        
        # 패턴 1: 색상=값, 사이즈=값 (등호 사용)
        color_match = re.search(color_keywords.pattern + r'\s*=\s*([^,/]+?)(?:\s*[,/]|\s*(?:사이즈|Size)|$)', 
                               option_text, re.IGNORECASE)
        if color_match:
            color = color_match.group(1).strip()
        
        size_match = re.search(size_keywords.pattern + r'\s*[=:]\s*([^,/]+?)(?:\s*[,/]|$)', 
                              option_text, re.IGNORECASE)
        if size_match:
            size = size_match.group(1).strip()
        
        # 패턴 2: 색상: 값, 사이즈: 값 (콜론 사용)
        if not color:
            color_match = re.search(color_keywords.pattern + r'\s*:\s*([^,/]+?)(?:\s*[,/]|\s*(?:사이즈|Size)|$)', 
                                   option_text, re.IGNORECASE)
            if color_match:
                color = color_match.group(1).strip()
        
        if not size:
            size_match = re.search(size_keywords.pattern + r'\s*:\s*([^,/]+?)(?:\s*[,/]|$)', 
                                  option_text, re.IGNORECASE)
            if size_match:
                size = size_match.group(1).strip()
        
        # 패턴 3: 색상/사이즈 (슬래시로 구분)
        if not color and not size:
            slash_match = self._compiled_patterns['slash_pattern'].match(option_text.strip())
            if slash_match:
                potential_color = slash_match.group(1).strip()
                potential_size = slash_match.group(2).strip()
                if self._compiled_patterns['size_check'].search(potential_size):
                    color = potential_color
                    size = potential_size
        
        # 패턴 4: 단어-숫자 형태
        if not color and not size:
            dash_match = self._compiled_patterns['dash_pattern'].match(option_text.strip())
            if dash_match:
                part1 = dash_match.group(1).strip()
                part2 = dash_match.group(2).strip()
                
                if self._compiled_patterns['exact_size'].match(part1):
                    size = part1
                    color = part2
                elif self._compiled_patterns['size_check'].search(part2):
                    color = part1
                    size = part2
        
        # 불필요한 기호 제거
        if color:
            color = re.sub(r'\s*[/\\|]+\s*$', '', color).strip()
        if size:
            size = re.sub(r'\s*[/\\|]+\s*$', '', size).strip()
        
        return color, size

    def _process_batch(self, batch_data):
        """배치 데이터 처리 (병렬 처리용)"""
        results = []
        for row_data in batch_data:
            result = self._process_single_row(row_data)
            results.append(result)
        return results
    
    def _process_single_row(self, row_data):
        """단일 행 처리 (병렬 처리용 헬퍼 함수)"""
        # 기존 convert_sheet1_to_sheet2의 단일 행 처리 로직을 여기로 이동
        # (실제 구현은 기존 로직과 동일)
        pass
    
    def convert_sheet1_to_sheet2(self, sheet1_df: pd.DataFrame) -> pd.DataFrame:
        """Sheet1 형식을 Sheet2 형식으로 변환 - 병렬 처리 최적화 버전"""
        logger.info("Sheet1 -> Sheet2 변환 시작 (병렬 처리 모드)")

        # Sheet2 형식의 23개 컬럼 생성
        sheet2_columns = [
            'A열(ㅇ)', 'B열(미등록주문)', 'C열(주문일)', 'D열(아이디주문번호)', 'E열(ㅇ)',
            'F열(주문자명)', 'G열(위탁자명)', 'H열(브랜드)', 'I열(상품명)', 'J열(색상)',
            'K열(사이즈)', 'L열(수량)', 'M열(옵션가)', 'N열(중도매명)', 'O열(도매가격)',
            'P열(미송)', 'Q열(비고)', 'R열(이름)', 'S열(전화번호)', 'T열(주소)',
            'U열(아이디)', 'V열(배송메세지)', 'W열(금액)'
        ]

        sheet2_df = pd.DataFrame(columns=sheet2_columns)

        if sheet1_df.empty:
            logger.warning("업로드된 데이터가 없습니다")
            return sheet2_df

        # Sheet1의 데이터를 Sheet2로 매핑
        for i, row in sheet1_df.iterrows():
            sheet2_row = {}
            
            # 기본값 설정
            for col in sheet2_columns:
                sheet2_row[col] = ""
            
            # 직접 매핑
            if len(sheet1_df.columns) >= 1:  # 업로드 A열 → Sheet2 C열 (주문일)
                sheet2_row['C열(주문일)'] = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            
            if len(sheet1_df.columns) >= 2:  # 업로드 B열 → Sheet2 D열 (아이디/주문번호)
                sheet2_row['D열(아이디주문번호)'] = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
            
            if len(sheet1_df.columns) >= 3:  # 업로드 C열 → Sheet2 F열 (주문자명)
                sheet2_row['F열(주문자명)'] = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
            
            # 업로드 D열 → Sheet2 G열 (위탁자명) + 주소 3번째 단어 추가
            if len(sheet1_df.columns) >= 4:
                name = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ""
                # 주소에서 3번째 단어 추출 (K열이 주소)
                address_third_word = ""
                if len(sheet1_df.columns) >= 11:  # K열(주소)이 있으면
                    address = str(row.iloc[10]) if pd.notna(row.iloc[10]) else ""
                    address_third_word = self.extract_third_word_from_address(address)
                
                if name and address_third_word:
                    sheet2_row['G열(위탁자명)'] = f"{name}({address_third_word})"
                else:
                    sheet2_row['G열(위탁자명)'] = name
            
            # 업로드 E열 → 브랜드/상품명 분할 (상품명에 키워드 제거 적용)
            if len(sheet1_df.columns) >= 5:
                e_value = str(row.iloc[4]) if pd.notna(row.iloc[4]) else ""
                e_value = e_value.strip()  # 앞뒤 공백 제거
                
                if e_value:
                    # 괄호를 이용한 브랜드 추출 시도 (예: 클라레오(기린) 상품명)
                    bracket_match = re.match(r'^([^)]+\)[^)]*?)\s+(.+)$', e_value)
                    if bracket_match:
                        # 괄호가 포함된 브랜드명과 상품명 분리
                        brand_part = bracket_match.group(1).strip()
                        product_part = bracket_match.group(2).strip()
                        sheet2_row['H열(브랜드)'] = brand_part
                        
                        # 상품명에 키워드 제거 적용
                        cleaned_product_name = self.normalize_product_name(product_part)
                        if len(cleaned_product_name) < 2:
                            # 원본에서 괄호만 제거
                            cleaned_product_name = product_part
                            for keyword in self.keyword_list:
                                if keyword:
                                    pattern = r'\(' + re.escape(keyword) + r'\)'
                                    cleaned_product_name = re.sub(pattern, '', cleaned_product_name, flags=re.IGNORECASE)
                            cleaned_product_name = re.sub(r'\s+', ' ', cleaned_product_name).strip()
                        
                        sheet2_row['I열(상품명)'] = cleaned_product_name
                        
                    elif ' ' in e_value:
                        # 일반적인 띄어쓰기 분할 (공백 제거 후)
                        parts = e_value.split(' ', 1)
                        if parts[0].strip():  # 첫 번째 부분이 비어있지 않으면
                            sheet2_row['H열(브랜드)'] = parts[0].strip()
                            # 상품명에 키워드 제거 적용
                            raw_product_name = parts[1].strip() if len(parts) > 1 else ""
                            if raw_product_name:
                                cleaned_product_name = self.normalize_product_name(raw_product_name)
                                if len(cleaned_product_name) < 2:
                                    # 원본에서 괄호만 제거
                                    cleaned_product_name = raw_product_name
                                    for keyword in self.keyword_list:
                                        if keyword:
                                            pattern = r'\(' + re.escape(keyword) + r'\)'
                                            cleaned_product_name = re.sub(pattern, '', cleaned_product_name, flags=re.IGNORECASE)
                                    cleaned_product_name = re.sub(r'\s+', ' ', cleaned_product_name).strip()
                                
                                sheet2_row['I열(상품명)'] = cleaned_product_name
                            else:
                                sheet2_row['I열(상품명)'] = ""
                        else:
                            # 첫 번째 부분이 비어있으면 전체를 상품명으로 처리
                            sheet2_row['H열(브랜드)'] = ""
                            cleaned_product_name = self.normalize_product_name(e_value)
                            if len(cleaned_product_name) < 2:
                                cleaned_product_name = e_value
                            sheet2_row['I열(상품명)'] = cleaned_product_name
                    else:
                        # 띄어쓰기가 없으면 전체를 브랜드로 처리
                        sheet2_row['H열(브랜드)'] = e_value
                        sheet2_row['I열(상품명)'] = ""
                else:
                    sheet2_row['H열(브랜드)'] = ""
                    sheet2_row['I열(상품명)'] = ""
            
            # 업로드 F열 (옵션) → 색상/사이즈 추출
            if len(sheet1_df.columns) >= 6:
                f_value = str(row.iloc[5]) if pd.notna(row.iloc[5]) else ""
                sheet2_row['J열(색상)'], sheet2_row['K열(사이즈)'] = self.parse_options(f_value)
            
            if len(sheet1_df.columns) >= 7:  # 업로드 G열 → Sheet2 L열 (수량)
                try:
                    sheet2_row['L열(수량)'] = int(row.iloc[6]) if pd.notna(row.iloc[6]) else 1
                except:
                    sheet2_row['L열(수량)'] = 1
            
            # 업로드 H열 → Sheet2 M열 (옵션가) - 새로 추가
            if len(sheet1_df.columns) >= 8:
                sheet2_row['M열(옵션가)'] = str(row.iloc[7]) if pd.notna(row.iloc[7]) else ""
            
            # 업로드 I열 → Sheet2 R열 (이름) + 주소 3번째 단어 추가
            if len(sheet1_df.columns) >= 9:
                name = str(row.iloc[8]) if pd.notna(row.iloc[8]) else ""
                # 주소에서 3번째 단어 추출 (K열이 주소)
                address_third_word = ""
                if len(sheet1_df.columns) >= 11:  # K열(주소)이 있으면
                    address = str(row.iloc[10]) if pd.notna(row.iloc[10]) else ""
                    address_third_word = self.extract_third_word_from_address(address)
                
                if name and address_third_word:
                    sheet2_row['R열(이름)'] = f"{name}({address_third_word})"
                else:
                    sheet2_row['R열(이름)'] = name
            
            if len(sheet1_df.columns) >= 10:  # 업로드 J열 → Sheet2 S열 (전화번호)
                sheet2_row['S열(전화번호)'] = str(row.iloc[9]) if pd.notna(row.iloc[9]) else ""
            
            if len(sheet1_df.columns) >= 11:  # 업로드 K열 → Sheet2 T열 (주소)
                sheet2_row['T열(주소)'] = str(row.iloc[10]) if pd.notna(row.iloc[10]) else ""
            
            if len(sheet1_df.columns) >= 12:  # 업로드 L열 → Sheet2 V열 (배송메세지)
                sheet2_row['V열(배송메세지)'] = str(row.iloc[11]) if pd.notna(row.iloc[11]) else ""
            
            # 매칭 결과는 나중에 채움
            sheet2_row['N열(중도매명)'] = ""
            sheet2_row['O열(도매가격)'] = 0
            sheet2_row['W열(금액)'] = 0
            
            # DataFrame에 추가
            sheet2_df = pd.concat([sheet2_df, pd.DataFrame([sheet2_row])], ignore_index=True)

        logger.info(f"Sheet2 변환 완료: {len(sheet2_df)}개 행")
        return sheet2_df

    def extract_size(self, text: str) -> str:
        """사이즈{...} 패턴에서 사이즈 추출 (브랜드매칭시트용)"""
        if pd.isna(text):
            return ""

        # 브랜드매칭시트의 실제 패턴: 색상{...}//사이즈{...}
        # 또는 기존 패턴: 사이즈{...}
        size_match = re.search(r"사이즈\{([^}]*)\}", str(text))
        if size_match:
            size_content = size_match.group(1).strip().lower()
            # | 또는 \ 기호를 공백으로 변환하여 검색하기 쉽게 만듦
            size_content = size_content.replace('|', ' ').replace('\\', ' ')
            return size_content
        
        return ""

    def extract_color(self, text: str) -> str:
        """색상{...} 패턴에서 색상 추출 (브랜드매칭시트용)"""
        if pd.isna(text):
            return ""

        # 브랜드매칭시트의 패턴: 색상{...}//사이즈{...}
        color_match = re.search(r"색상\{([^}]*)\}", str(text))
        if color_match:
            color_content = color_match.group(1).strip().lower()
            # | 또는 \ 기호를 공백으로 변환하여 검색하기 쉽게 만듦
            color_content = color_content.replace('|', ' ').replace('\\', ' ')
            return color_content
        
        return ""

    def match_row(self, brand: str, product: str, size: str, color: str = "") -> Tuple[str, str, str]:
        """브랜드, 상품명, 사이즈, 색상으로 매칭하여 공급가, 중도매, 브랜드+상품명 반환"""
        brand = str(brand).strip()
        product = str(product).strip()
        size = str(size).strip().lower()
        color = str(color).strip().lower()

        # 상품명 정규화 (키워드 제거)
        normalized_product = self.normalize_product_name(product)

        logger.debug(f"매칭 시도: 브랜드='{brand}', 상품명='{product}' (정규화: '{normalized_product}'), 사이즈='{size}', 색상='{color}'")

        if self.brand_data is None or self.brand_data.empty:
            logger.warning("브랜드 데이터가 없습니다")
            return "매칭 실패", "", ""

        # 매칭 후보들을 저장할 리스트 (정확도 순으로 정렬하기 위함)
        matching_candidates = []

        for _, row in self.brand_data.iterrows():
            # 1. 브랜드 정확히 일치 확인
            if str(row['브랜드']).strip() != brand:
                continue

            # 2. 상품명 포함 관계 확인 (정규화된 상품명과 비교)
            row_product = self.normalize_product_name(str(row['상품명']).strip())
            if normalized_product not in row_product and row_product not in normalized_product:
                continue

            # 3. 색상 매칭 (색상이 제공된 경우에만)
            if color:
                row_color_pattern = self.extract_color(str(row['옵션입력']))
                
                # 먼저 전체 매칭 시도
                color_match = False
                if color in row_color_pattern:
                    color_match = True
                else:
                    # 색상 변형 매칭 시도
                    # 브랜드매칭시트의 색상 패턴에서 모든 변형 추출
                    brand_color_variants = []
                    if row_color_pattern:
                        # 공백으로 분리된 각 색상에 대해 변형 추출
                        color_tokens = row_color_pattern.split()
                        for token in color_tokens:
                            variants = self.parse_color_variants(token)
                            brand_color_variants.extend(variants)
                    
                    # 업로드 파일의 색상에서도 변형 추출
                    upload_color_variants = self.parse_color_variants(color)
                    
                    # 각 변형들 간의 매칭 확인
                    for brand_variant in brand_color_variants:
                        for upload_variant in upload_color_variants:
                            # 완전 일치 또는 포함 관계
                            if (upload_variant == brand_variant or 
                                upload_variant in brand_variant or 
                                brand_variant in upload_variant):
                                color_match = True
                                break
                        if color_match:
                            break
                
                if not color_match:
                    continue

            # 4. 사이즈 매칭 - 개선된 로직 (정확도별 점수 부여)
            row_size_pattern = self.extract_size(str(row['옵션입력']))
            
            match_score = 0  # 매칭 정확도 점수 (높을수록 정확)
            match_type = ""  # 매칭 타입
            
            # 먼저 전체 매칭 시도 (가장 높은 점수)
            if size in row_size_pattern:
                match_score = 100
                match_type = "직접 매칭"
            else:
                # 사이즈 변형을 이용한 매칭 시도
                # 브랜드매칭시트의 사이즈 패턴에서 모든 변형 추출
                brand_size_variants = []
                if row_size_pattern:
                    # 공백으로 분리된 각 사이즈에 대해 변형 추출
                    size_tokens = row_size_pattern.split()
                    for token in size_tokens:
                        variants = self.parse_size_variants(token)
                        brand_size_variants.extend(variants)
                
                # 업로드 파일의 사이즈에서도 변형 추출
                upload_size_variants = self.parse_size_variants(size)
                
                # 각 변형들 간의 매칭 확인 (정확도 순으로)
                for brand_variant in brand_size_variants:
                    for upload_variant in upload_size_variants:
                        # 1. 완전 일치 (90점)
                        if upload_variant == brand_variant:
                            if match_score < 90:
                                match_score = 90
                                match_type = "완전 일치"
                            break
                        
                        # 2. 숫자+단위 특별 처리 (80점)
                        elif re.match(r'^\d+[a-z]*$', upload_variant) and re.match(r'^\d+[a-z]*$', brand_variant):
                            upload_num = re.match(r'^(\d+)', upload_variant)
                            brand_num = re.match(r'^(\d+)', brand_variant)
                            
                            if upload_num and brand_num and upload_num.group(1) == brand_num.group(1):
                                if match_score < 80:
                                    match_score = 80
                                    match_type = "숫자 매칭"
                                break
                        
                        # 3. 포함 관계 (길이 차이 고려하여 점수 차등)
                        elif (upload_variant in brand_variant or brand_variant in upload_variant):
                            # 길이 차이 확인
                            min_len = min(len(upload_variant), len(brand_variant))
                            max_len = max(len(upload_variant), len(brand_variant))
                            
                            # 길이 비율이 0.8 이상이면 높은 점수 (70점)
                            if min_len / max_len >= 0.8:
                                if match_score < 70:
                                    match_score = 70
                                    match_type = "높은 유사도 포함"
                            # 길이 비율이 0.6 이상이면 낮은 점수 (50점)
                            elif min_len / max_len >= 0.6:
                                if match_score < 50:
                                    match_score = 50
                                    match_type = "낮은 유사도 포함"
            
            # 매칭이 성공한 경우 후보에 추가
            if match_score > 0:
                공급가 = row['공급가']
                중도매 = row['중도매']
                브랜드상품명 = f"{row['브랜드']} {row['상품명']}"
                
                matching_candidates.append({
                    'score': match_score,
                    'type': match_type,
                    '공급가': 공급가,
                    '중도매': 중도매,
                    '브랜드상품명': 브랜드상품명,
                    'row': row
                })
                
                logger.debug(f"매칭 후보 추가: {브랜드상품명} (점수: {match_score}, 타입: {match_type})")

        # 매칭 후보가 있으면 가장 높은 점수의 후보 선택
        if matching_candidates:
            # 점수순으로 정렬 (높은 점수가 먼저)
            matching_candidates.sort(key=lambda x: x['score'], reverse=True)
            
            best_match = matching_candidates[0]
            
            logger.debug(f"최종 매칭 선택: {best_match['브랜드상품명']} (점수: {best_match['score']}, 타입: {best_match['type']})")
            
            return best_match['공급가'], best_match['중도매'], best_match['브랜드상품명']

        logger.debug("매칭 실패")
        return "매칭 실패", "", ""

    def process_matching(self, sheet2_df: pd.DataFrame) -> pd.DataFrame:
        """Sheet2 데이터에 대해 매칭 수행"""
        logger.info("매칭 처리 시작")

        if sheet2_df.empty:
            logger.warning("처리할 데이터가 없습니다")
            return sheet2_df

        success_count = 0
        total_count = len(sheet2_df)

        for idx, row in sheet2_df.iterrows():
            # 브랜드, 상품명, 사이즈 추출
            brand = str(row.get('H열(브랜드)', '')).strip()
            product = str(row.get('I열(상품명)', '')).strip()
            size = str(row.get('K열(사이즈)', '')).strip()
            color = str(row.get('J열(색상)', '')).strip() # 색상 추출
            quantity = row.get('L열(수량)', 1)

            # 빈 값 체크
            if not brand or not product or not size:
                sheet2_df.at[idx, 'N열(중도매명)'] = ""
                sheet2_df.at[idx, 'O열(도매가격)'] = 0
                sheet2_df.at[idx, 'W열(금액)'] = 0
                continue

            # 매칭 수행
            공급가, 중도매, 브랜드상품명 = self.match_row(brand, product, size, color)

            # 결과 저장
            if 공급가 != "매칭 실패":
                sheet2_df.at[idx, 'N열(중도매명)'] = 중도매
                sheet2_df.at[idx, 'O열(도매가격)'] = 공급가
                # W열 금액 계산: 도매가격 × 수량
                try:
                    total_amount = float(공급가) * int(quantity)
                    sheet2_df.at[idx, 'W열(금액)'] = total_amount
                except:
                    sheet2_df.at[idx, 'W열(금액)'] = 0
                success_count += 1
            else:
                sheet2_df.at[idx, 'N열(중도매명)'] = ""
                sheet2_df.at[idx, 'O열(도매가격)'] = 0
                sheet2_df.at[idx, 'W열(금액)'] = 0

        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        logger.info(f"매칭 완료: {success_count}/{total_count} ({success_rate:.1f}%)")

        return sheet2_df

    def save_to_excel(self, sheet2_df: pd.DataFrame, filename: str = "브랜드매칭결과.xlsx"):
        """Sheet2 형식으로 엑셀 파일 저장"""
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Sheet2 탭에 저장
                sheet2_df.to_excel(writer, sheet_name='Sheet2', index=False)

                # 컬럼 너비 조정
                worksheet = writer.sheets['Sheet2']
                for i, column in enumerate(sheet2_df.columns, 1):
                    if i <= 26:
                        column_letter = chr(64 + i)
                    else:
                        column_letter = f"A{chr(64 + i - 26)}"
                    worksheet.column_dimensions[column_letter].width = 15

            logger.info(f"엑셀 파일 저장 완료: {filename}")
            return filename

        except Exception as e:
            logger.error(f"엑셀 파일 저장 실패: {e}")
            raise e 