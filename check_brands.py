#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브랜드 데이터 확인 - 특정 브랜드들이 실제로 존재하는지 확인
"""

import pandas as pd
from brand_matching_system import BrandMatchingSystem

def check_brands():
    print("=== 브랜드 데이터 확인 ===")
    
    # 시스템 초기화
    system = BrandMatchingSystem()
    print(f"총 브랜드 데이터: {len(system.brand_data):,}개")
    
    # 모든 브랜드 목록
    all_brands = system.brand_data['브랜드'].unique()
    print(f"고유 브랜드 수: {len(all_brands)}개")
    
    # 찾고 있던 브랜드들
    target_brands = ['소예', '린도', '마마미', '로다제이', '바비', '보니토', '아르키드', '미미앤루', '니니벨로', '화이트스케치북']
    
    print(f"\n=== 타겟 브랜드 존재 여부 확인 ===")
    found_brands = []
    for brand in target_brands:
        matches = system.brand_data[system.brand_data['브랜드'].str.strip() == brand]
        if not matches.empty:
            print(f"✅ '{brand}': {len(matches)}개 상품")
            found_brands.append(brand)
            
            # 첫 번째 상품 정보 표시
            first_product = matches.iloc[0]
            print(f"   예시: {first_product['상품명']} - {first_product['옵션입력']}")
        else:
            print(f"❌ '{brand}': 없음")
    
    print(f"\n발견된 브랜드: {len(found_brands)}개")
    
    # 유사한 브랜드 찾기
    print(f"\n=== 유사한 브랜드 찾기 ===")
    for brand in target_brands:
        if brand not in found_brands:
            similar = []
            for existing_brand in all_brands:
                if brand.lower() in existing_brand.lower() or existing_brand.lower() in brand.lower():
                    similar.append(existing_brand)
            
            if similar:
                print(f"'{brand}' 유사 브랜드: {similar[:5]}")  # 상위 5개만
    
    # 실제 존재하는 브랜드들 중 일부 표시
    print(f"\n=== 실제 존재하는 브랜드 샘플 (상위 20개) ===")
    sample_brands = all_brands[:20]
    for i, brand in enumerate(sample_brands):
        count = len(system.brand_data[system.brand_data['브랜드'].str.strip() == brand])
        print(f"{i+1:2d}. {brand} ({count}개 상품)")
    
    return found_brands

if __name__ == "__main__":
    found_brands = check_brands()
    print(f"\n🎯 실제 존재하는 타겟 브랜드: {found_brands}") 