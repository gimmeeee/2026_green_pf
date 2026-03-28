import os
import gspread
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_gspread_client():
    # 1. 스트림릿 서버 환경 (Secrets)
    if "gcp_service_account" in st.secrets:
        return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
    
    # 2. 로컬 환경 (.env 경로 기반)
    json_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if json_path and os.path.exists(json_path):
        return gspread.service_account(filename=json_path)
    
    return None

def get_sheet_id():
    return st.secrets.get("GOOGLE_SHEET_ID") or os.getenv("GOOGLE_SHEET_ID")