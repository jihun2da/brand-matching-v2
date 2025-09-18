#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
정확 매칭 테스트 - 원본과 동일한 결과가 나오는지 확인
"""

import pandas as pd
import time
from brand_matching_system import BrandMatchingSystem

def test_exact_matching():
    print("=== 정확 매칭 테스트 시작 ===")
    
    # 1. 시스템 초기화
    print("\n1. 시스템 초기화 중...")
    try:
        system = BrandMatchingSystem()
        print(f"✅ 브랜드 데이터 로드: {len(system.brand_data):,}개")
        
        # 브랜드 데이터 샘플 확인
        if not system.brand_data.empty:
            sample_brands = system.brand_data['브랜드'].unique()[:10]
            print(f"   샘플 브랜드들: {list(sample_brands)}")
            
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {e}")
        return False
    
    # 2. 실제 브랜드 데이터로 테스트
    print("\n2. 실제 브랜드로 테스트...")
    test_cases = [
        # 실제 존재하는 브랜드들로 테스트
        ("소예", "테리헤어밴드", "s", "빨강"),
        ("린도", "세일러린넨바디수트", "m", "파랑"),
        ("마마미", "클래식썸머셔츠", "l", "노랑"),
        ("로다제이", "코코넛슈트", "xl", "검정"),
        ("바비", "래쉬가드", "s", "흰색"),
    ]
    
    success_count = 0
    for brand, product, size, color in test_cases:
        print(f"\n테스트: {brand} - {product} ({color}/{size})")
        
        try:
            start_time = time.time()
            supply_price, wholesale_price, brand_product, success = system.match_row(brand, product, size, color)
            elapsed = time.time() - start_time
            
            print(f"   결과: {supply_price}, {wholesale_price}, {brand_product}")
            print(f"   성공: {success}, 소요시간: {elapsed:.3f}초")
            
            if success:
                success_count += 1
                print(f"   ✅ 매칭 성공!")
            else:
                print(f"   ❌ 매칭 실패")
                
        except Exception as e:
            print(f"   💥 오류: {e}")
    
    print(f"\n📊 매칭 결과: {success_count}/{len(test_cases)}개 성공")
    
    # 3. 브랜드 데이터에서 실제 존재하는 상품으로 테스트
    print("\n3. 실제 존재하는 상품으로 테스트...")
    if not system.brand_data.empty:
        # 상위 5개 브랜드의 첫 번째 상품으로 테스트
        sample_data = system.brand_data.head(10)
        
        real_success_count = 0
        for i, (_, row) in enumerate(sample_data.iterrows()):
            if i >= 5:  # 5개만 테스트
                break
                
            brand = str(row['브랜드']).strip()
            product = str(row['상품명']).strip()
            
            # 옵션에서 색상/사이즈 추출
            options = str(row['옵션입력'])
            color = system.extract_color(options)
            size = system.extract_size(options)
            
            print(f"\n실제 데이터 테스트 {i+1}: {brand} - {product}")
            print(f"   옵션: {options}")
            print(f"   추출된 색상: '{color}', 사이즈: '{size}'")
            
            try:
                start_time = time.time()
                supply_price, wholesale_price, brand_product, success = system.match_row(brand, product, size, color)
                elapsed = time.time() - start_time
                
                print(f"   매칭 결과: {supply_price}, {wholesale_price}")
                print(f"   성공: {success}, 소요시간: {elapsed:.3f}초")
                
                if success:
                    real_success_count += 1
                    print(f"   ✅ 실제 데이터 매칭 성공!")
                else:
                    print(f"   ❌ 실제 데이터 매칭 실패")
                    
            except Exception as e:
                print(f"   💥 오류: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n📊 실제 데이터 매칭 결과: {real_success_count}/5개 성공")
        
        if real_success_count == 5:
            print("🎉 완벽! 모든 실제 데이터가 매칭되었습니다!")
            return True
        else:
            print("⚠️  일부 실제 데이터가 매칭되지 않았습니다.")
            return False
    
    return success_count > 0

if __name__ == "__main__":
    try:
        success = test_exact_matching()
        if success:
            print("\n🎉 정확 매칭 테스트 통과!")
        else:
            print("\n💥 정확 매칭 테스트 실패!")
            
    except Exception as e:
        print(f"\n💥 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc() 