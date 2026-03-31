import streamlit as st
import pandas as pd
from modules.data_manager import SheetManager
from modules.visualizer import SkinVisualizer
from pages.form.normal import show_normal_form
from modules.chatbot import SkinChatbot
import time

# 1. 데이터 및 챗봇 로드
@st.cache_data(ttl=60)
def get_data():
    try:
        db = SheetManager()
        df = db.get_all_responses_df()
        if 'Submission ID' in df.columns:
            df = df[df['Submission ID'].str.strip() != ""]
        return df
    except Exception as e:
        st.error(f"데이터 로드 에러: {e}")
        return pd.DataFrame()

@st.cache_resource
def get_chatbot():
    return SkinChatbot()

# 2. 시각화 대시보드
def render_visual_dashboard(df):
    viz = SkinVisualizer(df)
    st.header("📊 데이터 요약")
    col1, col2 = st.columns(2)
    col1.metric("총 응답 수", f"{len(df)}개")
    col2.metric("마지막 업데이트", time.strftime("%H:%M:%S"))
    st.divider()
    viz.plot_demographic_all()
    viz.plot_cancel_trigger_analysis()
    viz.plot_ott_usage_efficiency()

# 3. 플로팅 챗봇 UI (위치 고정 특화)
def render_chatbot_ui():
    # CSS: 스크롤과 무관하게 화면 우측 하단에 물리적으로 고정
    st.markdown("""
        <style>
        /* [1] 챗봇 아이콘: 화면 우측 하단 절대 고정 */
        div.stButton > button[key="floating_chat_icon"] {
            position: fixed !important;
            bottom: 30px !important;
            right: 30px !important;
            width: 70px !important;
            height: 70px !important;
            border-radius: 50% !important;
            background-color: #FF4B4B !important;
            color: white !important;
            font-size: 30px !important;
            z-index: 999999 !important; /* 모든 요소보다 위에 */
            box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
            border: none !important;
        }

        /* [2] 팝업창 본체: 아이콘 바로 위에 고정 */
        .chat-popup-window {
            position: fixed;
            bottom: 110px;
            right: 30px;
            width: 380px;
            height: 600px;
            background-color: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.25);
            z-index: 999997;
            display: flex;
            flex-direction: column;
            border: 1px solid #f0f0f0;
            overflow: hidden;
        }

        /* [3] 입력창: 브라우저 바닥이 아닌 팝업창 하단에 강제 고정 */
        div[data-testid="stChatInput"] {
            position: fixed !important;
            bottom: 125px !important; 
            right: 45px !important;
            width: 350px !important;
            z-index: 999998 !important;
            background-color: white !important;
        }
        
        /* 팝업 헤더 */
        .chat-header {
            background-color: #FF4B4B;
            padding: 15px;
            color: white;
            font-weight: bold;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 플로팅 아이콘 (스크롤을 내려도 따라다님)
    if st.button("💬", key="floating_chat_icon"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()

    # 팝업 열기
    if st.session_state.chat_open:
        st.markdown('<div class="chat-popup-window">', unsafe_allow_html=True)
        st.markdown('<div class="chat-header">🤖 OTT 분석 어드바이저</div>', unsafe_allow_html=True)

        # 메시지 영역 (높이 조절로 입력창 공간 확보)
        msg_container = st.container()
        with msg_container:
            inner_box = st.container(height=420)
            with inner_box:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

        # 입력창 (CSS가 팝업 안으로 위치를 강제 조정한 상태)
        if prompt := st.chat_input("질문을 입력하세요", key="popup_input"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with inner_box:
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    try:
                        bot = get_chatbot()
                        response = bot.get_response(prompt, st.session_state.messages[:-1])
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except:
                        st.error("API 연결 실패")
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# 4. 메인 실행부
def main():
    st.set_page_config(page_title="OTT Dashboard", layout="wide")
    df = get_data()

    # 사이드바 메뉴
    st.sidebar.title("🧭 메뉴")
    menu = st.sidebar.selectbox("페이지", ["Dashboard Home", "Survey Page"])

    if menu == "Dashboard Home":
        st.title("💸 우리 단지 디지털 월세 리포트")
        if not df.empty:
            render_visual_dashboard(df)
    elif menu == "Survey Page":
        show_normal_form()

    # 챗봇 UI 호출 (맨 마지막에 호출해야 레이어 순서가 가장 위로 올라감)
    render_chatbot_ui()

if __name__ == "__main__":
    main()