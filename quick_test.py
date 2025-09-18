#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
단일 매칭 빠른 테스트
"""

import time
from brand_matching_system import BrandMatchingSystem

def quick_test():
    print("=== 단일 매칭 빠른 테스트 ===")
    
    # 시스템 초기화
    system = BrandMatchingSystem()
    print(f"브랜드 데이터: {len(system.brand_data):,}개")
    
    # 실제 존재하는 브랜드로 테스트
    test_cases = [
        ("소예", "클래식무발타이즈", "s", "그레이"),
        ("아이아이", "루나벨드레스", "100", "퍼플"),
        ("린도", "B프릴귀달이보넷", "free", "핑크"),
    ]
    
    for i, (brand, product, size, color) in enumerate(test_cases, 1):
        print(f"\n{i}. 테스트: {brand} - {product} ({color}/{size})")
        
        start_time = time.time()
        result = system.match_row(brand, product, size, color)
        elapsed = time.time() - start_time
        
        print(f"   결과: {result}")
        print(f"   소요시간: {elapsed:.3f}초")
        
        if len(result) == 4 and result[3]:  # success == True
            print(f"   ✅ 성공!")
        else:
            print(f"   ❌ 실패")

if __name__ == "__main__":
    quick_test() 