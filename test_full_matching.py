#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전체 매칭 플로우 테스트
"""

import pandas as pd
import time
from brand_matching_system import BrandMatchingSystem

def test_full_matching():
    print("=== 전체 매칭 플로우 테스트 시작 ===")
    
    # 1. 테스트 데이터 생성 (실제 업로드 파일과 유사하게)
    print("\n1. 테스트 데이터 생성 중...")
    test_data = {
        'A': ['2024-01-01'] * 76,  # 실제 사용자 데이터와 동일한 크기
        'B': [f'ORDER{i:03d}' for i in range(76)],
        'C': ['홍길동'] * 76,
        'D': ['김철수'] * 76,
        'E': [f'소예 테리헤어밴드{i}' for i in range(76)],  # 실제 브랜드명 사용
        'F': ['빨강/S'] * 76,
        'G': [1] * 76,
        'H': [1000] * 76,
        'I': ['수령인'] * 76,
        'J': ['010-1234-5678'] * 76,
        'K': ['서울시 강남구 테헤란로'] * 76,
        'L': ['배송 메시지'] * 76
    }
    
    df = pd.DataFrame(test_data)
    print(f"✅ 테스트 데이터 생성 완료: {len(df)}행")
    
    # 2. 시스템 초기화
    print("\n2. 시스템 초기화 중...")
    try:
        system = BrandMatchingSystem()
        print(f"✅ 브랜드 데이터 로드: {len(system.brand_data)}개")
        print(f"✅ 키워드 로드: {len(system.keyword_list)}개")
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {e}")
        return False
    
    # 3. Sheet1 -> Sheet2 변환 테스트
    print("\n3. 데이터 변환 테스트 중...")
    try:
        start_time = time.time()
        sheet2_df = system.convert_sheet1_to_sheet2(df)
        convert_time = time.time() - start_time
        
        print(f"✅ 변환 완료: {len(sheet2_df)}행, 소요시간: {convert_time:.2f}초")
        
        # 변환 결과 확인
        if not sheet2_df.empty:
            print(f"   샘플 브랜드: {sheet2_df['H열(브랜드)'].iloc[0]}")
            print(f"   샘플 상품명: {sheet2_df['I열(상품명)'].iloc[0]}")
        
    except Exception as e:
        print(f"❌ 변환 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 정확 매칭 테스트 (핵심 부분)
    print("\n4. 정확 매칭 테스트 중...")
    try:
        start_time = time.time()
        
        # 간단한 타임아웃 체크
        try:
            result_df, failed_products = system.process_matching(sheet2_df)
            
            match_time = time.time() - start_time
            
            print(f"✅ 정확 매칭 완료!")
            print(f"   처리 시간: {match_time:.2f}초")
            print(f"   총 행 수: {len(result_df)}")
            print(f"   매칭 실패: {len(failed_products)}개")
            
            # 매칭 결과 확인
            if not result_df.empty:
                matched_count = len(result_df[result_df['O열(도매가격)'] > 0])
                print(f"   매칭 성공: {matched_count}개")
                
                if matched_count > 0:
                    sample = result_df[result_df['O열(도매가격)'] > 0].iloc[0]
                    print(f"   샘플 매칭: {sample['H열(브랜드)']} - {sample['I열(상품명)']} -> {sample['O열(도매가격)']}원")
            
        except Exception as inner_e:
            print(f"❌ 매칭 처리 중 오류: {inner_e}")
            return False
            
    except Exception as e:
        print(f"❌ 정확 매칭 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 전체 테스트 완료
    total_time = time.time() - start_time + convert_time
    print(f"\n=== 전체 테스트 완료 ===")
    print(f"총 소요시간: {total_time:.2f}초")
    print(f"상태: ✅ 성공")
    
    return True

if __name__ == "__main__":
    try:
        success = test_full_matching()
        if success:
            print("\n🎉 모든 테스트 통과!")
        else:
            print("\n💥 테스트 실패!")
    except Exception as e:
        print(f"\n💥 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc() 