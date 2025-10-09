#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브랜드 매칭 로컬 실행 앱
로컬에서 GUI 없이 실행 가능한 버전
"""

import pandas as pd
import os
import sys
from datetime import datetime
import logging

# 최적화된 매칭 시스템 import
from brand_matching_system import BrandMatchingSystem
from file_processor import BrandFileProcessor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('brand_matching.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class BrandMatchingLocalApp:
    """브랜드 매칭 로컬 실행 앱"""
    
    def __init__(self):
        logger.info("="*60)
        logger.info("브랜드 매칭 로컬 앱 시작")
        logger.info("="*60)
        
        self.matching_system = BrandMatchingSystem()
        self.file_processor = BrandFileProcessor()
        
        # 결과 디렉토리 생성
        self.results_dir = "results"
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
    
    def print_menu(self):
        """메뉴 출력"""
        print("\n" + "="*60)
        print("🔗 브랜드 매칭 시스템 (로컬 버전)")
        print("="*60)
        print("1. 엑셀 파일 매칭 처리")
        print("2. 브랜드 데이터 새로고침")
        print("3. 키워드 관리")
        print("4. 시스템 정보 확인")
        print("5. 종료")
        print("="*60)
    
    def get_user_choice(self) -> str:
        """사용자 선택 입력"""
        while True:
            choice = input("\n선택하세요 (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            print("❌ 잘못된 입력입니다. 1-5 사이의 숫자를 입력하세요.")
    
    def process_excel_file(self):
        """엑셀 파일 매칭 처리"""
        print("\n" + "-"*60)
        print("📁 엑셀 파일 매칭 처리")
        print("-"*60)
        
        # 파일 경로 입력
        print("\n처리할 엑셀 파일 경로를 입력하세요:")
        print("예) C:/wepapp/brand-matching2/모나마켓250930.xlsx")
        print("또는 현재 디렉토리의 파일명만 입력: 모나마켓250930.xlsx")
        
        file_path = input("\n파일 경로: ").strip().strip('"').strip("'")
        
        if not os.path.exists(file_path):
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
            return
        
        try:
            print(f"\n✅ 파일 읽는 중: {file_path}")
            
            # 1단계: 파일 읽기
            df = self.file_processor.read_excel_file(file_path)
            print(f"📊 총 {len(df):,}개 행을 읽었습니다.")
            
            # 2단계: Sheet2 형식으로 변환
            print("\n🔄 데이터 변환 중...")
            sheet2_df = self.matching_system.convert_sheet1_to_sheet2(df)
            print(f"✅ {len(sheet2_df):,}개 행으로 변환 완료")
            
            # 3단계: 정확 매칭
            print("\n🎯 정확 매칭 수행 중...")
            result_df, failed_products = self.matching_system.process_matching(sheet2_df)
            
            matched_count = len(result_df[pd.to_numeric(result_df['O열(도매가격)'], errors='coerce') > 0])
            print(f"✅ 정확 매칭 완료: {matched_count:,}/{len(result_df):,}개 ({matched_count/len(result_df)*100:.1f}%)")
            
            # 4단계: 유사도 매칭 (선택)
            similarity_df = pd.DataFrame()
            if failed_products:
                print(f"\n🔍 매칭 실패한 {len(failed_products):,}개 상품에 대해 유사도 매칭을 수행하시겠습니까?")
                choice = input("유사도 매칭 수행 (y/n): ").strip().lower()
                
                if choice == 'y':
                    print("🔍 유사도 매칭 수행 중...")
                    similarity_df = self.matching_system.find_similar_products_for_failed_matches(failed_products)
                    similarity_matched = len(similarity_df[similarity_df['매칭_상태'] == '유사매칭'])
                    print(f"✅ 유사도 매칭 완료: {similarity_matched:,}/{len(similarity_df):,}개")
            
            # 5단계: 결과 저장
            print("\n💾 결과 파일 저장 중...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 정확 매칭 결과 저장
            exact_filename = os.path.join(self.results_dir, f"정확매칭결과_{timestamp}.xlsx")
            result_df.to_excel(exact_filename, index=False, engine='openpyxl')
            print(f"✅ 정확 매칭 결과 저장: {exact_filename}")
            
            # 유사도 매칭 결과 저장 (있는 경우)
            if not similarity_df.empty:
                similarity_filename = os.path.join(self.results_dir, f"유사도매칭결과_{timestamp}.xlsx")
                similarity_df.to_excel(similarity_filename, index=False, engine='openpyxl')
                print(f"✅ 유사도 매칭 결과 저장: {similarity_filename}")
            
            # 통합 결과 저장
            combined_filename = os.path.join(self.results_dir, f"브랜드매칭_통합결과_{timestamp}.xlsx")
            with pd.ExcelWriter(combined_filename, engine='openpyxl') as writer:
                result_df.to_excel(writer, sheet_name='정확매칭', index=False)
                if not similarity_df.empty:
                    similarity_df.to_excel(writer, sheet_name='유사도매칭', index=False)
            print(f"✅ 통합 결과 저장: {combined_filename}")
            
            # 결과 요약
            print("\n" + "="*60)
            print("📊 매칭 결과 요약")
            print("="*60)
            print(f"총 상품 수: {len(result_df):,}개")
            print(f"정확 매칭 성공: {matched_count:,}개 ({matched_count/len(result_df)*100:.1f}%)")
            if not similarity_df.empty:
                similarity_matched = len(similarity_df[similarity_df['매칭_상태'] == '유사매칭'])
                print(f"유사도 매칭 성공: {similarity_matched:,}개")
                print(f"전체 매칭 성공: {matched_count + similarity_matched:,}개 ({(matched_count + similarity_matched)/len(result_df)*100:.1f}%)")
            print("="*60)
            
            print("\n✅ 모든 처리가 완료되었습니다!")
            
        except Exception as e:
            logger.error(f"파일 처리 중 오류 발생: {e}", exc_info=True)
            print(f"\n❌ 오류 발생: {e}")
    
    def refresh_brand_data(self):
        """브랜드 데이터 새로고침"""
        print("\n" + "-"*60)
        print("🔄 브랜드 데이터 새로고침")
        print("-"*60)
        
        try:
            print("\n브랜드 데이터를 Google Sheets에서 다시 로드합니다...")
            self.matching_system.load_brand_data()
            
            if self.matching_system.brand_data is not None:
                print(f"✅ 브랜드 데이터 로드 완료: {len(self.matching_system.brand_data):,}개 상품")
                print(f"✅ 브랜드 인덱스 구축 완료: {len(self.matching_system.brand_index):,}개 브랜드")
            else:
                print("❌ 브랜드 데이터 로드 실패")
        except Exception as e:
            logger.error(f"브랜드 데이터 새로고침 중 오류: {e}", exc_info=True)
            print(f"❌ 오류 발생: {e}")
    
    def manage_keywords(self):
        """키워드 관리"""
        while True:
            print("\n" + "-"*60)
            print("🔧 키워드 관리")
            print("-"*60)
            print(f"현재 키워드 수: {len(self.matching_system.keyword_list)}개")
            print()
            print("1. 키워드 목록 보기")
            print("2. 키워드 추가")
            print("3. 키워드 삭제")
            print("4. 뒤로 가기")
            print("-"*60)
            
            choice = input("\n선택하세요 (1-4): ").strip()
            
            if choice == '1':
                self.show_keywords()
            elif choice == '2':
                self.add_keyword()
            elif choice == '3':
                self.remove_keyword()
            elif choice == '4':
                break
            else:
                print("❌ 잘못된 입력입니다.")
    
    def show_keywords(self):
        """키워드 목록 보기"""
        print("\n📋 키워드 목록")
        print("-"*60)
        
        star_keywords = [kw for kw in self.matching_system.keyword_list if kw.startswith('*') and kw.endswith('*')]
        regular_keywords = [kw for kw in self.matching_system.keyword_list if not (kw.startswith('*') and kw.endswith('*'))]
        
        print(f"\n⭐ 특수 패턴 키워드 ({len(star_keywords)}개):")
        for i, kw in enumerate(star_keywords, 1):
            print(f"  {i}. {kw}")
        
        print(f"\n일반 키워드 ({len(regular_keywords)}개):")
        for i, kw in enumerate(regular_keywords[:20], 1):
            print(f"  {i}. {kw}")
        if len(regular_keywords) > 20:
            print(f"  ... 외 {len(regular_keywords) - 20}개")
    
    def add_keyword(self):
        """키워드 추가"""
        print("\n➕ 키워드 추가")
        keyword = input("추가할 키워드를 입력하세요: ").strip()
        
        if not keyword:
            print("❌ 키워드를 입력해주세요.")
            return
        
        if keyword in self.matching_system.keyword_list:
            print(f"⚠️ 키워드 '{keyword}'는 이미 존재합니다.")
            return
        
        if self.matching_system.add_keyword(keyword):
            print(f"✅ 키워드 '{keyword}'가 추가되었습니다.")
        else:
            print(f"❌ 키워드 추가에 실패했습니다.")
    
    def remove_keyword(self):
        """키워드 삭제"""
        print("\n➖ 키워드 삭제")
        keyword = input("삭제할 키워드를 입력하세요: ").strip()
        
        if not keyword:
            print("❌ 키워드를 입력해주세요.")
            return
        
        if keyword not in self.matching_system.keyword_list:
            print(f"⚠️ 키워드 '{keyword}'가 존재하지 않습니다.")
            return
        
        if self.matching_system.remove_keyword(keyword):
            print(f"✅ 키워드 '{keyword}'가 삭제되었습니다.")
        else:
            print(f"❌ 키워드 삭제에 실패했습니다.")
    
    def show_system_info(self):
        """시스템 정보 확인"""
        print("\n" + "-"*60)
        print("ℹ️ 시스템 정보")
        print("-"*60)
        
        # 브랜드 데이터 정보
        if self.matching_system.brand_data is not None:
            print(f"\n📊 브랜드 데이터:")
            print(f"  - 상품 수: {len(self.matching_system.brand_data):,}개")
            print(f"  - 브랜드 수: {len(self.matching_system.brand_index):,}개")
            
            # 브랜드별 상품 수 Top 10
            brand_counts = {}
            for idx, row in self.matching_system.brand_data.iterrows():
                brand = str(row['브랜드']).strip()
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            print(f"\n  상위 10개 브랜드:")
            for i, (brand, count) in enumerate(sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:10], 1):
                print(f"    {i}. {brand}: {count:,}개")
        else:
            print("\n📊 브랜드 데이터: ❌ 로드되지 않음")
        
        # 키워드 정보
        print(f"\n🔧 키워드:")
        print(f"  - 전체 키워드 수: {len(self.matching_system.keyword_list)}개")
        star_keywords = [kw for kw in self.matching_system.keyword_list if kw.startswith('*') and kw.endswith('*')]
        print(f"  - 특수 패턴 키워드: {len(star_keywords)}개")
        print(f"  - 일반 키워드: {len(self.matching_system.keyword_list) - len(star_keywords)}개")
        
        # 캐시 정보
        print(f"\n💾 캐시:")
        print(f"  - 정규화 캐시 크기: {len(self.matching_system._normalized_cache):,}개")
        
        # 파일 정보
        print(f"\n📁 결과 파일:")
        if os.path.exists(self.results_dir):
            result_files = [f for f in os.listdir(self.results_dir) if f.endswith('.xlsx')]
            print(f"  - 저장된 결과 파일: {len(result_files)}개")
        else:
            print(f"  - 결과 디렉토리: 없음")
        
        print("-"*60)
    
    def run(self):
        """앱 실행"""
        while True:
            self.print_menu()
            choice = self.get_user_choice()
            
            if choice == '1':
                self.process_excel_file()
            elif choice == '2':
                self.refresh_brand_data()
            elif choice == '3':
                self.manage_keywords()
            elif choice == '4':
                self.show_system_info()
            elif choice == '5':
                print("\n👋 브랜드 매칭 시스템을 종료합니다.")
                print("감사합니다!\n")
                break


def main():
    """메인 함수"""
    try:
        app = BrandMatchingLocalApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
        print("👋 브랜드 매칭 시스템을 종료합니다.\n")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}", exc_info=True)
        print(f"\n❌ 오류 발생: {e}")
        print("로그 파일(brand_matching.log)을 확인해주세요.\n")


if __name__ == "__main__":
    main()

