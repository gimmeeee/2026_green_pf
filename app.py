import streamlit as st
import pandas as pd
from modules.data_manager import SheetManager
from modules.visualizer import SkinVisualizer
# 설문 페이지 함수 임포트
from pages.form.normal import show_normal_form
import time

def render_visual_dashboard(df):
    """시각화 대시보드 렌더링"""
    viz = SkinVisualizer(df)
    
    # 상단 요약 지표 (실제 데이터 개수 확인용)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 총 응답 수", f"{len(df)}개")
    with col2:
        st.metric("📅 마지막 업데이트", time.strftime("%H:%M:%S"))
    
    st.divider()

    # Part 1: Demographic
    st.header("1️⃣ Demographic: 입주민 페르소나")
    viz.plot_demographic_all()
    viz.plot_high_intent_persona()
    st.divider()
    
    # Part 2: OTT Deep-Dive
    st.header("2️⃣ OTT 집중 분석: 효율성과 이탈")
    viz.plot_ott_quarter_dist()
    viz.plot_efficiency_scatter()
    viz.plot_cancel_trigger_analysis()
    st.divider()
    
    # Part 3: Hypothesis & Expansion
    st.header("3️⃣ 가설 검증 및 시장 확장성")
    viz.plot_pain_correlation()
    viz.plot_market_expansion()

def main():
    st.set_page_config(page_title="Digital Rent Dashboard", layout="wide", page_icon="💸")

    st.sidebar.title("🧭 단지 안내소")
    
    # 데이터 새로고침 로직 강화
    if st.sidebar.button("🔄 최신 데이터 강제 동기화"):
        st.cache_data.clear() # 캐시 전체 삭제
        st.sidebar.success("캐시가 삭제되었습니다. 다시 불러옵니다.")
        time.sleep(1)
        st.rerun()

    @st.cache_data(ttl=60) # TTL을 10분에서 1분으로 단축하여 더 자주 갱신되게 함
    def get_data():
        try:
            db = SheetManager()
            # '응답결과' 시트를 명시적으로 호출하고, 빈 값 처리를 강화
            df = db.get_all_responses_df()
            
            # Submission ID가 비어있는 행은 제거 (시트 하단의 빈 행 방지)
            if 'Submission ID' in df.columns:
                df = df[df['Submission ID'] != ""]
                
            return df
        except Exception as e:
            st.error(f"데이터 로드 에러: {e}")
            return pd.DataFrame()

    df = get_data()

    # 메뉴 구성
    menu = st.sidebar.selectbox("메뉴", ["Dashboard Home", "Survey Page"])

    if menu == "Dashboard Home":
        st.write("# 💸 우리 단지 디지털 월세 리포트")
        if not df.empty:
            render_visual_dashboard(df)
        else:
            st.warning("수집된 데이터가 없습니다. 시트 연결 상태를 확인해주세요.")
    
    elif menu == "Survey Page":
        show_normal_form()

if __name__ == "__main__":
    main()