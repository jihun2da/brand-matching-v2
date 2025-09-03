import streamlit as st
import pandas as pd
import os
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(__file__))

from brand_matching_system import BrandMatchingSystem
from file_processor import BrandFileProcessor
import io

# 페이지 설정
st.set_page_config(
    page_title="브랜드 매칭 시스템",
    page_icon="🔗",
    layout="wide"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>🔗 브랜드 매칭 시스템</h1>
    <p>Excel 파일을 업로드하여 브랜드 상품을 자동으로 매칭하세요</p>
</div>
""", unsafe_allow_html=True)

# 초기화
@st.cache_resource
def init_system():
    """시스템 초기화 (캐시됨)"""
    try:
        matching_system = BrandMatchingSystem()
        file_processor = BrandFileProcessor()
        return matching_system, file_processor
    except Exception as e:
        st.error(f"시스템 초기화 중 오류 발생: {str(e)}")
        st.info("기본 모드로 실행합니다.")
        return None, None

def main():
    matching_system, file_processor = init_system()
    
    if matching_system is None or file_processor is None:
        st.error("🚨 시스템을 초기화할 수 없습니다.")
        st.markdown("""
        ### 💡 **해결 방법**
        1. 페이지를 새로고침해 보세요
        2. 몇 분 후 다시 시도해 보세요
        3. 문제가 지속되면 관리자에게 문의하세요
        """)
        return
    
    # 사이드바
    st.sidebar.title("📋 메뉴")
    menu = st.sidebar.selectbox(
        "작업 선택",
        ["매칭 처리", "키워드 관리", "시스템 정보", "사용법"]
    )
    
    if menu == "매칭 처리":
        show_matching_page(matching_system, file_processor)
    elif menu == "키워드 관리":
        show_keyword_management_page(matching_system)
    elif menu == "시스템 정보":
        show_info_page(matching_system)
    else:
        show_usage_page()

def show_matching_page(matching_system, file_processor):
    """매칭 처리 페이지"""
    
    # 두 개의 컬럼으로 나누기
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📁 파일 업로드")
        
        # 파일 업로드
        uploaded_files = st.file_uploader(
            "Excel 파일을 선택하세요 (여러 파일 가능)",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="브랜드 정보가 포함된 Excel 파일을 업로드하세요"
        )
        
        if uploaded_files:
            st.markdown("""
            <div class="success-box">
                <strong>✅ 파일 업로드 완료!</strong><br>
                총 <strong>{}</strong>개 파일이 선택되었습니다.
            </div>
            """.format(len(uploaded_files)), unsafe_allow_html=True)
            
            # 업로드된 파일 목록 표시
            st.markdown("#### 📋 선택된 파일 목록")
            for i, file in enumerate(uploaded_files, 1):
                file_size = f"{file.size:,} bytes" if file.size < 1024*1024 else f"{file.size/(1024*1024):.1f} MB"
                st.markdown(f"**{i}.** `{file.name}` ({file_size})")
            
            # 매칭 실행 버튼
            st.markdown("---")
            if st.button("🚀 매칭 시작", type="primary", use_container_width=True):
                process_matching(uploaded_files, matching_system, file_processor)
        else:
            st.markdown("""
            <div class="info-box">
                <strong>📤 파일을 업로드해주세요</strong><br>
                위의 업로드 영역을 클릭하거나 파일을 드래그해주세요.
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📊 시스템 현황")
        
        # 브랜드 데이터 정보와 새로고침 버튼
        brand_col1, brand_col2 = st.columns([2, 1])
        
        with brand_col1:
            if hasattr(matching_system, 'brand_data') and len(matching_system.brand_data) > 0:
                st.metric("🏷️ 브랜드 상품", f"{len(matching_system.brand_data):,}개")
            else:
                st.metric("🏷️ 브랜드 상품", "로드 실패")
        
        with brand_col2:
            if st.button("🔄", help="브랜드 데이터 새로고침", use_container_width=True):
                with st.spinner("업데이트 중..."):
                    try:
                        # 캐시 클리어 및 데이터 새로고침
                        st.cache_resource.clear()
                        matching_system.load_brand_data()
                        st.success("✅ 업데이트 완료!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 업데이트 실패: {str(e)}")
        
        # 키워드 정보
        if hasattr(matching_system, 'keyword_list') and matching_system.keyword_list:
            st.metric("🔍 제외 키워드", f"{len(matching_system.keyword_list)}개")
        
        # 마지막 업데이트 시간 표시
        from datetime import datetime
        update_time = datetime.now().strftime("%H:%M:%S")
        st.caption(f"마지막 확인: {update_time}")
        
        # 지원 형식 안내
        st.markdown("---")
        st.markdown("#### 📋 지원 형식")
        st.markdown("""
        - **파일 형식**: `.xlsx`, `.xls`
        - **최대 크기**: 50MB
        - **다중 선택**: 가능
        - **필수 컬럼**: 브랜드, 상품명
        """)
        
        # 매칭 규칙 안내
        st.markdown("#### 🎯 매칭 규칙")
        st.markdown("""
        1. 브랜드명 일치 확인
        2. 상품명 유사도 검사
        3. 사이즈/컬러 매칭
        4. 최적 점수 기반 선택
        """)
        
        # 빠른 액세스 버튼들
        st.markdown("---")
        st.markdown("#### ⚡ 빠른 액세스")
        
        quick_col1, quick_col2 = st.columns(2)
        with quick_col1:
            if st.button("📊 시스템 정보", use_container_width=True):
                st.info("💡 사이드바에서 '시스템 정보' 메뉴를 선택해주세요!")
        
        with quick_col2:
            if st.button("🔧 키워드 관리", use_container_width=True):
                st.info("💡 사이드바에서 '키워드 관리' 메뉴를 선택해주세요!")

def process_matching(uploaded_files, matching_system, file_processor):
    """매칭 처리 실행"""
    temp_files = []  # 스코프 문제 해결
    try:
        # 진행 상황 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 1단계: 파일 읽기
        status_text.text("📖 파일을 읽는 중...")
        progress_bar.progress(20)
        
        # 업로드된 파일들을 임시로 저장하고 처리
        for uploaded_file in uploaded_files:
            temp_path = f"temp_{uploaded_file.name.replace(' ', '_')}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            temp_files.append(temp_path)
        
        st.info(f"📁 {len(temp_files)}개 파일을 처리합니다.")
        
        # 2단계: 파일 결합
        status_text.text("🔗 파일을 결합하는 중...")
        progress_bar.progress(40)
        
        combined_df = file_processor.combine_excel_files(temp_files)
        st.info(f"📊 총 {len(combined_df)}개 행을 읽었습니다.")
        
        # 3단계: Sheet2 형식 변환
        status_text.text("📋 데이터를 변환하는 중...")
        progress_bar.progress(60)
        
        sheet2_df = matching_system.convert_sheet1_to_sheet2(combined_df)
        st.info(f"🔄 {len(sheet2_df)}개 행으로 변환했습니다.")
        
        # 4단계: 매칭 처리
        status_text.text("🎯 매칭을 수행하는 중...")
        progress_bar.progress(80)
        
        result_df = matching_system.process_matching(sheet2_df)
        
        # 5단계: 완료
        status_text.text("✅ 매칭 완료!")
        progress_bar.progress(100)
        
        # 결과 표시
        show_results(result_df)
        
        # 임시 파일 정리
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.error(f"🔍 상세 오류: {type(e).__name__}")
        
        # 디버깅 정보 표시
        if temp_files:
            st.warning(f"📂 임시 파일들: {temp_files}")
        
        # 임시 파일 정리
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

def show_results(result_df):
    """결과 표시 - KeyError 방지를 위한 안전한 처리"""
    try:
        # 완료 메시지
        st.markdown("""
        <div class="success-box">
            <h3>🎉 매칭이 완료되었습니다!</h3>
            <p>결과를 확인하고 Excel 파일을 다운로드하세요.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 통계 정보
        st.markdown("### 📊 매칭 결과 통계")
        col1, col2, col3, col4 = st.columns(4)
        
        # 매칭 성공/실패는 O열(도매가격)으로 판단 (안전한 컬럼 체크)
        if 'O열(도매가격)' in result_df.columns:
            # 도매가격이 0보다 크면 매칭 성공
            matched_count = len(result_df[pd.to_numeric(result_df['O열(도매가격)'], errors='coerce') > 0])
            unmatched_count = len(result_df[pd.to_numeric(result_df['O열(도매가격)'], errors='coerce') == 0])
        else:
            # 컬럼이 없으면 기본값 사용
            matched_count = 0
            unmatched_count = len(result_df)
        
        with col1:
            st.metric("📦 총 상품 수", f"{len(result_df):,}개")
        
        with col2:
            st.metric("✅ 매칭 성공", f"{matched_count:,}개", 
                     delta=f"{matched_count}개 매칭")
        
        with col3:
            st.metric("❌ 매칭 실패", f"{unmatched_count:,}개")
        
        with col4:
            if len(result_df) > 0:
                success_rate = (matched_count / len(result_df)) * 100
                st.metric("📈 성공률", f"{success_rate:.1f}%",
                         delta=f"{success_rate:.1f}%" if success_rate >= 80 else None)
        
        # 결과 미리보기
        st.markdown("---")
        st.markdown("### 📋 결과 미리보기 (상위 10개)")
        
        # 매칭 성공/실패별 필터
        tab1, tab2, tab3 = st.tabs(["🔍 전체", "✅ 매칭 성공", "❌ 매칭 실패"])
        
        with tab1:
            st.dataframe(result_df.head(10), use_container_width=True)
        
        with tab2:
            if 'O열(도매가격)' in result_df.columns:
                success_df = result_df[pd.to_numeric(result_df['O열(도매가격)'], errors='coerce') > 0]
                if len(success_df) > 0:
                    st.dataframe(success_df.head(10), use_container_width=True)
                else:
                    st.info("매칭 성공한 항목이 없습니다.")
            else:
                st.info("매칭 결과 컬럼을 찾을 수 없습니다.")
        
        with tab3:
            if 'O열(도매가격)' in result_df.columns:
                fail_df = result_df[pd.to_numeric(result_df['O열(도매가격)'], errors='coerce') == 0]
                if len(fail_df) > 0:
                    st.dataframe(fail_df.head(10), use_container_width=True)
                else:
                    st.info("매칭 실패한 항목이 없습니다.")
            else:
                st.info("매칭 결과 컬럼을 찾을 수 없습니다.")
        
        # 다운로드 섹션
        st.markdown("---")
        st.markdown("### 💾 결과 다운로드")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("""
            <div class="info-box">
                <strong>📁 Excel 파일로 저장</strong><br>
                매칭 결과를 Excel 파일로 다운로드할 수 있습니다.<br>
                파일명에는 현재 날짜와 시간이 포함됩니다.
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Excel 파일 생성
            excel_buffer = io.BytesIO()
            result_df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"브랜드매칭결과_{timestamp}.xlsx"
            
            st.download_button(
                label="📥 Excel 다운로드",
                data=excel_buffer.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"❌ 결과 표시 중 오류 발생: {str(e)}")
        st.error(f"🔍 상세 오류: {type(e).__name__}")
        
        # 기본 정보라도 표시
        st.info(f"📊 총 {len(result_df)}개 행이 처리되었습니다.")
        
        # 기본 다운로드 기능 제공
        try:
            excel_buffer = io.BytesIO()
            result_df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"브랜드매칭결과_{timestamp}.xlsx"
            
            st.download_button(
                label="📥 기본 Excel 다운로드",
                data=excel_buffer.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except:
            st.error("다운로드 기능도 사용할 수 없습니다.")
        
        # 데이터 확인용
        if not result_df.empty:
            st.markdown("### 📋 원본 데이터 (상위 5개)")
            st.dataframe(result_df.head(5), use_container_width=True)

def show_info_page(matching_system):
    """시스템 정보 페이지"""
    st.header("ℹ️ 시스템 정보")
    
    # 브랜드 데이터 새로고침 버튼 (상단에 배치)
    col_refresh1, col_refresh2, col_refresh3 = st.columns([1, 2, 1])
    with col_refresh2:
        if st.button("🔄 브랜드 데이터 새로고침", type="primary", use_container_width=True):
            with st.spinner("브랜드 데이터를 업데이트하는 중..."):
                try:
                    # 캐시 클리어
                    st.cache_resource.clear()
                    
                    # 브랜드 데이터 다시 로드
                    matching_system.load_brand_data()
                    
                    st.success("✅ 브랜드 데이터가 성공적으로 업데이트되었습니다!")
                    st.info(f"📊 현재 브랜드 상품 수: {len(matching_system.brand_data):,}개")
                    
                    # 잠시 후 페이지 새로고침
                    import time
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 브랜드 데이터 업데이트 중 오류 발생: {str(e)}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 브랜드 데이터")
        if hasattr(matching_system, 'brand_data') and len(matching_system.brand_data) > 0:
            # 브랜드 상품 수와 마지막 업데이트 시간 표시
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            col_metric1, col_metric2 = st.columns(2)
            with col_metric1:
                st.metric("브랜드 상품 수", f"{len(matching_system.brand_data):,}개")
            with col_metric2:
                st.metric("마지막 확인", current_time)
            
            # 브랜드별 통계
            if len(matching_system.brand_data) > 0:
                brands = {}
                for _, item in matching_system.brand_data.iterrows():
                    brand = item.get('브랜드', 'Unknown')
                    brands[brand] = brands.get(brand, 0) + 1
                
                st.subheader("🏷️ 브랜드별 상품 수")
                brand_df = pd.DataFrame(list(brands.items()), columns=['브랜드', '상품수'])
                brand_df = brand_df.sort_values('상품수', ascending=False).head(10)
                st.dataframe(brand_df, use_container_width=True)
                
                # 총 브랜드 수 표시
                st.info(f"📈 총 **{len(brands)}개** 브랜드의 상품을 관리 중입니다.")
        else:
            st.warning("브랜드 데이터를 로드할 수 없습니다.")
            st.info("위의 '🔄 브랜드 데이터 새로고침' 버튼을 클릭해보세요.")
    
    with col2:
        st.subheader("🔧 키워드 정보")
        if hasattr(matching_system, 'keyword_list') and matching_system.keyword_list:
            st.metric("제외 키워드 수", f"{len(matching_system.keyword_list)}개")
            
            # 키워드 목록 표시
            keywords_text = ", ".join(matching_system.keyword_list[:20])
            if len(matching_system.keyword_list) > 20:
                keywords_text += f" ... (총 {len(matching_system.keyword_list)}개)"
            st.text_area("키워드 목록 (상위 20개)", keywords_text, height=100)
            
            # 키워드 관리 페이지로 이동 버튼
            if st.button("⚙️ 키워드 관리하기", use_container_width=True):
                st.info("💡 사이드바에서 '키워드 관리' 메뉴를 선택해주세요!")
        else:
            st.warning("키워드 데이터를 로드할 수 없습니다.")
    
    # 시스템 상태 정보
    st.markdown("---")
    st.subheader("🖥️ 시스템 상태")
    
    col_status1, col_status2, col_status3 = st.columns(3)
    
    with col_status1:
        # Google Sheets 연결 상태
        try:
            if hasattr(matching_system, 'brand_data') and len(matching_system.brand_data) > 0:
                st.success("🟢 Google Sheets 연결됨")
            else:
                st.error("🔴 Google Sheets 연결 실패")
        except:
            st.error("🔴 Google Sheets 연결 실패")
    
    with col_status2:
        # 키워드 파일 상태
        import os
        if os.path.exists("keywords.xlsx"):
            st.success("🟢 키워드 파일 존재")
        else:
            st.warning("🟡 키워드 파일 없음")
    
    with col_status3:
        # 매칭 시스템 상태
        if matching_system:
            st.success("🟢 매칭 시스템 정상")
        else:
            st.error("🔴 매칭 시스템 오류")
    
    # 도움말 정보
    st.markdown("---")
    st.subheader("💡 도움말")
    st.markdown("""
    **브랜드 데이터 업데이트가 안 될 때:**
    1. **🔄 브랜드 데이터 새로고침** 버튼을 클릭하세요
    2. 구글 시트의 데이터가 변경된 경우 자동으로 반영됩니다
    3. 인터넷 연결 상태를 확인해주세요
    
    **시스템 상태 확인:**
    - **🟢 초록색**: 정상 작동
    - **🟡 노란색**: 주의 필요
    - **🔴 빨간색**: 오류 발생
    
    **문제 해결:**
    - 데이터가 업데이트되지 않으면 새로고침 버튼을 시도해보세요
    - 키워드 파일이 없으면 키워드 관리에서 저장해보세요
    - 시스템 오류 시 페이지를 새로고침해보세요
    """)

def show_keyword_management_page(matching_system):
    """키워드 관리 페이지"""
    st.header("🔧 키워드 관리")
    
    if matching_system is None:
        st.error("시스템이 초기화되지 않았습니다.")
        return
    
    # 키워드 추가 섹션
    st.markdown("### ➕ 키워드 추가")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # text_area를 사용하여 특수문자 입력 문제 해결
        new_keyword = st.text_area("새 키워드 입력", 
                                  placeholder="제거할 키워드를 입력하세요 (예: *S~XL*, *13~15*)", 
                                  height=50, 
                                  key="keyword_input",
                                  help="* 기호나 특수문자가 포함된 키워드도 입력 가능합니다")
        
        # 실시간 입력 내용 확인 (디버깅용)
        if new_keyword:
            cleaned_preview = new_keyword.replace('\n', '').replace('\r', '').strip()
            if cleaned_preview:
                st.caption(f"입력된 내용: `{cleaned_preview}` (길이: {len(cleaned_preview)})")
                if '*' in cleaned_preview:
                    st.caption("✅ * 기호가 포함되어 있습니다")
                else:
                    st.caption("⚠️ * 기호가 없습니다")
    
    with col2:
        if st.button("➕ 추가", type="primary", use_container_width=True):
            # 줄바꿈 제거 및 공백 정리
            cleaned_keyword = new_keyword.replace('\n', '').replace('\r', '').strip()
            
            # 상세 디버깅 정보
            st.info(f"🔍 디버깅 정보:\n- 원본 입력: `{repr(new_keyword)}`\n- 정리된 키워드: `{repr(cleaned_keyword)}`\n- * 포함 여부: {'예' if '*' in cleaned_keyword else '아니오'}")
            
            if cleaned_keyword:
                # 키워드 추가 전 중복 확인
                if cleaned_keyword in matching_system.keyword_list:
                    st.warning(f"키워드 '{cleaned_keyword}'는 이미 존재합니다.")
                else:
                    if matching_system.add_keyword(cleaned_keyword):
                        st.success(f"키워드 '{cleaned_keyword}'가 추가되었습니다!")
                        
                        # 디버깅용: 추가된 키워드 확인
                        if cleaned_keyword.startswith('*') and cleaned_keyword.endswith('*'):
                            st.info(f"✨ 특수 패턴 키워드가 추가되었습니다: {cleaned_keyword}")
                        
                        # 키워드 파일에서 다시 로드해서 확인
                        matching_system.load_keywords()
                        if cleaned_keyword in matching_system.keyword_list:
                            st.success("✅ 키워드가 파일에 정상적으로 저장되었습니다!")
                        else:
                            st.error("❌ 키워드 저장에 문제가 있을 수 있습니다.")
                        
                        st.rerun()
                    else:
                        st.error("키워드 추가에 실패했습니다.")
            else:
                st.warning("키워드를 입력해주세요.")
    
    # 현재 키워드 목록
    st.markdown("---")
    st.markdown("### 📋 현재 키워드 목록")
    
    # 키워드 분류
    star_keywords = [kw for kw in matching_system.keyword_list if kw.startswith('*') and kw.endswith('*')]
    regular_keywords = [kw for kw in matching_system.keyword_list if not (kw.startswith('*') and kw.endswith('*'))]
    
    st.markdown(f"**총 {len(matching_system.keyword_list)}개의 키워드** (⭐ 특수패턴: {len(star_keywords)}개, 일반: {len(regular_keywords)}개)")
    
    if matching_system.keyword_list:
        # 검색 기능
        search_term = st.text_input("🔍 키워드 검색", placeholder="키워드를 검색하세요")
        
        # 필터링된 키워드 목록
        if search_term:
            filtered_keywords = [kw for kw in matching_system.keyword_list if search_term.lower() in kw.lower()]
        else:
            filtered_keywords = matching_system.keyword_list
        
        st.markdown(f"**검색 결과: {len(filtered_keywords)}개**")
        
        # 키워드 목록을 여러 컬럼으로 표시
        if filtered_keywords:
            # 페이지네이션
            keywords_per_page = 50
            total_pages = (len(filtered_keywords) - 1) // keywords_per_page + 1
            
            if total_pages > 1:
                page = st.selectbox("페이지 선택", range(1, total_pages + 1)) - 1
            else:
                page = 0
            
            start_idx = page * keywords_per_page
            end_idx = min(start_idx + keywords_per_page, len(filtered_keywords))
            page_keywords = filtered_keywords[start_idx:end_idx]
            
            # 키워드를 4개 컬럼으로 표시
            cols = st.columns(4)
            for i, keyword in enumerate(page_keywords):
                col_idx = i % 4
                with cols[col_idx]:
                    # * 키워드인지 확인하여 아이콘 구분
                    if keyword.startswith('*') and keyword.endswith('*'):
                        button_text = f"⭐❌ {keyword}"
                        button_help = f"특수패턴 키워드 '{keyword}' 삭제"
                    else:
                        button_text = f"❌ {keyword}"
                        button_help = f"일반 키워드 '{keyword}' 삭제"
                    
                    # 각 키워드를 버튼으로 표시하고 클릭하면 삭제
                    if st.button(button_text, key=f"delete_{keyword}_{i}", 
                                help=button_help, use_container_width=True):
                        if matching_system.remove_keyword(keyword):
                            st.success(f"키워드 '{keyword}'가 삭제되었습니다!")
                            st.rerun()
                        else:
                            st.error("키워드 삭제에 실패했습니다.")
            
            # 페이지 정보
            if total_pages > 1:
                st.markdown(f"**페이지 {page + 1} / {total_pages}** (전체 {len(filtered_keywords)}개 중 {start_idx + 1}-{end_idx}번째)")
        else:
            st.info("검색 조건에 맞는 키워드가 없습니다.")
    else:
        st.info("등록된 키워드가 없습니다.")
    
    # 키워드 파일 관리
    st.markdown("---")
    st.markdown("### 📁 키워드 파일 관리")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**현재 키워드를 파일로 저장**")
        if st.button("💾 키워드 저장", use_container_width=True):
            if matching_system.save_keywords():
                st.success("키워드가 keywords.xlsx 파일로 저장되었습니다!")
            else:
                st.error("키워드 저장에 실패했습니다.")
    
    with col2:
        st.markdown("**키워드 파일에서 다시 로드**")
        if st.button("🔄 키워드 다시 로드", use_container_width=True):
            matching_system.load_keywords()
            st.success("키워드를 다시 로드했습니다!")
            st.rerun()
    
    # 도움말
    st.markdown("---")
    st.markdown("### ℹ️ 도움말")
    st.markdown("""
    **키워드 관리 방법:**
    - **추가**: 상단의 입력창에 키워드를 입력하고 '추가' 버튼을 클릭
    - **삭제**: 키워드 목록에서 해당 키워드의 '❌' 버튼을 클릭
    - **검색**: 키워드가 많을 때 검색창을 이용해 원하는 키워드를 찾기
    - **저장**: 변경사항은 자동으로 keywords.xlsx 파일에 저장됨
    
    **키워드 역할:**
    - 상품명에서 불필요한 텍스트를 제거하여 매칭 정확도 향상
    - 괄호와 함께 `(키워드)` 형태로 제거됨
    - 예: `튜브탑(JS-JL)` → `튜브탑` (JS-JL이 키워드인 경우)
    
    **특수 패턴 키워드 (⭐ 추천):**
    - `*S~XL*`: 사이즈 범위 패턴 (S~XL, S-XL 모두 매칭)
    - `*13~15*`: 숫자 범위 패턴 (13~15, 13-15 모두 매칭)
    - `*FREE*`: 고정 텍스트 패턴
    - * 기호로 감싸면 틸드(~)와 하이픈(-) 변형까지 자동 처리됩니다
    """)

def show_usage_page():
    """사용법 페이지"""
    st.header("📖 사용법")
    
    st.markdown("""
    ### 🚀 **매칭 프로세스**
    
    1. **파일 업로드**: Excel 파일(들)을 선택합니다
    2. **매칭 시작**: '매칭 시작' 버튼을 클릭합니다
    3. **결과 확인**: 매칭 결과와 통계를 확인합니다
    4. **다운로드**: 결과 파일을 다운로드합니다
    
    ### 📋 **파일 형식**
    
    - **지원 형식**: `.xlsx`, `.xls`
    - **필요 컬럼**: 브랜드, 상품명, 옵션 정보 등
    - **여러 파일**: 동시에 여러 파일 업로드 가능
    
    ### 🎯 **매칭 규칙**
    
    - **브랜드명** 일치 확인
    - **상품명** 유사도 검사 (키워드 제외 후)
    - **사이즈/컬러** 옵션 매칭
    - **우선순위** 기반 최적 매칭
    
    ### 🔧 **키워드 관리**
    
    - **키워드 추가/삭제**: 사이드바의 '키워드 관리'에서 수정 가능
    - **자동 제거**: 상품명에서 키워드가 괄호와 함께 자동 제거
    - **실시간 적용**: 키워드 변경 시 즉시 매칭에 반영
    
    ### 🔄 **데이터 업데이트**
    
    - **브랜드 데이터**: 구글 시트의 최신 데이터로 수동 업데이트 가능
    - **자동 캐시**: 성능 향상을 위해 데이터 캐싱 (수동 새로고침 필요)
    - **실시간 확인**: 시스템 현황에서 '🔄' 버튼으로 즉시 업데이트
    - **업데이트 방법**:
      1. 매칭 처리 페이지: 우측 상단 '🔄' 버튼
      2. 시스템 정보 페이지: '🔄 브랜드 데이터 새로고침' 버튼
    
    ### 📊 **시스템 모니터링**
    
    - **연결 상태**: Google Sheets, 키워드 파일, 매칭 시스템 상태 확인
    - **브랜드 통계**: 브랜드별 상품 수와 총 브랜드 수 표시
    - **실시간 시간**: 마지막 확인 시간 표시
    
    ### ⚠️ **주의사항**
    
    - 파일 크기는 50MB 이하로 제한됩니다
    - 처리 시간은 데이터 양에 따라 다릅니다
    - 결과 파일은 자동으로 다운로드됩니다
    - **중요**: 구글 시트에 새 상품이 추가되면 반드시 새로고침 버튼을 클릭하세요!
    """)

if __name__ == "__main__":
    main() 