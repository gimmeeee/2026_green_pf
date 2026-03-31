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
    # 1. 세션 상태 초기화 (상태 유실 방지)
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 버튼 클릭 시 상태를 반전시키는 콜백 (동기화 후에도 상태 유지)
    def handle_fab_click():
        st.session_state.chat_open = not st.session_state.chat_open

    # 2. CSS: 버튼 디자인 복구 및 입력창 위치 '절대' 고정
    st.markdown("""
        <style>
        /* 빨간 원형 버튼 디자인 */
        div.stButton > button[key="fixed_fab_btn"] {
            position: fixed !important;
            bottom: 30px !important;
            right: 30px !important;
            width: 65px !important;
            height: 65px !important;
            border-radius: 50% !important;
            background-color: #FF4B4B !important;
            color: white !important;
            z-index: 1000001 !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        }
        div.stButton > button[key="fixed_fab_btn"] p { display: none !important; }
        div.stButton > button[key="fixed_fab_btn"]::after {
            content: "💬" !important;
            font-size: 30px !important;
            display: block !important;
        }

        /* 팝업창 프레임 */
        .chat-container-fixed {
            position: fixed;
            bottom: 110px;
            right: 30px;
            width: 370px;
            height: 550px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            z-index: 999990;
            border: 1px solid #eee;
            display: flex;
            flex-direction: column;
        }

        /* 메시지 영역 강제 귀속 */
        div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stChatMessage"]) {
            position: fixed !important;
            bottom: 185px !important;
            right: 40px !important;
            width: 350px !important;
            height: 380px !important;
            z-index: 999995 !important;
            overflow-y: auto !important;
            background: white !important;
        }

        /* 입력창 위치 절대 고정 (사라짐 방지) */
        div[data-testid="stChatInput"] {
            position: fixed !important;
            bottom: 125px !important;
            right: 45px !important;
            width: 340px !important;
            z-index: 1000000 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 3. 플로팅 버튼 (on_click으로 리런 시에도 상태 보존)
    st.button("CHAT", key="fixed_fab_btn", on_click=handle_fab_click)

    # 4. 팝업창 활성화 시 내용 렌더링
    if st.session_state.chat_open:
        # 헤더와 프레임
        st.markdown("""
            <div class="chat-container-fixed">
                <div style="background-color:#FF4B4B; padding:15px; color:white; font-weight:bold; text-align:center; border-radius: 20px 20px 0 0;">
                    🤖 OTT 분석 어드바이저
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 메시지 및 입력 위젯
        # container를 명시적으로 사용하여 위젯이 사라지지 않게 묶음
        with st.container():
            # 메시지 출력
            msg_box = st.container()
            with msg_box:
                if not st.session_state.messages:
                    st.info("데이터 동기화가 완료되었습니다. 분석을 시작할까요?")
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

            # 입력창 (팝업이 열려있을 때만 렌더링)
            if prompt := st.chat_input("질문을 입력하세요", key="active_chat_input"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                try:
                    bot = get_chatbot() # SkinChatbot 클래스 호출
                    response = bot.get_response(prompt, st.session_state.messages[:-1])
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"대화 에러: {e}")
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