#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
0730 베베쭈나 파일 상세 분석
"""

import pandas as pd
from brand_matching_system import BrandMatchingSystem

def analyze_bebecuna_file():
    """0730 베베쭈나 파일의 실제 데이터 분석"""
    print("=== 0730 베베쭈나 파일 상세 분석 ===")
    
    try:
        # 엑셀 파일 로드
        df = pd.read_excel('0730 베베쭈나.xlsx')
        print(f"파일 로드 완료: {len(df)}개 행")
        
        print("\n전체 컬럼명:")
        for i, col in enumerate(df.columns):
            print(f"  {i}: {col}")
        
        # F열 (옵션) 데이터 상세 분석
        option_col_index = 5  # F열 (0부터 시작하므로 5)
        if len(df.columns) > option_col_index:
            print(f"\nF열 ({df.columns[option_col_index]}) 전체 데이터:")
            option_data = df.iloc[:, option_col_index].dropna()
            
            for i, value in enumerate(option_data):
                print(f"  행 {i+1}: '{value}' (타입: {type(value)})")
                
                # 현재 파싱 결과 확인
                matching_system = BrandMatchingSystem()
                color, size = matching_system.parse_options(str(value))
                print(f"    -> 파싱 결과: 색상='{color}', 사이즈='{size}'")
                
                if not color and not size:
                    print(f"    ❌ 파싱 실패!")
                elif not color:
                    print(f"    ⚠️ 색상 파싱 실패!")
                elif not size:
                    print(f"    ⚠️ 사이즈 파싱 실패!")
                else:
                    print(f"    ✅ 성공!")
                print()
        
        # 전체 프로세스 테스트
        print(f"\n{'='*60}")
        print("전체 변환 프로세스 테스트")
        print(f"{'='*60}")
        
        matching_system = BrandMatchingSystem()
        result_df = matching_system.convert_sheet1_to_sheet2(df)
        
        print(f"변환 결과: {len(result_df)}개 행")
        
        # J열(색상), K열(사이즈) 결과 확인
        if 'J열(색상)' in result_df.columns and 'K열(사이즈)' in result_df.columns:
            print(f"\n변환 결과 - 색상/사이즈:")
            
            color_success = 0
            size_success = 0
            
            for i, row in result_df.iterrows():
                color = row['J열(색상)']
                size = row['K열(사이즈)']
                product = row.get('I열(상품명)', '')
                
                if color and str(color).strip():
                    color_success += 1
                if size and str(size).strip():
                    size_success += 1
                
                print(f"  행 {i+1}: 상품='{product}', 색상='{color}', 사이즈='{size}'")
            
            print(f"\n최종 결과:")
            print(f"  색상 성공: {color_success}/{len(result_df)} ({color_success/len(result_df)*100:.1f}%)")
            print(f"  사이즈 성공: {size_success}/{len(result_df)} ({size_success/len(result_df)*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

def test_manual_patterns():
    """수동으로 다양한 패턴 테스트"""
    print(f"\n{'='*60}")
    print("수동 패턴 테스트")
    print(f"{'='*60}")
    
    matching_system = BrandMatchingSystem()
    
    # 실제 베베쭈나 파일에서 나올 수 있는 패턴들
    manual_patterns = [
        '색상=올리브, 사이즈=XL',
        '색상: 네이비 / 사이즈: free',
        '컬러: 화이트 / 사이즈: 13',
        'Color: 블루 / Size: XL',
        '올리브/XL',
        '네이비-FREE',
        '화이트 M',
        '블루 13',
        '색상 올리브 사이즈 XL',
        '컬러 네이비 사이즈 FREE',
    ]
    
    for pattern in manual_patterns:
        color, size = matching_system.parse_options(pattern)
        status = "✅" if (color or size) else "❌"
        print(f"{status} '{pattern}' -> 색상='{color}', 사이즈='{size}'")

if __name__ == "__main__":
    analyze_bebecuna_file()
    test_manual_patterns() 