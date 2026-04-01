import streamlit as st
import pandas as pd
from modules.data_manager import SheetManager
from modules.visualizer import SkinVisualizer
from pages.form.normal import show_normal_form
from modules.chatbot import SkinChatbot
from streamlit_float import *
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
    st.divider()
    
    # Part 3: Hypothesis & Expansion
    st.header("3️⃣ 가설 검증 및 시장 확장성")
    viz.plot_pain_correlation()
    viz.plot_market_expansion()

# 3. 플로팅 챗봇 UI
def on_send():
    if st.session_state.chat_input_val:
        user_val = st.session_state.chat_input_val
        # 사용자의 질문을 메시지 리스트에 추가
        st.session_state.messages.append({"role": "user", "content": user_val})
        
        try:
            bot = get_chatbot()
            # AI 답변 생성
            response = bot.get_response(user_val, st.session_state.messages[:-1])
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            # 에러 발생 시 팝업 내부에 표시
            import re
            error_str = str(e)
            code_match = re.search(r'\d{3}', error_str)
            code = code_match.group() if code_match else "Unknown"
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ 연결 오류 : {code}"})
            
        # 입력창 비우기
        st.session_state.chat_input_val = ""
        # 팝업 상태 유지 강제 고정
        st.session_state.chat_open = True

# 3. 챗봇 UI 렌더링 함수
def render_chatbot_ui():
    float_init()

    # 세션 상태 초기화
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # [공통 CSS] 디자인 디테일 수정
    st.markdown("""
        <style>
        /* 1. 채팅 메시지 스타일 (버블) */
        div[data-testid="stChatMessage"] {
            z-index: 1000 !important;
            background-color: transparent !important;
            border: none !important;
            padding: 0.2rem 1rem !important;
            margin-bottom: -10px !important;
            overflow-wrap: break-word !important;
        }

        /* 채팅 텍스트 자체의 스타일 (폰트 색상, 크기, 줄간격) */
        div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] p {
            color: #212529 !important;
            font-size: 0.95rem !important;
            line-height: 1.6 !important;
        }
                
        /* 메시지 컨테이너 자체에 상하 여백 강제 부여 */
        [data-testid="stVerticalBlock"] > div:has(div[data-testid="stChatMessage"]) {
            margin-top: 10px !important;    /* 헤더 아래 공간 확보 */
            margin-bottom: 20px !important; /* 입력창 위 공간 확보 */
        }

        /* 2. 입력창 컨테이너 (입력창 부모 박스) */
        div[data-testid="stTextInput"] {
            position: absolute !important;
            bottom: 20px !important;  /* 바닥에서의 높이 */
            left: 0 !important;
            right: 0 !important;
            z-index: 1010 !important;
            padding: 10px 20px !important;
            background-color: white !important; /* 중요: 메시지가 입력창 뒤로 지나갈 때 안 보이게 함 */
            height: 45px !important;
        }
        
        /* 3. 입력창 내부 레이어: 불필요한 Streamlit 배경 제거 및 오버플로우 허용 */
        div[data-testid="stTextInput"] > div,
        div[data-testid="stTextInputRootElement"],
        div[data-baseweb="base-input"],
        div[data-baseweb="input"] {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            overflow: visible !important; /* 내부 요소가 잘리지 않게 함 */
        }
                
        /* 입력창 클릭 시 문구(placeholder)가 즉각 반응하도록 설정 */
        div[data-testid="stTextInput"] input:focus::placeholder {
            color: transparent !important;
        }
        
        /* 메시지 영역이 입력창과 겹치지 않게 하단 여백 추가 */
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding-bottom: 100px !important;
        }
                
        /* 챗은 배경 없이 깨끗하게 */
        .st-emotion-cache-1097z0u {
            background-color: transparent !important;
        }

        /* 4. 실제 입력 필드(input tag) 스타일 */
        div[data-testid="stTextInput"] input {
            background-color: #f1f3f5 !important;
            border: 1.5px solid #ced4da !important; /* 테두리 색상 살짝 연하게 조정 가능 */
            border-radius: 20px !important; /* 팝업 모서리와 곡률 맞춤 */
            
            height: 45px !important;
            padding: 0 15px !important;
            
            color: #212529 !important;
            font-size: 0.95rem !important;
        }

        /* 메시지 영역 하단 패딩 확보: 입력창에 가려지지 않게 함 */
        [data-testid="stChatMessageContainer"] {
            padding-top: 70px !important;    /* 헤더(60px) 공간 확보 */
            padding-bottom: 120px !important; /* 입력창 및 여백 확보 */
            overflow-y: auto !important;
        }

        /* 클릭(포커스) 시 스타일 유지 및 placeholder 처리 */
        div[data-testid="stTextInput"] input:focus {
            border: 1.5px solid #FF4B4B !important;
            box-shadow: none !important;
            outline: none !important;
        }

        /* Placeholder(안내 문구) 색상 */
        div[data-testid="stTextInput"] input::placeholder {
            color: #adb5bd !important;
            opacity: 1 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("<br>" * 5, unsafe_allow_html=True)
        st.divider()
        btn_label = "❌ 닫기" if st.session_state.chat_open else "💬 분석 어드바이저"
        if st.button(btn_label, use_container_width=True, type="primary"):
            st.session_state.chat_open = not st.session_state.chat_open
            st.rerun()

    if st.session_state.chat_open:
        chat_container = st.container()
        
        with chat_container:
            # 1. 헤더: 단색 플랫 디자인
            st.markdown("""
                <div style="background:#FF4B4B; color:white; padding:20px; border-radius:25px 25px 0 0; 
                            text-align:center; font-weight:700; font-size:1.1rem; position:relative; z-index: 1002; box-shadow: 0 0 10px rgba(0,0,0,0.3);">
                    🤖 분석 어드바이저
                </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            # 2. 메시지 영역
            msg_area = st.container(height=520, border=False)
            with msg_area:
                if not st.session_state.messages:
                    st.markdown("""<div style="text-align:center; color:#adb5bd; padding-top:180px; font-size:0.85rem;">
                                   분석 결과에 대해 무엇이든 물어보세요.</div>""", unsafe_allow_html=True)
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            # 3. 질문 입력창 (위 CSS에서 패딩과 곡률이 적용됨)
            st.text_input("질문", key="chat_input_val", on_change=on_send, 
                          placeholder="질문을 입력하고 Enter!", label_visibility="collapsed")

        # 팝업 본체 고정 및 둥근 테두리/그림자 최적화
        chat_container.float(
            "bottom: 3rem; right: 3rem; width: 420px; height: 600px; " # 높이 넉넉히 확보
            "background: white; border-radius: 25px; "
            "box-shadow: 0 15px 50px rgba(0,0,0,0.15); border: none; "
            "display: block; overflow: visible;" # 내부 요소가 '절대 위치'로 뜰 수 있게 허용
        )

# 4. 메인 실행부
def main():
    st.set_page_config(page_title="Digital Rent Dashboard", layout="wide", page_icon="💸")
    st.markdown('<html lang="ko">', unsafe_allow_html=True)
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
        st.write("# 우리 단지 디지털 월세 리포트 💸")
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