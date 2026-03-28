# pages/form/normal.py
import streamlit as st
import streamlit.components.v1 as components

def show_normal_form():
    st.title("이번 달엔 '디지털 월세' 얼마나 내셨나요? 💸")
    st.info("""
    구독의 시대, 어떻게 하면 더 현명하게 '디지털 월세'를 관리할 수 있을지 생생한 목소리를 듣고 싶습니다.  
    보내주신 소중한 응답은 '똑똑한 구독 서비스 관리 앱'을 설계하는 데 핵심적인 데이터로 사용됩니다. 감사합니다!
            """)

    # Tally 설문지 URL (사용자의 Tally 주소로 교체하세요)
    # 예: https://tally.so/embed/w2boXD?alignLeft=1&hideTitle=1&transparentBackground=1&dynamicHeight=1
    tally_url = "https://tally.so/r/obodgN"

    # Tally 임베드 위젯 삽입
    # scrolling=True를 설정하여 긴 설문도 원활하게 표시합니다.
    components.iframe(tally_url, height=800, scrolling=True)

    st.divider()
    st.markdown("""
    ### 💡 안내 사항
    - 설문 제출 후 상단 메뉴의 **'Home(대시보드)'**으로 이동하시면 집계된 데이터를 확인하실 수 있습니다.
    - 데이터 반영에 약간의 시간 차이가 발생할 수 있습니다.
    """)

if __name__ == "__main__":
    show_normal_form()