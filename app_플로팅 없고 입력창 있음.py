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
    st.header("1️⃣ 응답자 분석 (Demographic)")
    viz.plot_demographic_all()
    viz.plot_high_intent_persona()
    st.divider()
    
    # Part 2: OTT Deep-Dive
    st.header("2️⃣ OTT 집중 분석: 해지 사유와 효율성")
    viz.plot_cancel_trigger_analysis()
    viz.plot_ott_usage_efficiency()
    viz.plot_segment_reason_correlation()
    st.divider()
    
    # Part 3: Hypothesis & Expansion
    st.header("3️⃣ 가설 검증 및 시장 확장성")
    viz.plot_pain_correlation()
    viz.plot_market_expansion()

# 3. 플로팅 챗봇 UI (위치 고정 특화)
def render_chatbot_ui():
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 1. CSS: 버튼의 위치와 스타일을 무조건 '오른쪽 아래'로 고정
    # Streamlit의 모든 버튼 중 'HIDDEN'이라는 글자를 가진 놈을 타겟팅합니다.
    st.markdown("""
        <style>
        /* 모든 버튼 중 텍스트가 HIDDEN인 버튼 찾기 */
        button div p {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        /* 버튼 컨테이너 위치 강제 고정 */
        .stButton button {
            position: fixed !important;
            bottom: 30px !important;
            right: 30px !important;
            width: 65px !important;
            height: 65px !important;
            border-radius: 50% !important;
            background-color: #FF4B4B !important;
            color: white !important;
            z-index: 999999 !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
            transition: transform 0.2s ease !important;
        }

        /* 버튼 안의 텍스트 'HIDDEN'을 '💬'로 교체 */
        .stButton button p {
            font-size: 0 !important; /* 원래 글자 숨기기 */
        }
        .stButton button p::before {
            content: "💬" !important;
            font-size: 30px !important;
        }

        .stButton button:hover {
            transform: scale(1.1) !important;
            background-color: #FF3333 !important;
        }

        /* 대화창 팝업 레이아웃 */
        .chat-window {
            position: fixed;
            bottom: 110px;
            right: 30px;
            width: 370px;
            height: 550px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            z-index: 999998;
            border: 1px solid #eee;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* 채팅 입력바 위치 조정 */
        div[data-testid="stChatInput"] {
            position: fixed !important;
            bottom: 125px !important;
            right: 45px !important;
            width: 340px !important;
            z-index: 1000000 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. 실제 버튼 생성 (이 버튼이 위 CSS에 의해 오른쪽 아래로 이동함)
    # 버튼을 사이드바 맨 아래나 메인 맨 아래 어디에 두든 CSS가 끌어당깁니다.
    st.button("HIDDEN", key="hidden_toggle")
    
    if st.session_state.get("hidden_toggle"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()

    # 3. 팝업창 UI
    if st.session_state.chat_open:
        st.markdown("""
            <div class="chat-window">
                <div style="background-color:#FF4B4B; padding:15px; color:white; font-weight:bold; text-align:center;">
                    🤖 OTT 분석 어드바이저
                </div>
            </div>
        """, unsafe_allow_html=True)

        msg_area = st.container(height=390)
        with msg_area:
            if not st.session_state.messages:
                st.info("안녕하세요! 무엇이든 물어보세요.")
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if prompt := st.chat_input("질문을 입력하세요", key="popup_input"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            # 챗봇 로직 수행...
            try:
                bot = get_chatbot()
                response = bot.get_response(prompt, st.session_state.messages[:-1])
                st.session_state.messages.append({"role": "assistant", "content": response})
            except:
                st.error("연결 실패")
            st.rerun()

# 4. 메인 실행부
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
    menu = st.sidebar.selectbox("메뉴", ["Dashboard Home", "Survey Page", "부록"])

    if menu == "Dashboard Home":
        st.write("# 💸 우리 단지 디지털 월세 리포트")
        if not df.empty:
            render_visual_dashboard(df)
        else:
            st.warning("수집된 데이터가 없습니다. 시트 연결 상태를 확인해주세요.")
    
    elif menu == "Survey Page":
        show_normal_form()

    # 챗봇 UI 호출 (맨 마지막에 호출해야 레이어 순서가 가장 위로 올라감)
    render_chatbot_ui()

if __name__ == "__main__":
    main()