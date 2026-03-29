import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np

class SkinVisualizer:
    def __init__(self, df):
        self.df = df.copy()
        
        # 1. 기초 데이터 정리
        self.df = self.df.replace(['', 'None', 'nan', None], np.nan)
        
        # 2. 헬퍼 함수
        def to_binary(x):
            if pd.isna(x): return 0
            s = str(x).lower().strip()
            if s in ['true', '1', '1.0', 'y', 'yes', 'checked', '예']: return 1
            return 0

        # 3. 서비스 개수 계산
        self.service_cols = [col for col in self.df.columns if 'service_current_' in col and 'none' not in col]
        if self.service_cols:
            for col in self.service_cols:
                self.df[col] = self.df[col].apply(to_binary)
            self.df['service_count'] = self.df[self.service_cols].sum(axis=1)
        else:
            self.df['service_count'] = 0

        # 4. 관리 어려움 데이터 치환 (산점도용)
        if 'pain_management' in self.df.columns:
            self.df['pain_num'] = self.df['pain_management'].apply(to_binary)
        else:
            self.df['pain_num'] = 0

        # 5. 기타 수치형 변환
        num_fields = ['usage_intent', 'ott_time_total', 'fee_service_total']
        for field in num_fields:
            if field in self.df.columns:
                self.df[field] = pd.to_numeric(self.df[field], errors='coerce').fillna(0)

    def plot_demographic_all(self):
        st.markdown("#### 🏢 Part 1. 응답자 페르소나 분석")
        st.markdown("##### [시각화 1] 전체 응답자 인구통계 분포")
        col1, col2, col3 = st.columns(3)
        with col1:
            if 'gender' in self.df.columns:
                fig = px.pie(self.df, names='gender', title="성별 비중", hole=0.3, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if 'age_group' in self.df.columns:
                fig = px.pie(self.df, names='age_group', title="연령대 분포", hole=0.3, color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig, use_container_width=True)
        with col3:
            if 'job' in self.df.columns:
                job_counts = self.df['job'].value_counts()
                fig = px.bar(job_counts, title="직업군 분포", color=job_counts.index, color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig, use_container_width=True)

    def plot_high_intent_persona(self):
        st.markdown("##### [시각화 2] 앱 사용의향 상위 그룹 분석")
        if 'usage_intent' in self.df.columns:
            high_intent = self.df[self.df['usage_intent'] >= 5]
            if not high_intent.empty:
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.pie(high_intent, names='job', title="고관여 그룹의 직업군")
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig = px.pie(high_intent, names='age_group', title="고관여 그룹의 연령대")
                    st.plotly_chart(fig, use_container_width=True)

    def plot_ott_quarter_dist(self):
        st.divider()
        st.markdown("#### 🕒 Part 2. OTT 이용 행태 분석")
        if 'user_seg' in self.df.columns:
            order = ['Light', 'Middle', 'Heavy']
            counts = self.df['user_seg'].value_counts().reindex(order).fillna(0)
            fig = px.bar(x=counts.index, y=counts.values, color=counts.index, 
                         title="유저 쿼터별 분포",
                         color_discrete_map={'Light': '#93c5fd', 'Middle': '#3b82f6', 'Heavy': '#1d4ed8'})
            st.plotly_chart(fig, use_container_width=True)

    def plot_efficiency_scatter(self):
        st.markdown("##### [시각화 2] 구독 효율성 분석")
        if 'ott_time_total' in self.df.columns and 'fee_service_total' in self.df.columns:
            # 1. 산점도 생성
            fig = px.scatter(self.df, 
                             x='ott_time_total', 
                             y='fee_service_total', 
                             color='user_seg', 
                             size='service_count',
                             hover_data=['job', 'age_group', 'service_count'], 
                             labels={'ott_time_total': '시청 시간(h)', 'fee_service_total': '월 지출(원)', 'user_seg': '유저 그룹'},
                             title="시간 대비 비용 효율성 (언더유저 분석)",
                             color_discrete_map={'Light': '#60a5fa', 'Middle': '#2563eb', 'Heavy': '#1d4ed8'})

            # 2. 언더유저(Under-user) 강조 영역 추가
            # 시청 시간은 적고(예: 300h 이하), 지출은 높은(예: 6만원 이상) 구역
            fig.add_vrect(x0=0, x1=300, y0=60000, y1=self.df['fee_service_total'].max() * 1.1,
                          fillcolor="red", opacity=0.07, layer="below", line_width=0,
                          annotation_text="비효율 구간 (언더유저)", annotation_position="top left",
                          annotation_font=dict(color="red", size=12))

            # 3. 레이아웃 최적화
            fig.update_layout(plot_bgcolor='rgba(248, 250, 252, 0.5)',
                              xaxis=dict(gridcolor='white'),
                              yaxis=dict(gridcolor='white'))
            
            st.plotly_chart(fig, use_container_width=True)
            st.info("💡 **언더유저 분석:** 붉은 영역에 위치한 사용자는 지출액 대비 사용 시간이 매우 적어, **구독 다이어트 기능**의 핵심 타겟이 됩니다.")

    def plot_cancel_trigger_analysis(self):
        st.markdown("##### [시각화 3] 해지 트리거 분석")
        col1, col2 = st.columns(2)
        with col1:
            if 'ott_cancel_reason' in self.df.columns:
                reasons = self.df['ott_cancel_reason'].astype(str).str.split(',').explode().str.strip()
                counts = reasons.value_counts()
                fig = px.bar(counts, orientation='h', title="전체 해지 사유", color=counts.values, color_continuous_scale='Reds')
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if 'ott_cancel_reason_primary' in self.df.columns:
                counts = self.df['ott_cancel_reason_primary'].value_counts()
                fig = px.pie(values=counts.values, names=counts.index, title="결정적 해지 사유", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)

    def plot_pain_correlation(self):
        st.divider()
        st.markdown("#### 🤯 Part 3. UX 심층 가설 검증")
        st.markdown("##### [시각화 1] 유저의 인지 부하(Cognitive Load)와 지출 부담의 상관관계")
        
        plot_df = self.df.copy()
        plot_df['fee_per_service'] = plot_df['fee_service_total'] / plot_df['service_count'].replace(0, 1)
        
        # 산점도
        fig = px.scatter(plot_df, 
                         x='fee_service_total', 
                         y='service_count',
                         color='pain_num',
                         size='fee_per_service',
                         hover_data={'job': True, 'fee_service_total': ':,.0f'},
                         labels={'fee_service_total': '월 총 구독료(원)', 'service_count': '구독 서비스 개수'},
                         title="구독 피로도 위험군 식별 (Pain Point Cluster)",
                         color_continuous_scale=['#e2e8f0', '#ef4444'])

        # 임계점 가이드라인
        fig.add_shape(type="line", x0=50000, y0=0, x1=50000, y1=plot_df['service_count'].max(),
                      line=dict(color="RoyalBlue", width=2, dash="dot"))
        fig.add_shape(type="line", x0=0, y0=4, x1=plot_df['fee_service_total'].max(), y1=4,
                      line=dict(color="RoyalBlue", width=2, dash="dot"))

        fig.update_layout(plot_bgcolor='white', showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # UX 인사이트 메시지 (불필요한 인용구 제거)
        st.info("""
        🎨 **UX Designer's Insight:**
        - **🔴 빨간색 대형 노드 (우상단):** 지출도 크고 관리 개수도 많은 **'고위험군'**입니다. 이들에게는 자동 결제 내역 추적 및 해지 대행과 같은 **'강력한 자동화'** 기능이 최우선으로 제공되어야 합니다.
        - **⚪ 파란색/회색 소형 노드 (좌하단):** 구독 초기 단계의 유저로, 관리 기능보다는 취향에 맞는 **'콘텐츠 큐레이션'**을 통한 서비스 안착 전략이 유효합니다.
        - **💡 결론:** 지출 금액이 일정 수준(약 5만원)을 넘어서는 순간, 유저는 관리에 대한 심리적 압박을 느끼기 시작하며 '도구'를 찾게 됩니다.
        """)

    def plot_market_expansion(self):
        st.markdown("##### [시각화 2] 카테고리별 구독 점유율")
        if self.service_cols:
            counts = self.df[self.service_cols].sum().sort_values(ascending=False)
            counts.index = [idx.replace('service_current_', '').upper() for idx in counts.index]
            
            plot_df = pd.DataFrame({'카테고리': counts.index, '구독자 수': counts.values})
            
            if not plot_df.empty:
                # 1. 막대 그래프 생성 및 텍스트 표시
                fig = px.bar(plot_df, 
                             x='카테고리', 
                             y='구독자 수', 
                             color='구독자 수',
                             text='구독자 수', # 막대 위에 숫자 표시
                             title="카테고리별 실제 구독자 현황",
                             labels={'카테고리': '서비스 카테고리', '구독자 수': '응답 인원(명)'}, 
                             color_continuous_scale='Purples')
                
                # 2. 텍스트 포맷 및 위치 조정
                fig.update_traces(texttemplate='%{text}명', textposition='outside')
                fig.update_layout(yaxis=dict(tickformat="d", range=[0, plot_df['구독자 수'].max() * 1.2]), 
                                  showlegend=False, plot_bgcolor='white')
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 3. 비즈니스 확장 인사이트 (점유율 2위 강조)
                if len(plot_df) > 1:
                    second_cat = plot_df.iloc[1]['카테고리']
                    st.success(f"🚀 **확장 전략:** OTT 시장은 이미 포화 상태입니다. 결합 상품이나 관리 서비스 확장 시 점유율 2위인 **'{second_cat}'** 카테고리를 우선 공략해야 합니다.")