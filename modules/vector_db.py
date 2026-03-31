# 동기화(Sync) 전략
# 시트 내용이 변경될 때마다 벡터 DB를 업데이트

import os
import re
import pandas as pd
# 성공했던 모델을 쓰기 위해 추가
from langchain_huggingface import HuggingFaceEmbeddings 
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()
# Hugging Face 토큰 경고 방지 (익명 허용)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

class SkinVectorDB:
    def __init__(self):
        # --- [성공 포인트 1] 검증된 임베딩 모델로 교체 ---
        # Google 임베딩 대신, 이전에 성공했던 모델을 사용하여 404 에러를 원천 차단합니다.
        self.model_name = "jhgan/ko-sroberta-multitask"
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name
        )
        # 모델을 처음 실행할 때 한 번 다운로드하며, 이후에는 로컬 캐시를 사용합니다.
        # model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        # self.embeddings = HuggingFaceEmbeddings(
        #     model_name=model_name,
        #     model_kwargs={'device': 'cpu'}, # GPU가 없다면 cpu 강제 지정
        #     encode_kwargs={'normalize_embeddings': True}
        # )
        
        # 저장 경로
        self.persist_directory = os.path.join(os.getcwd(), "chroma_db")

    def clean_text(self, text):
        # --- [성공 포인트 2] 이전 파일의 '최적화 세탁기' 로직 그대로 이식 ---
        # 유니코드 대리쌍(Surrogate)과 제어문자를 제거하여 임베딩 시 발생할 수 있는 치명적인 에러를 방지합니다.
        if not isinstance(text, str):
            text = str(text)
        
        # 1. 유니코드 대리쌍(Surrogate) 제거
        cleaned = re.sub(r'[\ud800-\udfff]', '', text)
        
        # 2. 제어문자 제거
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
        
        # 3. 필수 문장부호 제외 특수기호 공백 치환
        cleaned = re.sub(r'[^\w\s.,?!%()~-]', ' ', cleaned)
        
        # 4. 다중 공백 압축
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

    def upsert_survey_data(self, df):
        if df.empty:
            return "저장할 데이터가 없습니다."

        documents = []
        for idx, row in df.iterrows():
            # 데이터 결합
            content = f"사용자 ID: {row[0]}\n"
            for col, val in row.items():
                content += f"{col}: {val}\n"
            
            # 🔥 저장 전 세탁기 가동 (성공 로직 적용)
            # 저장 직전에 clean_text를 거치도록 설계되어 DB에 깨끗한 데이터만
            cleaned_content = self.clean_text(content)
            
            doc = Document(
                page_content=cleaned_content, 
                metadata={"user_id": str(row[0])}
            )
            documents.append(doc)

        # Chroma DB 저장
        vector_db = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        return f"✅ {len(documents)}건의 데이터가 정제되어 벡터 DB에 저장되었습니다."

    def query_similar_data(self, query, k=3):
        # 검색어도 정제해서 비교
        cleaned_query = self.clean_text(query)
        vector_db = Chroma(
            persist_directory=self.persist_directory, 
            embedding_function=self.embeddings
        )
        return vector_db.similarity_search(cleaned_query, k=k)

if __name__ == "__main__":
    vdb = SkinVectorDB()
    print("✅ OTT 설문 데이터 분석용 벡터 DB 준비 완료")

    test_data = pd.DataFrame([
        ["user_01", "20대", "남성", "넷플릭스, 티빙", "비용 부담으로 해지 고민", "통합 관리 필요"],
        ["user_02", "30대", "여성", "디즈니+", "볼 게 없어서 해지", "신작 알림 필요"]
    ])
    
    print("🚀 정제 및 동기화 시작...")
    result = vdb.upsert_survey_data(test_data)
    print(result)

    print("\n🔍 검색 테스트: '비용이 고민이에요'")
    search_result = vdb.query_similar_data("비용이 고민이에요", k=1)
    
    if search_result:
        print(f"찾은 결과: {search_result[0].page_content[:50]}...")