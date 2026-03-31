# pip install gspread google-auth langchain_chroma sentence-transformers
# python -m modules.sync_all
# 모듈실행명령 modules라는 '패키지' 안에 들어있는 sync_all이라는 **'모듈'**을 찾아서 실행
# pip install -r requirements.txt
from modules.data_manager import SheetManager
from modules.vector_db import SkinVectorDB
import pandas as pd

def sync_sheets_to_vector_db():
    print("🔍 1. 구글 시트에서 전체 응답 데이터를 불러오는 중...")
    try:
        # SheetManager 초기화 및 데이터 로드
        sm = SheetManager(q_sheet="질문관리", r_sheet="응답결과")
        # 모든 응답 데이터를 데이터프레임으로 가져오기
        df = sm.get_all_responses_df() 
        
        if df.empty:
            print("❌ 동기화할 데이터가 시트에 없습니다.")
            return

        print(f"📊 로드 완료: 총 {len(df)}건의 응답을 확인했습니다.")

        print("🚀 2. 벡터 DB 생성 및 데이터 정제/임베딩 시작...")
        # 벡터 DB 매니저 초기화
        vdb = SkinVectorDB()
        
        # 전체 데이터프레임을 전달하여 일괄 저장
        # 내부적으로 clean_text가 가동되어 지저분한 기호를 제거합니다.
        result_msg = vdb.upsert_survey_data(df)
        
        print(f"✨ 결과: {result_msg}")
        print("🎉 모든 시트 데이터가 벡터 DB와 성공적으로 동기화되었습니다!")

    except Exception as e:
        print(f"❌ 동기화 중 오류 발생: {e}")

if __name__ == "__main__":
    sync_sheets_to_vector_db()