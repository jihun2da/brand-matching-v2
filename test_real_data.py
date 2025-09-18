#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 브랜드 데이터로 완전한 매칭 테스트
"""

import pandas as pd
import time
from brand_matching_system import BrandMatchingSystem

def test_with_real_data():
    print("=== 실제 브랜드 데이터로 완전한 매칭 테스트 ===")
    total_start = time.time()
    
    # 1. 시스템 초기화
    print("\n1. 시스템 초기화 중...")
    system = BrandMatchingSystem()
    print(f"✅ 브랜드 데이터 로드: {len(system.brand_data):,}개")
    
    # 2. 실제 존재하는 브랜드들로 테스트 데이터 생성
    print("\n2. 실제 브랜드 데이터로 테스트 데이터 생성...")
    test_data = {
        'A': ['2024-01-01'] * 20,
        'B': [f'ORDER{i:03d}' for i in range(20)],
        'C': ['홍길동'] * 20,
        'D': ['김철수'] * 20,
        'E': [  # 실제 존재하는 브랜드들로 변경
            '소예 클래식무발타이즈', '린도 B프릴귀달이보넷', '마마미 톡톡티',
            '로다제이 루피반집업', '보니토 피그먼트캡모자', '니니벨로 기획어텀베이직티',
            '화이트스케치북 뉴페이크반폴라', '아이아이 루나벨드레스', '엠키즈 상품1',
            '오뜨베베 상품2', '레브베베 상품3', '리틀래빗 상품4',
            '미소 상품5', '로아 상품6', '데일리샵 상품7',
            '마이베베 상품8', '어썸베베 상품9', '더베이지 상품10',
            '미미상회 상품11', '하로하로 상품12'
        ],
        'F': ['그레이/S', '핑크/M', '아이/L', '블랙/XL'] * 5,
        'G': [1] * 20,
        'H': [1000] * 20,
        'I': ['수령인'] * 20,
        'J': ['010-1234-5678'] * 20,
        'K': ['서울시 강남구 테헤란로'] * 20,
        'L': ['배송 메시지'] * 20
    }
    
    df = pd.DataFrame(test_data)
    print(f"✅ 테스트 데이터 생성 완료: {len(df)}행")
    print(f"   - 모두 실제 존재하는 브랜드들")
    
    # 3. Sheet1 -> Sheet2 변환
    print("\n3. 데이터 변환 중...")
    convert_start = time.time()
    sheet2_df = system.convert_sheet1_to_sheet2(df)
    convert_time = time.time() - convert_start
    
    print(f"✅ 변환 완료: {len(sheet2_df)}행, 소요시간: {convert_time:.2f}초")
    
    # 변환 결과 확인
    if not sheet2_df.empty:
        print(f"   첫 번째 변환 결과:")
        print(f"     브랜드: {sheet2_df['H열(브랜드)'].iloc[0]}")
        print(f"     상품명: {sheet2_df['I열(상품명)'].iloc[0]}")
        print(f"     색상: {sheet2_df['J열(색상)'].iloc[0]}")
        print(f"     사이즈: {sheet2_df['K열(사이즈)'].iloc[0]}")
    
    # 4. 정확 매칭
    print("\n4. 정확 매칭 중...")
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
    
    # 성공한 매칭 샘플 표시
    if matched_count > 0:
        success_samples = result_df[result_df['O열(도매가격)'] > 0].head(3)
        print(f"   매칭 성공 샘플:")
        for i, (_, row) in enumerate(success_samples.iterrows()):
            print(f"     {i+1}. {row['H열(브랜드)']} - {row['I열(상품명)']} -> {row['O열(도매가격)']}원")
    
    # 실패한 매칭 샘플 표시
    if failed_count > 0:
        print(f"   매칭 실패 샘플 (상위 3개):")
        for i, failed in enumerate(failed_products[:3]):
            print(f"     {i+1}. {failed.get('브랜드', '')} - {failed.get('상품명', '')}")
    
    # 5. 유사도 매칭 (실패한 것들만)
    similarity_df = pd.DataFrame()
    if failed_products:
        print(f"\n5. 유사도 매칭 중... ({failed_count}개 실패 상품)")
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
        
        # 유사도 매칭 성공 샘플 표시
        if successful_similarity > 0:
            similarity_samples = similarity_df[similarity_df['매칭_상태'] == '유사매칭'].head(3)
            print(f"   유사매칭 성공 샘플:")
            for i, (_, row) in enumerate(similarity_samples.iterrows()):
                print(f"     {i+1}. {row['원본_브랜드']} {row['원본_상품명']} -> {row['유사상품_브랜드']} {row['유사상품_상품명']} (유사도: {row['종합_유사도']})")
    
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
        successful_similarity = len(similarity_df[similarity_df['매칭_상태'] == '유사매칭']) if not similarity_df.empty else 0
        print(f"  - 유사도 매칭: {successful_similarity}개")
        print(f"  - 완전 실패: {failed_count - successful_similarity}개")
        total_matched = matched_count + successful_similarity
    else:
        total_matched = matched_count
    
    success_rate = (total_matched / len(df)) * 100
    print(f"  - 전체 성공률: {success_rate:.1f}%")
    
    if matched_count >= 15:  # 20개 중 15개 이상 정확 매칭 기대
        print(f"🎉 테스트 성공! 정확 매칭률이 우수합니다!")
        return True
    elif total_matched >= 15:  # 유사도 매칭까지 포함해서 15개 이상
        print(f"✅ 테스트 통과! 전체 매칭률이 양호합니다!")
        return True
    else:
        print(f"⚠️  매칭률이 예상보다 낮습니다.")
        return False

if __name__ == "__main__":
    try:
        success = test_with_real_data()
        if success:
            print("\n🎉 실제 데이터 테스트 성공!")
        else:
            print("\n💥 실제 데이터 테스트 개선 필요!")
            
    except Exception as e:
        print(f"\n💥 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc() 