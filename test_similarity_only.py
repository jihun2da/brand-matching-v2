#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유사도 매칭만 빠른 테스트
"""

import time
from brand_matching_system import BrandMatchingSystem

def test_similarity_only():
    print("=== 유사도 매칭만 빠른 테스트 ===")
    
    # 시스템 초기화
    system = BrandMatchingSystem()
    print(f"브랜드 데이터: {len(system.brand_data):,}개")
    
    # 매칭 실패한 상품들 시뮬레이션 (3개만)
    failed_products = [
        {
            '브랜드': '소예',
            '상품명': '클래식무발타이즈_테스트',  # 약간 다른 이름
            '색상': '그레이',
            '사이즈': 's',
            '행번호': 0
        },
        {
            '브랜드': '아이아이',
            '상품명': '루나벨드레스_변형',  # 약간 다른 이름
            '색상': '퍼플',
            '사이즈': '100',
            '행번호': 1
        },
        {
            '브랜드': '존재하지않는브랜드',  # 완전히 없는 브랜드
            '상품명': '없는상품',
            '색상': '빨강',
            '사이즈': 'm',
            '행번호': 2
        }
    ]
    
    print(f"\n매칭 실패 상품 {len(failed_products)}개로 유사도 매칭 테스트")
    
    start_time = time.time()
    try:
        result_df = system.find_similar_products_for_failed_matches(failed_products)
        elapsed = time.time() - start_time
        
        print(f"✅ 유사도 매칭 완료!")
        print(f"   소요시간: {elapsed:.2f}초")
        print(f"   결과: {len(result_df)}개")
        
        if not result_df.empty:
            successful = len(result_df[result_df['매칭_상태'] == '유사매칭'])
            failed = len(result_df[result_df['매칭_상태'] == '매칭실패'])
            print(f"   유사매칭 성공: {successful}개")
            print(f"   완전 실패: {failed}개")
            
            # 성공 샘플 표시
            if successful > 0:
                success_sample = result_df[result_df['매칭_상태'] == '유사매칭'].iloc[0]
                print(f"   성공 샘플: {success_sample['원본_브랜드']} {success_sample['원본_상품명']} -> {success_sample['유사상품_브랜드']} {success_sample['유사상품_상품명']} (유사도: {success_sample['종합_유사도']})")
        
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 유사도 매칭 실패: {e}")
        print(f"   소요시간: {elapsed:.2f}초")
        return False

if __name__ == "__main__":
    success = test_similarity_only()
    if success:
        print("\n🎉 유사도 매칭 테스트 성공!")
    else:
        print("\n�� 유사도 매칭 테스트 실패!") 