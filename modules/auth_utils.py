import os
import gspread
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_gspread_client():
    # 1. 스트림릿 서버 환경 (Secrets)
    
    if "gcp_service_account" in st.secrets:
        # AttrDict를 일반 dict로 변환
        creds_dict = {k: v for k, v in st.secrets["gcp_service_account"].items()}
        
        # 핵심: \n 문자열을 실제 줄바꿈으로 변환
        # 스트림릿 Secrets에 \n이 포함된 문자열을 넣으면, 시스템은 보안과 데이터 보존을 위해 이를 \\n (역슬래시 두 개)로 읽어버리는 경우가 많습니다.
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        return gspread.service_account_from_dict(creds_dict)
    
    # 2. 로컬 환경
    json_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if json_path and os.path.exists(json_path):
        return gspread.service_account(filename=json_path)
    
    return None

def get_sheet_id():
    return st.secrets.get("GOOGLE_SHEET_ID") or os.getenv("GOOGLE_SHEET_ID")