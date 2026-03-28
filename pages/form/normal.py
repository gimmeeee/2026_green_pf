# 기존 app.py의 설문 폼 로직
# pages/form/normal.py
import streamlit as st
from modules.data_manager import SheetManager

def show_normal_form():

    try:
        # 모듈 폴더의 클래스 호출
        db = SheetManager(q_sheet="질문관리", r_sheet="응답결과")
        questions_data = db.get_questions()

    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return

    st.title("📋 피부 고민 설문조사")
    user_id = st.text_input("연락처 또는 이메일", placeholder="중복 참여 확인용")

    with st.form("survey_form"):
        responses = {}
        for q in questions_data:
            q_num, q_text, q_type = q['문항번호'], q['질문내용'], q['질문유형']
            q_options = [opt.strip() for opt in str(q['선택지']).split(',')] if q['선택지'] else []
            
            label = f"Q{q_num}. {q_text}"
            if q_type == 'radio':
                responses[q_num] = st.radio(label, options=q_options, index=None)
            elif q_type == 'checkbox':
                responses[q_num] = st.multiselect(label, options=q_options)
            elif q_type == 'text':
                responses[q_num] = st.text_area(label)
            st.write("---")

        if st.form_submit_button("설문 제출하기", type="primary"):
            if not user_id:
                st.warning("식별 정보를 입력해주세요.")
            elif db.check_duplicate(user_id):
                st.error("이미 참여하신 기록이 있습니다.")
            else:
                # 데이터 조립
                row = [user_id]
                for q in questions_data:
                    ans = responses[q['문항번호']]
                    row.append(", ".join(ans) if isinstance(ans, list) else (ans or ""))
                
                db.save_response(row)
                st.success("제출 완료!")
                st.balloons()

if __name__ == "__main__":
    show_normal_form()