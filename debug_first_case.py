#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
첫 번째 케이스 디버깅
"""

import time
from brand_matching_system import BrandMatchingSystem

def debug_first_case():
    print("=== 첫 번째 케이스 디버깅 ===")
    
    system = BrandMatchingSystem()
    
    # 문제가 되는 케이스
    brand = "소예"
    product = "클래식무발타이즈"
    size = "s"
    color = "그레이"
    
    print(f"디버깅: {brand} - {product} ({color}/{size})")
    
    # 브랜드 필터링 확인
    brand_filtered = system.brand_data[system.brand_data['브랜드'].str.strip() == brand]
    print(f"브랜드 '{brand}' 필터링 결과: {len(brand_filtered)}개")
    
    if not brand_filtered.empty:
        print("샘플 데이터:")
        for i, (_, row) in enumerate(brand_filtered.head(3).iterrows()):
            print(f"  {i+1}. {row['상품명']} - {row['옵션입력']}")
    
    # 상품명 정규화 확인
    normalized_product = system.normalize_product_name(product)
    print(f"정규화된 상품명: '{product}' -> '{normalized_product}'")
    
    # 매칭 시도 (타임아웃 3초)
    print("\n매칭 시도 중... (최대 3초)")
    start_time = time.time()
    
    try:
        result = system.match_row(brand, product, size, color)
        elapsed = time.time() - start_time
        print(f"결과: {result}")
        print(f"소요시간: {elapsed:.3f}초")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"오류: {e}")
        print(f"소요시간: {elapsed:.3f}초")

if __name__ == "__main__":
    debug_first_case() 