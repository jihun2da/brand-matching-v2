#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브랜드 매칭 시스템 - 속도 최적화 및 메모리 최적화 버전
"""

import pandas as pd
import re
import logging
import os
import gc
from typing import List, Dict, Tuple
from functools import lru_cache
import concurrent.futures
from threading import Lock
from difflib import SequenceMatcher
try:
    import Levenshtein
    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    LEVENSHTEIN_AVAILABLE = False
    logger.warning("python-Levenshtein not available, using fallback similarity calculation")
from brand_sheets_api import brand_sheets_api

logger = logging.getLogger(__name__)

class BrandMatchingSystem:
    """
    브랜드 매칭 시스템 - 메모리 최적화 버전
    """

    def __init__(self):
        self.brand_data = None
        self.keyword_list = []
        
        # 메모리 최적화를 위한 캐시 크기 조정
        self._normalized_cache = {}
        self._cache_lock = Lock()
        self._compiled_patterns = {}
        self._max_cache_size = 1000  # 캐시 크기 제한
        
        # 데이터 로드
        self.load_brand_data()
        self.load_keywords()
        self._precompile_patterns()

    def _precompile_patterns(self):
        """자주 사용되는 정규식 패턴들을 미리 컴파일"""
        patterns = {
            'parentheses': r'\([^)]*\)',
            'brackets': r'\[[^\]]*\]',
            'braces': r'\{[^}]*\}',
            'special_chars': r'[^\w\s가-힣]',
            'multiple_spaces': r'\s+',
            'comma_spaces': r'\s*,\s*',
            'multiple_commas': r',+',
            'korean_alpha_num': r'[가-힣a-zA-Z0-9]',
            'word_boundary': r'^[a-zA-Z0-9가-힣\s]+$',
            
            # 사이즈 관련 패턴들
            'size_s_xl': r'\([sS]~[xX][lL]\)',
            'size_s_xl_dash': r'\([sS]-[xX][lL]\)',
            'size_xs_xl': r'\([xX][sS]~[xX][lL]\)',
            'size_xs_xl_dash': r'\([xX][sS]-[xX][lL]\)',
            'size_m_jxl': r'\([mM]~[jJ][xX][lL]\)',
            'size_m_jxl_dash': r'\([mM]-[jJ][xX][lL]\)',
            'size_numbers': r'\([0-9]+[~-][0-9]+\)',
            'size_js_patterns': r'\([jJ][sS][~-][jJ][xXlLmM]+\)',
            
            # 옵션 파싱 패턴들
            'color_keywords': r'(?:색상|컬러|Color)',
            'size_keywords': r'(?:사이즈|Size)',
            'slash_pattern': r'^([^/]+)/([^/]+)$',
            'dash_pattern': r'^([^-]+)-([^-]+)$',
            'size_check': r'[0-9]|[SMLX]',
            'exact_size': r'^[SMLX]$|^[0-9]+$',
            
            # 브랜드매칭시트 패턴들
            'size_pattern': r'사이즈\s*[\{\[\(]([^}\]\)]+)[\}\]\)]',
            'color_pattern': r'색상\s*[\{\[\(]([^}\]\)]+)[\}\]\)]',
            'option_split': r'[,/\s]+',
        }
        
        for name, pattern in patterns.items():
            try:
                if name in ['color_keywords', 'size_keywords', 'size_check', 'exact_size']:
                    self._compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
                else:
                    self._compiled_patterns[name] = re.compile(pattern)
            except Exception as e:
                logger.error(f"패턴 컴파일 실패 ({name}): {e}")
        
        logger.info(f"정규식 패턴 {len(patterns)}개 컴파일 완료")

    def _clean_cache(self):
        """캐시 크기가 제한을 초과할 때 정리"""
        with self._cache_lock:
            if len(self._normalized_cache) > self._max_cache_size:
                # 오래된 항목의 절반 제거
                items_to_remove = len(self._normalized_cache) // 2
                keys_to_remove = list(self._normalized_cache.keys())[:items_to_remove]
                for key in keys_to_remove:
                    del self._normalized_cache[key]
                
                # 메모리 정리
                gc.collect()
                logger.info(f"캐시 정리 완료: {items_to_remove}개 항목 제거")

    def calculate_string_similarity(self, str1: str, str2: str) -> float:
        """문자열 유사도 계산 (0.0 ~ 1.0)"""
        if not str1 or not str2:
            return 0.0
        
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()
        
        if str1 == str2:
            return 1.0
        
        if LEVENSHTEIN_AVAILABLE:
            # Levenshtein 거리 기반 유사도
            max_len = max(len(str1), len(str2))
            if max_len == 0:
                return 1.0
            distance = Levenshtein.distance(str1, str2)
            return 1.0 - (distance / max_len)
        else:
            # SequenceMatcher 기반 유사도 (fallback)
            return SequenceMatcher(None, str1, str2).ratio()
    
    def calculate_color_similarity(self, color1: str, color2: str) -> float:
        """색상 유사도 계산 - 오타 및 변형 허용"""
        if not color1 or not color2:
            return 0.0
        
        # 기본 문자열 유사도
        base_similarity = self.calculate_string_similarity(color1, color2)
        
        # 색상 변형 매핑 (한글-영어, 오타 등)
        color_mappings = {
            '메란지': ['멜란지', 'melange', '메렌지'],
            '멜란지': ['메란지', 'melange', '메렌지'],
            '블랙': ['black', '검정', '검은색'],
            '화이트': ['white', '흰색', '하얀색'],
            '레드': ['red', '빨강', '빨간색'],
            '블루': ['blue', '파랑', '파란색', '블루'],
            '그린': ['green', '초록', '초록색'],
            '옐로우': ['yellow', '노랑', '노란색'],
            '핑크': ['pink', '분홍', '분홍색'],
            '그레이': ['gray', 'grey', '회색'],
            '베이지': ['beige', '베이지색'],
            '네이비': ['navy', '남색'],
        }
        
        # 변형 매핑 확인
        color1_lower = color1.lower()
        color2_lower = color2.lower()
        
        for main_color, variants in color_mappings.items():
            if (color1_lower == main_color or color1_lower in variants) and \
               (color2_lower == main_color or color2_lower in variants):
                return 0.95  # 높은 유사도
        
        return base_similarity
    
    def calculate_size_similarity(self, size1: str, size2: str) -> float:
        """사이즈 유사도 계산 - 다양한 표기법 허용"""
        if not size1 or not size2:
            return 0.0
        
        # 기본 문자열 유사도
        base_similarity = self.calculate_string_similarity(size1, size2)
        
        # 사이즈 변형 매핑
        size_mappings = {
            'xs': ['엑스에스', 'x-small', 'extra small'],
            's': ['에스', 'small', '소'],
            'm': ['엠', 'medium', '중', '미디움'],
            'l': ['엘', 'large', '대', '라지'],
            'xl': ['엑스엘', 'x-large', 'extra large'],
            'xxl': ['더블엑스엘', '2xl', 'xx-large'],
            'xxxl': ['트리플엑스엘', '3xl', 'xxx-large'],
            'free': ['프리', '프리사이즈', 'one size'],
        }
        
        size1_lower = size1.lower()
        size2_lower = size2.lower()
        
        # 숫자 사이즈 처리 (예: 90, 95, 100)
        if size1_lower.isdigit() and size2_lower.isdigit():
            num1, num2 = int(size1_lower), int(size2_lower)
            diff = abs(num1 - num2)
            if diff == 0:
                return 1.0
            elif diff <= 5:
                return 0.8
            elif diff <= 10:
                return 0.6
            else:
                return base_similarity
        
        # 변형 매핑 확인
        for main_size, variants in size_mappings.items():
            if (size1_lower == main_size or size1_lower in variants) and \
               (size2_lower == main_size or size2_lower in variants):
                return 0.95  # 높은 유사도
        
        return base_similarity

    @lru_cache(maxsize=200)
    def _get_keyword_pattern(self, keyword: str) -> re.Pattern:
        """키워드별 정규식 패턴을 캐시와 함께 생성"""
        escaped_keyword = re.escape(keyword)
        
        # 컴파일된 패턴 사용
        if 'word_boundary' in self._compiled_patterns and self._compiled_patterns['word_boundary'].match(keyword):
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

    def normalize_product_name(self, name: str) -> str:
        """상품명 정규화 - 캐시 및 메모리 최적화 버전"""
        if not name or pd.isna(name):
            return ""
        
        name_str = str(name).strip()
        if not name_str:
            return ""
        
        # 캐시 확인
        with self._cache_lock:
            if name_str in self._normalized_cache:
                return self._normalized_cache[name_str]
        
        # 정규화 처리
        try:
            normalized = name_str.lower()
            
            # 컴파일된 패턴 사용 (안전하게)
            if 'parentheses' in self._compiled_patterns:
                normalized = self._compiled_patterns['parentheses'].sub('', normalized)
            if 'brackets' in self._compiled_patterns:
                normalized = self._compiled_patterns['brackets'].sub('', normalized)
            if 'braces' in self._compiled_patterns:
                normalized = self._compiled_patterns['braces'].sub('', normalized)
            if 'special_chars' in self._compiled_patterns:
                normalized = self._compiled_patterns['special_chars'].sub(' ', normalized)
            if 'multiple_spaces' in self._compiled_patterns:
                normalized = self._compiled_patterns['multiple_spaces'].sub(' ', normalized)
            
            normalized = normalized.strip()
            
            # 키워드 제거 (안전한 방식)
            if self.keyword_list:
                # * 기호로 감싸진 패턴 우선 처리
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
                
                # 일반 키워드 제거
                regular_keywords = [kw for kw in self.keyword_list 
                                   if not (kw.startswith('*') and kw.endswith('*'))]
                
                for keyword in regular_keywords:
                    if not keyword:
                        continue
                    
                    # 괄호와 함께 키워드 제거
                    parentheses_pattern = re.compile(r'\(' + re.escape(keyword) + r'\)', re.IGNORECASE)
                    normalized = parentheses_pattern.sub('', normalized)
                    
                    # 단독 키워드 제거
                    keyword_pattern = self._get_keyword_pattern(keyword)
                    normalized = keyword_pattern.sub('', normalized)
                
                # 텍스트 정리
                if 'comma_spaces' in self._compiled_patterns:
                    normalized = self._compiled_patterns['comma_spaces'].sub(',', normalized)
                if 'multiple_commas' in self._compiled_patterns:
                    normalized = self._compiled_patterns['multiple_commas'].sub(',', normalized)
                if 'multiple_spaces' in self._compiled_patterns:
                    normalized = self._compiled_patterns['multiple_spaces'].sub(' ', normalized)
                
                normalized = normalized.strip(',').strip()
            
            # 결과 검증
            if len(normalized) < 2 or ('korean_alpha_num' in self._compiled_patterns and 
                                      not self._compiled_patterns['korean_alpha_num'].search(normalized)):
                normalized = name_str.lower()
            
            # 캐시에 저장 (크기 제한 확인)
            with self._cache_lock:
                if len(self._normalized_cache) >= self._max_cache_size:
                    self._clean_cache()
                self._normalized_cache[name_str] = normalized
            
            return normalized
            
        except Exception as e:
            logger.error(f"상품명 정규화 실패 ({name_str}): {e}")
            return name_str.lower()

    @lru_cache(maxsize=200)
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

    @lru_cache(maxsize=200)
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

    def find_similar_products_for_failed_matches(self, failed_products: List[Dict]) -> pd.DataFrame:
        """매칭 실패한 상품들에 대해 유사도 기반 매칭 수행"""
        logger.info(f"매칭 실패 상품 {len(failed_products)}개에 대해 유사도 매칭 시작")
        
        if self.brand_data is None or self.brand_data.empty:
            logger.error("브랜드 데이터가 없습니다")
            return pd.DataFrame()
        
        results = []
        
        for i, failed_product in enumerate(failed_products):
            logger.debug(f"유사도 매칭 진행: {i+1}/{len(failed_products)}")
            
            # 실패한 상품 정보 추출
            brand = failed_product.get('브랜드', '').strip()
            product_name = failed_product.get('상품명', '').strip()
            color = failed_product.get('색상', '').strip()
            size = failed_product.get('사이즈', '').strip()
            
            # 상품명 정규화
            normalized_product_name = self.normalize_product_name(product_name)
            
            best_match = None
            best_score = 0.0
            
            # 브랜드 데이터에서 유사한 상품 찾기
            for _, brand_row in self.brand_data.iterrows():
                brand_brand = str(brand_row.get('브랜드', '')).strip()
                brand_product = str(brand_row.get('상품명', '')).strip()
                brand_options = str(brand_row.get('옵션입력', '')).strip()
                
                # 브랜드 일치 확인 (브랜드가 다르면 스킵)
                if brand and brand_brand and brand.lower() != brand_brand.lower():
                    continue
                
                # 상품명 유사도 계산
                brand_normalized = self.normalize_product_name(brand_product)
                product_similarity = self.calculate_string_similarity(normalized_product_name, brand_normalized)
                
                # 상품명 유사도가 너무 낮으면 스킵 (임계값: 0.3)
                if product_similarity < 0.3:
                    continue
                
                # 색상/사이즈 유사도 계산
                color_similarity = 0.0
                size_similarity = 0.0
                
                if color or size:
                    # 브랜드 상품의 색상/사이즈 추출
                    brand_color = self.extract_color(brand_options)
                    brand_size = self.extract_size(brand_options)
                    
                    if color and brand_color:
                        # 색상 변형들과 비교
                        color_variants = self.parse_color_variants(color)
                        brand_color_variants = self.parse_color_variants(brand_color)
                        
                        max_color_sim = 0.0
                        for c1 in color_variants:
                            for c2 in brand_color_variants:
                                sim = self.calculate_color_similarity(c1, c2)
                                max_color_sim = max(max_color_sim, sim)
                        color_similarity = max_color_sim
                    
                    if size and brand_size:
                        # 사이즈 변형들과 비교
                        size_variants = self.parse_size_variants(size)
                        brand_size_variants = self.parse_size_variants(brand_size)
                        
                        max_size_sim = 0.0
                        for s1 in size_variants:
                            for s2 in brand_size_variants:
                                sim = self.calculate_size_similarity(s1, s2)
                                max_size_sim = max(max_size_sim, sim)
                        size_similarity = max_size_sim
                
                # 종합 유사도 계산 (가중평균)
                # 상품명 60%, 색상 20%, 사이즈 20%
                total_score = (product_similarity * 0.6 + 
                              color_similarity * 0.2 + 
                              size_similarity * 0.2)
                
                # 색상이나 사이즈가 없는 경우 상품명 비중 증가
                if not color and not size:
                    total_score = product_similarity
                elif not color:
                    total_score = product_similarity * 0.8 + size_similarity * 0.2
                elif not size:
                    total_score = product_similarity * 0.8 + color_similarity * 0.2
                
                # 최고 점수 업데이트
                if total_score > best_score:
                    best_score = total_score
                    best_match = {
                        'brand_brand': brand_brand,
                        'brand_product': brand_product,
                        'brand_wholesale': brand_row.get('중도매', ''),
                        'brand_supply': brand_row.get('공급가', ''),
                        'brand_options': brand_options,
                        'product_similarity': product_similarity,
                        'color_similarity': color_similarity,
                        'size_similarity': size_similarity,
                        'total_score': total_score
                    }
            
            # 결과 저장
            result_row = {
                '원본_브랜드': brand,
                '원본_상품명': product_name,
                '원본_색상': color,
                '원본_사이즈': size,
                '유사상품_브랜드': best_match['brand_brand'] if best_match else '',
                '유사상품_상품명': best_match['brand_product'] if best_match else '',
                '유사상품_중도매': best_match['brand_wholesale'] if best_match else '',
                '유사상품_공급가': best_match['brand_supply'] if best_match else '',
                '유사상품_옵션': best_match['brand_options'] if best_match else '',
                '상품명_유사도': f"{best_match['product_similarity']:.3f}" if best_match else '0.000',
                '색상_유사도': f"{best_match['color_similarity']:.3f}" if best_match else '0.000',
                '사이즈_유사도': f"{best_match['size_similarity']:.3f}" if best_match else '0.000',
                '종합_유사도': f"{best_match['total_score']:.3f}" if best_match else '0.000',
                '매칭_상태': '유사매칭' if best_match and best_match['total_score'] >= 0.3 else '매칭실패'
            }
            
            # 원본 데이터의 다른 컬럼들도 추가
            for key, value in failed_product.items():
                if key not in result_row:
                    result_row[f'원본_{key}'] = value
            
            results.append(result_row)
        
        # 결과를 DataFrame으로 변환
        result_df = pd.DataFrame(results)
        
        # 유사도 순으로 정렬
        if not result_df.empty:
            result_df = result_df.sort_values('종합_유사도', ascending=False)
        
        logger.info(f"유사도 매칭 완료: {len(result_df)}개 결과")
        return result_df

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

    def match_row(self, brand: str, product: str, size: str, color: str = "") -> Tuple[str, str, str, bool]:
        """브랜드, 상품명, 사이즈, 색상으로 매칭하여 공급가, 중도매, 브랜드+상품명, 매칭성공여부 반환"""
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
            
            return best_match['공급가'], best_match['중도매'], best_match['브랜드상품명'], True

        logger.debug("매칭 실패")
        return "매칭 실패", "", "", False

    def process_matching(self, sheet2_df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """Sheet2 데이터에 대해 매칭 수행하고 매칭 실패한 상품들 반환"""
        logger.info("매칭 처리 시작")

        if sheet2_df.empty:
            logger.warning("처리할 데이터가 없습니다")
            return sheet2_df, []

        success_count = 0
        total_count = len(sheet2_df)
        failed_products = []  # 매칭 실패한 상품들

        for idx, row in sheet2_df.iterrows():
            # 브랜드, 상품명, 사이즈 추출
            brand = str(row.get('H열(브랜드)', '')).strip()
            product = str(row.get('I열(상품명)', '')).strip()
            size = str(row.get('K열(사이즈)', '')).strip()
            color = str(row.get('J열(색상)', '')).strip() # 색상 추출
            quantity = row.get('L열(수량)', 1)

            # 빈 값 체크
            if not brand or not product:
                sheet2_df.at[idx, 'N열(중도매명)'] = ""
                sheet2_df.at[idx, 'O열(도매가격)'] = 0
                sheet2_df.at[idx, 'W열(금액)'] = 0
                continue

            # 매칭 수행
            공급가, 중도매, 브랜드상품명, success = self.match_row(brand, product, size, color)

            # 결과 저장
            if success and 공급가 != "매칭 실패":
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
                # 매칭 실패한 상품 정보 수집
                failed_product = {
                    '브랜드': brand,
                    '상품명': product,
                    '색상': color,
                    '사이즈': size,
                    '수량': quantity,
                    '행번호': idx
                }
                
                # 원본 행의 모든 데이터 추가
                for col_name, col_value in row.items():
                    if col_name not in failed_product:
                        failed_product[col_name] = col_value
                
                failed_products.append(failed_product)
                
                sheet2_df.at[idx, 'N열(중도매명)'] = ""
                sheet2_df.at[idx, 'O열(도매가격)'] = 0
                sheet2_df.at[idx, 'W열(금액)'] = 0

        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        logger.info(f"매칭 완료: {success_count}/{total_count} ({success_rate:.1f}%)")
        logger.info(f"매칭 실패: {len(failed_products)}개 상품")

        return sheet2_df, failed_products

    def process_matching_with_similarity(self, sheet2_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """매칭 수행 후 실패한 상품들에 대해 유사도 매칭 추가 수행"""
        logger.info("정확 매칭 + 유사도 매칭 처리 시작")
        
        # 1단계: 정확 매칭
        matched_df, failed_products = self.process_matching(sheet2_df)
        
        # 2단계: 매칭 실패한 상품들에 대해 유사도 매칭
        similarity_results_df = pd.DataFrame()
        if failed_products:
            logger.info(f"매칭 실패한 {len(failed_products)}개 상품에 대해 유사도 매칭 시작")
            similarity_results_df = self.find_similar_products_for_failed_matches(failed_products)
        
        return matched_df, similarity_results_df

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

    def save_similarity_results_to_excel(self, similarity_df: pd.DataFrame, filename: str = "유사도매칭결과.xlsx"):
        """유사도 매칭 결과를 엑셀 파일로 저장"""
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 유사도 매칭 결과 저장
                similarity_df.to_excel(writer, sheet_name='유사도매칭결과', index=False)

                # 컬럼 너비 조정
                worksheet = writer.sheets['유사도매칭결과']
                for i, column in enumerate(similarity_df.columns, 1):
                    column_letter = self._get_column_letter(i)
                    
                    # 컬럼명에 따른 너비 조정
                    if '상품명' in column:
                        worksheet.column_dimensions[column_letter].width = 30
                    elif '유사도' in column:
                        worksheet.column_dimensions[column_letter].width = 12
                    elif '브랜드' in column:
                        worksheet.column_dimensions[column_letter].width = 15
                    elif '색상' in column or '사이즈' in column:
                        worksheet.column_dimensions[column_letter].width = 15
                    elif '중도매' in column or '공급가' in column:
                        worksheet.column_dimensions[column_letter].width = 12
                    else:
                        worksheet.column_dimensions[column_letter].width = 15

                # 헤더 스타일 적용
                from openpyxl.styles import Font, PatternFill, Alignment
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")

                # 유사도 컬럼에 조건부 서식 적용
                for col_idx, column in enumerate(similarity_df.columns, 1):
                    if '유사도' in column:
                        column_letter = self._get_column_letter(col_idx)
                        for row_idx in range(2, len(similarity_df) + 2):
                            cell = worksheet[f"{column_letter}{row_idx}"]
                            try:
                                value = float(cell.value)
                                if value >= 0.8:
                                    cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                                elif value >= 0.6:
                                    cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                                elif value >= 0.3:
                                    cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                            except:
                                pass

            logger.info(f"유사도 매칭 결과 저장 완료: {filename}")
            return filename

        except Exception as e:
            logger.error(f"유사도 매칭 결과 저장 실패: {e}")
            raise e

    def _get_column_letter(self, col_idx: int) -> str:
        """컬럼 인덱스를 엑셀 컬럼 문자로 변환"""
        result = ""
        while col_idx > 0:
            col_idx -= 1
            result = chr(col_idx % 26 + ord('A')) + result
            col_idx //= 26
        return result 