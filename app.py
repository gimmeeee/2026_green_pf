import streamlit as st
import pandas as pd
from modules.data_manager import SheetManager
from modules.visualizer import SkinVisualizer
from pages.form.normal import show_normal_form

# --- [함수 1] 구글 응답 결과 요약 보고서 (매개변수 df 추가) ---
def render_business_summary(df): # (수정) df를 인자로 받도록 변경
    st.subheader("📝 문항별 응답 요약 (Top Selection)")    
    
    if df.empty:
        st.info("데이터가 충분하지 않습니다.")
        return

    summary_list = []
    
    # 12개 질문에 대해 순회 (인덱스 1부터 시작)
    for i in range(1, len(df.columns)):
        col_name = df.columns[i]
        
        # 주관식/객관식 판별 및 통계 로직
        if "주로 사용" in col_name or "바라는 점" in col_name:
            top_val = "주관식 응답"
            count = f"{df[col_name].nunique()}개의 다양한 의견"
        else:
            series = df[col_name].str.split(', ').explode()
            top_choice = series.value_counts()
            
            if not top_choice.empty:
                top_val = top_choice.index[0]
                count = f"{top_choice.values[0]}명 선택"
            else:
                top_val = "-"
                count = "0명"

        summary_list.append({
            "문항 번호": f"Q{i}",
            "질문 내용 요약": col_name[:25] + "..." if len(col_name) > 25 else col_name,
            "최다 선택 답변": top_val,
            "응답 수": count
        })

    summary_df = pd.DataFrame(summary_list)
    st.table(summary_df)

# --- [함수 2] 시각화 대시보드 ---
def render_visual_dashboard(df):
    st.subheader("📊 실시간 데이터 시각화")
    viz = SkinVisualizer(df)
    
    col1, col2 = st.columns(2)
    with col1:
        viz.plot_target_distribution()
    with col2:
        viz.plot_skin_concerns()
        
    st.divider()
    viz.plot_visit_vs_reason()
    
    st.divider()
    col3, col4 = st.columns(2)
    with col3:
        viz.plot_cost_analysis()
    with col4:
        viz.plot_selection_criteria()

# --- 메인 실행부 ---
def main():
    st.set_page_config(page_title="Skin AI Analysis", layout="wide")

    # 데이터 로드
    try:
        db = SheetManager()
        df = db.get_all_responses_df()
    except Exception as e:
        st.error(f"데이터 연결 실패: {e}")
        df = pd.DataFrame() 

    # 사이드바 메뉴
    st.sidebar.title("🧭 Navigation")
    menu = st.sidebar.selectbox("Go to", ["Home", "Normal Survey", "AI Prediction", "개발리드미"])

    if menu == "Home":
        st.write("# 🏠 Dashboard Home")
        
        if not df.empty:
            # (수정) 함수 호출 시 로드한 df를 전달합니다.
            render_business_summary(df) 
            st.write("---")
            render_visual_dashboard(df)
        else:
            st.info("수집된 데이터가 없습니다. 설문을 먼저 진행해주세요.")
        
    elif menu == "Normal Survey":
        show_normal_form()

    elif menu == "AI Prediction":
        st.write("## 🤖 AI 분석 리포트 (준비 중)")

    elif menu == "개발리드미":
        st.write("리드미")        

if __name__ == "__main__":
    main()