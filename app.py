import streamlit as st
import pandas as pd
from modules.data_manager import SheetManager
from modules.visualizer import SkinVisualizer

def render_visual_dashboard(df):
    """소장님의 3단계 전략 구조 반영"""
    viz = SkinVisualizer(df)
    
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
    if st.sidebar.button("🔄 데이터 새로고침"):
        st.cache_data.clear()
        st.toast("최신 정보를 불러오는 중입니다...")

    @st.cache_data(ttl=600)
    def get_data():
        try:
            db = SheetManager()
            df = db.get_all_responses_df()
            return df
        except Exception as e:
            st.error(f"데이터 로드 에러: {e}")
            return pd.DataFrame()

    df = get_data()

    menu = st.sidebar.selectbox("메뉴", ["Dashboard Home", "Survey Page"])

    if menu == "Dashboard Home":
        st.write("# 💸 우리 단지 디지털 월세 리포트")
        if not df.empty:
            render_visual_dashboard(df)
        else:
            st.warning("수집된 데이터가 없습니다.")
    
    elif menu == "Survey Page":
        st.info("Tally 설문 페이지로 이동하거나 폼을 렌더링합니다.")

if __name__ == "__main__":
    main()