from modules.auth_utils import get_gspread_client, get_sheet_id
import pandas as pd
import gspread

class SheetManager:
    def __init__(self, q_sheet="질문관리", r_sheet="응답결과"):
        try:
            self.client = get_gspread_client()
            self.sheet_id = get_sheet_id()
            
            if not self.client:
                raise Exception("구글 클라이언트 인증 실패")
                
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            self.q_sheet_name = q_sheet
            self.r_sheet_name = r_sheet
        except Exception as e:
            raise Exception(f"시트 연결 중 오류 발생: {e}")

    def get_questions(self, sheet_name=None):
        """설문 문항 로드"""
        target = sheet_name or self.q_sheet_name
        return self.spreadsheet.worksheet(target).get_all_records()

    def check_duplicate(self, user_id, col_index=1, sheet_name=None):
        """중복 참여 확인 (Submission ID 기준)"""
        target = sheet_name or self.r_sheet_name
        existing_ids = self.spreadsheet.worksheet(target).col_values(col_index)
        return user_id in existing_ids

    def save_response(self, row_data, sheet_name=None):
        """설문 응답 저장"""
        target = sheet_name or self.r_sheet_name
        return self.spreadsheet.worksheet(target).append_row(row_data)

    def get_all_responses_df(self, sheet_name=None):
        """모든 응답 데이터를 데이터프레임으로 변환 (안정성 강화)"""
        target = sheet_name or self.r_sheet_name
        records = self.spreadsheet.worksheet(target).get_all_records()
        df = pd.DataFrame(records)
        # 결측치를 빈 문자열로 대체하여 .str 에러 방지
        return df.fillna("")