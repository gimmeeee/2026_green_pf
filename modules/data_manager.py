# modules/data_manager.py
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

    def get_all_responses_df(self, sheet_name=None):
        """
        모든 응답 데이터를 데이터프레임으로 변환. 
        get_all_records() 대신 get_all_values()를 사용하여 데이터 유실 방지.
        """
        target = sheet_name or self.r_sheet_name
        worksheet = self.spreadsheet.worksheet(target)
        
        # get_all_values()는 시트의 모든 셀을 리스트의 리스트로 가져옵니다. (가장 확실한 방법)
        all_values = worksheet.get_all_values()
        
        if not all_values:
            return pd.DataFrame()
            
        # 첫 번째 행을 헤더로 설정
        headers = all_values[0]
        data = all_values[1:]
        
        df = pd.DataFrame(data, columns=headers)
        
        # 1. Submission ID가 비어있는 가짜 행(공백 행) 제거
        if 'Submission ID' in df.columns:
            df = df[df['Submission ID'].str.strip() != ""]
            
        # 2. 모든 데이터의 앞뒤 공백 제거 및 결측치 처리
        df = df.apply(lambda x: x.str.strip() if hasattr(x, "str") else x)
        df = df.replace('', None)
        
        return df

    def get_questions(self, sheet_name=None):
        """설문 문항 로드"""
        target = sheet_name or self.q_sheet_name
        return self.spreadsheet.worksheet(target).get_all_records()

    def save_response(self, row_data, sheet_name=None):
        """설문 응답 저장"""
        target = sheet_name or self.r_sheet_name
        return self.spreadsheet.worksheet(target).append_row(row_data)