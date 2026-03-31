# pip uninstall -y langchain-google-genai google-generativeai
# 2. 최신 버전(4.0.0 이상)으로 재설치
# pip install -U langchain-google-genai
# 429 RESOURCE_EXHAUSTED → 요청은 갔고, 쿼터만 없음 
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from modules.vector_db import SkinVectorDB
from dotenv import load_dotenv

load_dotenv()

class SkinChatbot:
    def __init__(self):
       
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3,  # 문서에서 Gemini 3.0+ (1.5 포함) 권장값인 1.0으로 설정
            max_retries=3
        )
       
        self.vdb = SkinVectorDB()
        self.system_prompt = """
            당신은 '디지털 월세'로 불리는 구독 서비스 관리 앱 설계를 위한 UX 전문가입니다. 
            제공된 설문 데이터를 바탕으로 사용자들의 이용 행태, 해지 사유, 니즈 등을 분석하여 답변하세요.
            데이터에 기반하여 객관적으로 답변하고, 없는 내용을 지어내지 마세요.
        """

    def get_response(self, user_query, chat_history):
        # 벡터 DB 검색 (기존 로직 유지)
        try:
            related_docs = self.vdb.query_similar_data(user_query, k=5)
            context = "\n".join([doc.page_content for doc in related_docs])
        except:
            context = "데이터를 찾을 수 없습니다."

        # [최신 문서 반영] Invocation 구조 최적화
        messages = [
            SystemMessage(content=f"{self.system_prompt}\n\n[데이터 맥락]\n{context}"),
        ]
        
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=user_query))
        
        # 호출 및 응답 반환
        response = self.llm.invoke(messages)
        
        # [주의] Gemini 1.5/2.5는 .content가 직접 문자열을 반환합니다.
        return response.content