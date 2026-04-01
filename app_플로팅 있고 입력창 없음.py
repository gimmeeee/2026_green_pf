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
def inject_floating_css():
    st.markdown("""
        <style>
        /* 1. 플로팅 버튼: 스크롤 상관없이 화면 우측 하단 고정 */
        .floating-button {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 70px;
            height: 70px;
            background-color: #FF4B4B;
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 70px;
            font-size: 30px;
            cursor: pointer;
            z-index: 1000000;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            border: none;
        }

        /* 2. 팝업 대화창: 버튼 바로 위에 고정 */
        .chat-popup {
            position: fixed;
            bottom: 110px;
            right: 30px;
            width: 380px;
            height: 600px;
            background-color: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            z-index: 999999;
            display: flex;
            flex-direction: column;
            border: 1px solid #eee;
            overflow: hidden;
        }
        
        /* 3. 팝업 내부 헤더 */
        .chat-header {
            background-color: #FF4B4B;
            padding: 15px;
            color: white;
            font-weight: bold;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

def render_chatbot_ui():
    # 1. 세션 상태 관리
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 2. CSS 주입 (Streamlit 기본 요소는 숨기고 커스텀 버튼 디자인 적용)
    st.markdown("""
        <style>
        /* 기존 스트림릿 버튼 숨기기 (키가 포함된 버튼만 타겟팅) */
        div.stButton > button[key="chat_button"] {
            display: none !important;
        }

        /* [진짜 플로팅 버튼] 디자인 */
        .custom-float-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 65px;
            height: 65px;
            background-color: #FF4B4B;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            z-index: 999999;
            border: none;
            transition: all 0.3s ease;
        }
        .custom-float-btn:hover {
            transform: scale(1.1);
        }

        /* 팝업 대화창 스타일 */
        .chat-popup {
            position: fixed;
            bottom: 110px;
            right: 30px;
            width: 370px;
            height: 580px;
            background-color: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            z-index: 999998;
            display: flex;
            flex-direction: column;
            border: 1px solid #eee;
            overflow: hidden;
        }

        /* 입력창 위치 강제 고정 */
        div[data-testid="stChatInput"] {
            position: fixed !important;
            bottom: 125px !important; 
            right: 45px !important;
            width: 340px !important;
            z-index: 1000000 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 3. HTML 버튼 클릭 감지를 위한 투명한 스트림릿 버튼 (작은 점 방지용)
    # 실제 클릭은 HTML 버튼이 받지만, 상태 변경은 이 버튼이 트리거함
    if st.button("💬", key="chat_button"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()

    # 4. 화면에 보일 실제 커스텀 버튼 (HTML)
    # 클릭 시 위에서 만든 chat_button을 클릭하게 만드는 JS 코드 포함
    st.markdown(f"""
        <div class="custom-float-btn" onclick="document.querySelector('button[key=\'chat_button\']').click()">
            💬
        </div>
    """, unsafe_allow_html=True)

    # 5. 팝업창 렌더링
    if st.session_state.chat_open:
        st.markdown("""
            <div class="chat-popup">
                <div style="background-color:#FF4B4B; padding:15px; color:white; font-weight:bold; text-align:center;">
                    🤖 OTT 분석 어드바이저
                </div>
            </div>
        """, unsafe_allow_html=True)

        msg_window = st.container(height=410)
        with msg_window:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if prompt := st.chat_input("질문을 입력하세요", key="popup_input"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with msg_window:
                with st.chat_message("user"):
                    st.markdown(prompt)
                try:
                    bot = get_chatbot()
                    response = bot.get_response(prompt, st.session_state.messages[:-1])
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except:
                    st.error("API 연결 실패")
            st.rerun()

# 4. 메인 실행부
def main():
    st.set_page_config(page_title="OTT Dashboard", layout="wide")
    df = get_data()

    # 사이드바 메뉴
    st.sidebar.title("🧭 메뉴")
    menu = st.sidebar.selectbox("페이지", ["Dashboard Home", "Survey Page", "부록"])

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