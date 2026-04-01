def render_chatbot_ui():
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 1. CSS: 사이드바 위젯 중 특정 ID를 가진 놈만 우측 하단으로 강제 이사
    st.markdown("""
        <style>
        /* 채팅 버튼 (항상 우측 하단 고정) */
        div.stButton > button[key="final_toggle"] {
            position: fixed !important;
            bottom: 30px !important;
            right: 30px !important;
            width: 60px !important;
            height: 60px !important;
            border-radius: 50% !important;
            background-color: #FF4B4B !important;
            z-index: 999999 !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        }
        div.stButton > button[key="final_toggle"] p { display: none !important; }
        div.stButton > button[key="final_toggle"]::after { content: "💬"; font-size: 25px; color: white; }

        /* 팝업 컨테이너 (사이드바 안에 있지만 화면 우측에 고정) */
        [data-testid="stSidebarUserContent"] div:has(div[data-testid="stExpander"]) {
            position: fixed !important;
            bottom: 100px !important;
            right: 30px !important;
            width: 350px !important;
            z-index: 999998 !important;
        }
        
        /* 팝업 헤더 색상 제어 */
        div[data-testid="stExpander"] {
            border-radius: 15px !important;
            border: 1px solid #FF4B4B !important;
            background: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. 버튼은 메인 어디에 두든 CSS가 우측 하단으로 보냅니다.
    st.button("T", key="final_toggle", on_click=lambda: st.session_state.update({"chat_open": not st.session_state.chat_open}))

    # 3. [핵심] 사이드바 영역 안에 채팅창을 물리적으로 생성 (도망 방지)
    if st.session_state.chat_open:
        with st.sidebar:
            # Expander를 사용하여 팝업 느낌을 줌
            with st.expander("🤖 OTT 분석 어드바이저", expanded=True):
                # 메시지 표시 영역
                chat_container = st.container(height=350)
                with chat_container:
                    if not st.session_state.messages:
                        st.info("데이터 동기화 완료!")
                    for msg in st.session_state.messages:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
                
                # 입력창 (사이드바 안에 박혀있어서 절대 안 사라짐)
                if prompt := st.chat_input("질문을 입력하세요", key="sidebar_chat_input"):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    try:
                        bot = get_chatbot()
                        response = bot.get_response(prompt, st.session_state.messages[:-1])
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except:
                        st.error("연결 에러")
                    st.rerun()