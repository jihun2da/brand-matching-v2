#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_sheet1_to_sheet2 메서드 테스트
"""

import pandas as pd
import time
from brand_matching_system import BrandMatchingSystem

def test_convert():
    print("테스트 시작...")
    
    # 테스트 데이터 생성 (76개 행)
    test_data = {
        'A': ['2024-01-01'] * 76,
        'B': [f'ORDER{i:03d}' for i in range(76)],
        'C': ['홍길동'] * 76,
        'D': ['김철수'] * 76,
        'E': [f'브랜드{i%5} 상품명{i}' for i in range(76)],
        'F': ['빨강/M'] * 76,
        'G': [1] * 76,
        'H': [1000] * 76,
        'I': ['수령인'] * 76,
        'J': ['010-1234-5678'] * 76,
        'K': ['서울시 강남구 테헤란로'] * 76,
        'L': ['배송 메시지'] * 76
    }
    
    df = pd.DataFrame(test_data)
    print(f"테스트 데이터 생성: {len(df)}행")
    
    # BrandMatchingSystem 초기화
    try:
        system = BrandMatchingSystem()
        print("시스템 초기화 완료")
    except Exception as e:
        print(f"시스템 초기화 실패: {e}")
        return
    
    # 변환 테스트
    try:
        start_time = time.time()
        result = system.convert_sheet1_to_sheet2(df)
        elapsed = time.time() - start_time
        
        print(f"✅ 테스트 성공!")
        print(f"   입력: {len(df)}행")
        print(f"   출력: {len(result)}행")
        print(f"   소요시간: {elapsed:.2f}초")
        print(f"   컬럼 수: {len(result.columns)}")
        
        # 샘플 데이터 확인
        if not result.empty:
            print("\n샘플 결과:")
            print(f"   H열(브랜드): {result['H열(브랜드)'].iloc[0]}")
            print(f"   I열(상품명): {result['I열(상품명)'].iloc[0]}")
            print(f"   J열(색상): {result['J열(색상)'].iloc[0]}")
            print(f"   K열(사이즈): {result['K열(사이즈)'].iloc[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_convert() 