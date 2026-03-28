## 🎯 RAG 성능 평가 지표 (RAGAS Framework)

본 프로젝트는 구글 시트 데이터를 기반으로 한 챗봇의 답변 정확도를 객관적으로 검증하기 위해 **RAGAS(RAG Assessment)** 프레임워크의 4가지 핵심 지표를 채택하여 관리합니다. 단순히 답변을 생성하는 것에 그치지 않고, 데이터의 근거(Ground Truth)와 생성된 답변 간의 논리적 일치성을 수치화합니다.

### 📊 주요 평가 메트릭 (Metrics)

| 지표 (Metrics) | 평가 대상 | 핵심 정의 | 산출 방식 (Concept) |
| :--- | :---: | :--- | :--- |
| **Faithfulness** | **Generation** | 답변이 컨텍스트(시트 데이터)에만 근거하는가? | $\frac{\text{Number of faithful claims}}{\text{Total number of claims in answer}}$ |
| **Answer Relevance** | **Generation** | 답변이 사용자의 질문 의도에 직접적으로 부합하는가? | 질문과 답변 간의 코사인 유사도(Cosine Similarity) 측정 |
| **Context Precision** | **Retrieval** | 질문과 관련된 데이터가 검색 결과 상단에 위치하는가? | 검색된 문서 중 실제 정답과 관련된 문서의 정밀도 가중치 |
| **Context Recall** | **Retrieval** | 정답 도출에 필요한 정보가 시트에서 모두 검색되었는가? | $\frac{\text{Attributed claims in ground truth}}{\text{Total claims in ground truth}}$ |



### 🛠 성능 최적화 프로세스

1. **Data Structuring**: 구글 폼으로 수집된 질문/응답 탭 데이터를 Pandas를 통해 정제 및 로드합니다.
2. **Retrieval Strategy**: 구글 API를 통해 실시간 데이터를 동기화하며, 질문의 의도에 맞는 최적의 컨텍스트를 추출합니다.
3. **LLM-as-a-Judge**: 고성능 모델(GPT-4o 등)을 평가자로 활용하여 생성된 답변을 위 4가지 지표로 자동 채점합니다.
4. **Visualization Feedback**: 스트림릿(Streamlit) 대시보드에서 분석된 예측 데이터와 RAGAS 지표를 시각화하여 데이터의 신뢰도를 실시간으로 모니터링합니다.

> **💡 Project Insight**
> 웹 퍼블리싱 경험을 바탕으로 데이터 시각화(Matplotlib, Seaborn)를 선행하여 데이터의 편향성을 제거하였으며, 이를 통해 **Faithfulness(충실도)** 점수를 극대화하는 것에 집중하였습니다.

## 📅 Development Process & Timeline

프로젝트는 데이터의 신뢰성 확보와 사용자 경험(UX) 최적화를 위해 총 4단계의 스프린트로 진행되었습니다.

| 단계 | 기간 | 주요 과제 (Key Tasks) | 산출물 |
| :--- | :---: | :--- | :--- |
| **Phase 1. Planning** | Week 1 | 구글 폼 설계 및 데이터 수집 구조 정의 | 데이터 스키마 정의서 |
| **Phase 2. Data Eng.** | Week 2 | Google Sheets API 연동 및 Pandas 데이터 전처리 | 정제된 데이터프레임 |
| **Phase 3. AI & Visual** | Week 3 | RAG 엔진 구축 및 Seaborn/Matplotlib 시각화 | LangChain 기반 챗봇 |
| **Phase 4. Deploy** | Week 4 | Streamlit 배포 및 RAGAS 기반 성능 평가 | 실시간 웹 서비스 |

---

## 🛠️ Key Stack & Methods

### 1. Data Pipeline & Visualization
구글 시트의 동적 데이터를 실시간으로 핸들링하기 위한 핵심 라이브러리와 메서드를 활용합니다.
* **`gspread`**: 서비스 계정 인증을 통한 시트 데이터 Read/Write (JSON Key 관리)
* **`Pandas`**: `df.groupby()`, `df.describe()`를 통한 데이터 통계 분석 및 전처리
* **`Seaborn / Matplotlib`**: 질문 빈도(Countplot), 응답 시간(Lineplot) 등 예측 모델의 근거가 되는 시각화 자료 생성

### 2. LangChain Engine (RAG)
단순한 질의응답을 넘어 데이터 기반의 예측(Prediction)을 수행하는 구조입니다.
* **`create_pandas_dataframe_agent`**: 시각화된 데이터프레임을 LLM이 직접 쿼리하여 통계적 답변 생성
* **`RecursiveCharacterTextSplitter`**: 응답 탭의 긴 텍스트를 의미 단위로 분할하여 검색 효율 증대
* **`OpenAIEmbeddings` & `FAISS`**: 고차원 벡터 임베딩 및 고속 유사도 검색(Similarity Search)

### 3. Deployment & Security
* **`Streamlit`**: `st.chat_message`, `st.sidebar`를 활용한 인터랙티브 대시보드 구현
* **`python-dotenv`**: API Key 및 구글 자격증명 경로를 환경 변수(`.env`)로 격리하여 보안 강화
* **`GitHub Actions`**: 코드 변경 시 스트림릿 클라우드와 자동 동기화(CI/CD)

---

## 🔍 Key Implementation Logic

### 데이터 기반 예측 시나리오 (Example)
1.  **Input**: "특정 카테고리의 문의가 증가할 시점은 언제인가요?"
2.  **Logic**: 
    - `Pandas Agent`가 시트 내 시계열 데이터를 분석
    - `Matplotlib`으로 트렌드 차트 생성 후 사용자에게 전시
    - `LangChain`이 차트 분석 결과와 과거 응답 패턴을 결합하여 예측 답변 생성
3.  **Output**: 시각화 그래프와 함께 구체적인 예측 수치 제공

## 🏗️ System Architecture

이 프로젝트는 구글 시트의 실시간 데이터를 기반으로 시각화 분석과 AI 예측을 결합한 RAG 시스템입니다.

```mermaid
graph TD
    A[Google Form] -->|Data Entry| B(Google Sheets)
    B -->|API Fetch| C{Data Processing}
    C -->|Visualization| D[Streamlit Dashboard]
    C -->|Vectorizing| E[LangChain RAG Engine]
    E -->|Context Retrieval| F[LLM - GPT-4o]
    F -->|Prediction/Answer| G[Chatbot UI]
    G -->|User Feedback| B

