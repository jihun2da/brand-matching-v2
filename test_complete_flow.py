#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
완전한 매칭 플로우 테스트 (정확 매칭 + 유사도 매칭)
"""

import pandas as pd
import time
from brand_matching_system import BrandMatchingSystem

def test_complete_flow():
    print("=== 완전한 매칭 플로우 테스트 시작 ===")
    total_start = time.time()
    
    # 1. 테스트 데이터 생성 (다양한 케이스 포함)
    print("\n1. 테스트 데이터 생성 중...")
    test_data = {
        'A': ['2024-01-01'] * 20,  # 작은 데이터로 테스트
        'B': [f'ORDER{i:03d}' for i in range(20)],
        'C': ['홍길동'] * 20,
        'D': ['김철수'] * 20,
        'E': [  # 다양한 브랜드와 상품명 테스트 (정확히 20개)
            '소예 테리헤어밴드1', '린도 세일러린넨바디수트', '마마미 클래식썸머셔츠',
            '로다제이 코코넛슈트', '바비 래쉬가드', '보니토 래쉬가드스윔세트',
            '아르키드 슬립온', '미미앤루 티셔츠', '니니벨로 루비볼레로세트',
            '화이트스케치북 카고롱스커트', '키즈 래쉬가드', '여름 원피스',
            '아동 수영복', '유아 티셔츠', '베이비 반바지',
            '존재하지않는브랜드 상품1', '테스트브랜드 상품2', '가짜브랜드 상품3',
            '오류브랜드 상품4', '매칭실패 상품5'
        ],
        'F': ['빨강/S', '파랑/M', '노랑/L', '검정/XL'] * 5,
        'G': [1] * 20,
        'H': [1000] * 20,
        'I': ['수령인'] * 20,
        'J': ['010-1234-5678'] * 20,
        'K': ['서울시 강남구 테헤란로'] * 20,
        'L': ['배송 메시지'] * 20
    }
    
    df = pd.DataFrame(test_data)
    print(f"✅ 테스트 데이터 생성 완료: {len(df)}행")
    print(f"   - 실제 브랜드 상품: 15개")
    print(f"   - 매칭 실패 예상: 5개")
    
    # 2. 시스템 초기화
    print("\n2. 시스템 초기화 중...")
    try:
        system = BrandMatchingSystem()
        print(f"✅ 브랜드 데이터 로드: {len(system.brand_data):,}개")
        print(f"✅ 키워드 로드: {len(system.keyword_list)}개")
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Sheet1 -> Sheet2 변환 테스트
    print("\n3. 데이터 변환 테스트 중...")
    try:
        convert_start = time.time()
        sheet2_df = system.convert_sheet1_to_sheet2(df)
        convert_time = time.time() - convert_start
        
        print(f"✅ 변환 완료: {len(sheet2_df)}행, 소요시간: {convert_time:.2f}초")
        
        # 변환 결과 샘플 확인
        if not sheet2_df.empty:
            print(f"   샘플 브랜드: {sheet2_df['H열(브랜드)'].iloc[0]}")
            print(f"   샘플 상품명: {sheet2_df['I열(상품명)'].iloc[0]}")
        
    except Exception as e:
        print(f"❌ 변환 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 정확 매칭 테스트
    print("\n4. 정확 매칭 테스트 중...")
    try:
        exact_start = time.time()
        result_df, failed_products = system.process_matching(sheet2_df)
        exact_time = time.time() - exact_start
        
        matched_count = len(result_df[result_df['O열(도매가격)'] > 0]) if not result_df.empty else 0
        failed_count = len(failed_products)
        
        print(f"✅ 정확 매칭 완료!")
        print(f"   처리 시간: {exact_time:.2f}초")
        print(f"   총 행 수: {len(result_df)}")
        print(f"   매칭 성공: {matched_count}개")
        print(f"   매칭 실패: {failed_count}개")
        
        if matched_count > 0:
            sample = result_df[result_df['O열(도매가격)'] > 0].iloc[0]
            print(f"   샘플 매칭: {sample['H열(브랜드)']} - {sample['I열(상품명)']} -> {sample['O열(도매가격)']}원")
        
    except Exception as e:
        print(f"❌ 정확 매칭 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 유사도 매칭 테스트 (핵심!)
    print(f"\n5. 유사도 매칭 테스트 중... ({failed_count}개 실패 상품)")
    if failed_products:
        try:
            similarity_start = time.time()
            similarity_df = system.find_similar_products_for_failed_matches(failed_products)
            similarity_time = time.time() - similarity_start
            
            successful_similarity = len(similarity_df[similarity_df['매칭_상태'] == '유사매칭']) if not similarity_df.empty else 0
            failed_similarity = len(similarity_df[similarity_df['매칭_상태'] == '매칭실패']) if not similarity_df.empty else 0
            
            print(f"✅ 유사도 매칭 완료!")
            print(f"   처리 시간: {similarity_time:.2f}초")
            print(f"   총 결과: {len(similarity_df)}개")
            print(f"   유사매칭 성공: {successful_similarity}개")
            print(f"   완전 매칭 실패: {failed_similarity}개")
            
            if successful_similarity > 0:
                sample = similarity_df[similarity_df['매칭_상태'] == '유사매칭'].iloc[0]
                print(f"   샘플 유사매칭: {sample['원본_브랜드']} {sample['원본_상품명']} -> {sample['유사상품_브랜드']} {sample['유사상품_상품명']} (유사도: {sample['종합_유사도']})")
            
        except Exception as e:
            print(f"❌ 유사도 매칭 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("   모든 상품이 정확 매칭되어 유사도 매칭이 불필요합니다.")
    
    # 6. 전체 결과 요약
    total_time = time.time() - total_start
    print(f"\n=== 전체 테스트 완료 ===")
    print(f"총 소요시간: {total_time:.2f}초")
    print(f"  - 변환: {convert_time:.2f}초")
    print(f"  - 정확 매칭: {exact_time:.2f}초")
    if failed_products:
        print(f"  - 유사도 매칭: {similarity_time:.2f}초")
    
    print(f"\n📊 최종 결과:")
    print(f"  - 입력 상품: {len(df)}개")
    print(f"  - 정확 매칭: {matched_count}개")
    if failed_products:
        print(f"  - 유사도 매칭: {successful_similarity}개")
        print(f"  - 완전 실패: {failed_similarity}개")
    
    total_matched = matched_count + (successful_similarity if failed_products else 0)
    success_rate = (total_matched / len(df)) * 100
    print(f"  - 전체 성공률: {success_rate:.1f}%")
    
    print(f"상태: ✅ 성공")
    return True

def test_edge_cases():
    """엣지 케이스 테스트"""
    print("\n=== 엣지 케이스 테스트 ===")
    
    # 빈 데이터 테스트
    print("1. 빈 데이터 테스트...")
    try:
        system = BrandMatchingSystem()
        empty_df = pd.DataFrame()
        result = system.convert_sheet1_to_sheet2(empty_df)
        print(f"✅ 빈 데이터 처리 성공: {len(result)}행")
    except Exception as e:
        print(f"❌ 빈 데이터 처리 실패: {e}")
        return False
    
    # 큰 데이터 테스트 (100개)
    print("2. 대용량 데이터 테스트 (100개)...")
    try:
        large_data = {
            'A': ['2024-01-01'] * 100,
            'B': [f'ORDER{i:03d}' for i in range(100)],
            'C': ['홍길동'] * 100,
            'D': ['김철수'] * 100,
            'E': [f'소예 테리헤어밴드{i}' for i in range(100)],
            'F': ['빨강/S'] * 100,
            'G': [1] * 100,
            'H': [1000] * 100,
            'I': ['수령인'] * 100,
            'J': ['010-1234-5678'] * 100,
            'K': ['서울시 강남구 테헤란로'] * 100,
            'L': ['배송 메시지'] * 100
        }
        
        large_df = pd.DataFrame(large_data)
        start_time = time.time()
        
        # 변환
        sheet2_df = system.convert_sheet1_to_sheet2(large_df)
        
        # 정확 매칭
        result_df, failed_products = system.process_matching(sheet2_df)
        
        # 유사도 매칭 (실패한 것만)
        if failed_products:
            similarity_df = system.find_similar_products_for_failed_matches(failed_products)
        
        elapsed = time.time() - start_time
        print(f"✅ 대용량 데이터 처리 성공: {len(large_df)}개 - 소요시간: {elapsed:.2f}초")
        
    except Exception as e:
        print(f"❌ 대용량 데이터 처리 실패: {e}")
        return False
    
    print("✅ 모든 엣지 케이스 테스트 통과!")
    return True

if __name__ == "__main__":
    try:
        # 기본 플로우 테스트
        success1 = test_complete_flow()
        
        # 엣지 케이스 테스트
        success2 = test_edge_cases()
        
        if success1 and success2:
            print("\n🎉 모든 테스트 통과! 시스템이 정상 작동합니다!")
        else:
            print("\n💥 일부 테스트 실패!")
            
    except Exception as e:
        print(f"\n💥 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc() 