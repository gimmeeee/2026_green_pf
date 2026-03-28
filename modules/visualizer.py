import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np

class SkinVisualizer:
    def __init__(self, df):
        self.df = df.copy()
        # 데이터 클리닝 및 숫자형 변환
        self.df = self.df.replace(['', 'None', 'nan', None], np.nan)
        
        numeric_cols = ['usage_intent', 'ott_time_total', 'fee_service_total', 'pain_management']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        # 구독 서비스 개수 계산 (service_current_ 접두사 활용)
        self.service_cols = [col for col in self.df.columns if 'service_current_' in col and 'none' not in col]
        
        # 데이터 타입에 상관없이 1/0으로 변환하는 헬퍼 함수
        def to_binary(x):
            if pd.isna(x): return 0
            s = str(x).lower().strip()
            if s in ['true', '1', '1.0', 'y', 'yes', 'checked']: return 1
            return 0

        if self.service_cols:
            # 개별 서비스 컬럼들을 바이너리로 변환
            for col in self.service_cols:
                self.df[col] = self.df[col].apply(to_binary)
            self.df['service_count'] = self.df[self.service_cols].sum(axis=1)
        else:
            self.df['service_count'] = 0

    # --- Part 1: Demographic (응답자 페르소나) ---
    def plot_demographic_all(self):
        st.markdown("#### 🏢 Part 1. 응답자 페르소나 분석")
        st.markdown("##### [시각화 1] 전체 응답자 인구통계 분포")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if 'gender' in self.df.columns:
                fig = px.pie(self.df, names='gender', title="성별 비중", hole=0.3,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if 'age_group' in self.df.columns:
                fig = px.pie(self.df, names='age_group', title="연령대 분포", hole=0.3,
                             color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig, use_container_width=True)
        with col3:
            if 'job' in self.df.columns:
                job_counts = self.df['job'].value_counts()
                fig = px.bar(job_counts, title="직업군 분포", color=job_counts.index,
                             color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig, use_container_width=True)

    def plot_high_intent_persona(self):
        st.markdown("##### [시각화 2] 앱 사용의향(usage_intent) 상위 그룹 분석")
        if 'usage_intent' in self.df.columns:
            high_intent = self.df[self.df['usage_intent'] >= 5]
            
            if not high_intent.empty:
                top_age = high_intent['age_group'].value_counts().idxmax()
                top_job = high_intent['job'].value_counts().idxmax()
                top_gender = high_intent['gender'].value_counts().idxmax()
                
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.pie(high_intent, names='job', title="고관여 그룹의 직업군", color_discrete_sequence=px.colors.sequential.Agsunset)
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig = px.pie(high_intent, names='age_group', title="고관여 그룹의 연령대", color_discrete_sequence=px.colors.sequential.Teal)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.success(f"💡 **인사이트:** 우리 앱의 핵심 타겟은 **'{top_age} {top_gender} {top_job}'** 성향을 가진 그룹입니다.")
            else:
                st.info("앱 사용 의향이 높은 그룹에 대한 데이터가 아직 부족합니다.")

    # --- Part 2: OTT Deep-Dive (대중적 서비스 집중 분석) ---
    def plot_ott_quarter_dist(self):
        st.divider()
        st.markdown("#### 🕒 Part 2. 가장 대중적인 OTT 서비스 집중 분석")
        st.markdown("##### [시각화 1] 쿼터(user_seg)별 입주민 분포")
        
        if 'user_seg' in self.df.columns:
            order = ['Light', 'Middle', 'Heavy']
            counts = self.df['user_seg'].value_counts().reindex(order).fillna(0)
            
            fig = px.bar(x=counts.index, y=counts.values, color=counts.index,
                         title="Light / Middle / Heavy 쿼터 분포",
                         color_discrete_map={'Light': '#93c5fd', 'Middle': '#60a5fa', 'Heavy': '#2563eb'},
                         category_orders={"x": order})
            fig.update_layout(xaxis_title="쿼터(user_seg)", yaxis_title="인원 수")
            st.plotly_chart(fig, use_container_width=True)
            
            max_seg = counts.idxmax() if not counts.empty else "N/A"
            st.info(f"🧐 현재 단지 내에는 **'{max_seg}'** 쿼터 유저가 가장 큰 비중을 차지하고 있습니다.")

    def plot_efficiency_scatter(self):
        st.markdown("##### [시각화 2] 구독 효율성 분석 (산점도)")
        if 'ott_time_total' in self.df.columns and 'fee_service_total' in self.df.columns:
            fig = px.scatter(self.df, x='ott_time_total', y='fee_service_total',
                             color='user_seg', size='service_count',
                             hover_data=['job', 'age_group'],
                             labels={'ott_time_total': '주간 시청 시간 (h)', 'fee_service_total': '월 구독료 (원)', 'user_seg': '유저 쿼터'},
                             title="시청 시간 대비 지출액 관계")
            
            time_limit = 3
            fee_min = 20000
            
            max_y = self.df['fee_service_total'].max() if not self.df.empty else 50000
            fig.add_shape(type="rect", x0=0, y0=fee_min, x1=time_limit, y1=max_y * 1.1,
                          line=dict(color="Red", width=2), fillcolor="LightSalmon", opacity=0.2)
            st.plotly_chart(fig, use_container_width=True)
            
            under_users = self.df[(self.df['ott_time_total'] < time_limit) & (self.df['fee_service_total'] >= fee_min)]
            percent = (len(under_users) / len(self.df)) * 100 if len(self.df) > 0 else 0
            
            if percent > 15:
                st.warning(f"⚠️ **기획 포인트:** '언더유저(Under-user)'가 전체의 **{percent:.1f}%**입니다. 이들을 위한 '구독 다이어트 알림'이 앱의 킬러 콘텐츠가 될 것입니다.")
            else:
                st.success(f"✅ 언더유저 비중이 **{percent:.1f}%**로 낮은 편입니다. 헤비 유저를 위한 관리 편의성에 더 집중할 수 있습니다.")

    def plot_cancel_trigger_analysis(self):
        st.markdown("##### [시각화 3] 해지 트리거 분석 (전체 vs 결정적 사유)")
        col1, col2 = st.columns(2)
        
        # 1. 결정적 해지 사유 (Primary) 데이터 전처리
        primary_reason = "데이터 없음"
        if 'ott_cancel_reason_primary' in self.df.columns:
            valid_p = self.df['ott_cancel_reason_primary'].astype(str).str.strip().replace(['nan', 'None', '', 'nan'], np.nan).dropna()
            if not valid_p.empty:
                primary_counts = valid_p.value_counts()
                primary_reason = primary_counts.idxmax()

        # 2. 전체 해지 사유 (Multiple) 데이터 전처리
        with col1:
            if 'ott_cancel_reason' in self.df.columns:
                reasons = self.df['ott_cancel_reason'].astype(str).str.split(',').explode().str.strip()
                counts = reasons.replace(['nan', 'None', '', 'nan'], np.nan).dropna().value_counts().sort_values(ascending=True)
                
                if not counts.empty:
                    fig = px.bar(counts, orientation='h', title="전체 해지 사유 (전체 응답 집계)", 
                                 labels={'value': '응답 수', 'index': '사유'},
                                 color_discrete_sequence=['#94a3b8'])
                    fig.update_layout(height=400 + (len(counts) * 20))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("다중 응답 해지 사유 데이터가 없습니다.")
        
        with col2:
            if 'ott_cancel_reason_primary' in self.df.columns and not valid_p.empty:
                primary_top = valid_p.value_counts()
                fig = px.pie(values=primary_top.values, names=primary_top.index, hole=0.4, 
                             title="결정적 해지 사유 (분포 전체)", 
                             color_discrete_sequence=px.colors.sequential.Reds)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("결정적 해지 사유 데이터가 없습니다.")
        
        st.info(f"🤖 **AI 분석:** 사람들은 평소 다양한 불만을 이야기하지만, 실제 해지로 이어지는 결정적 한 방은 **'{primary_reason}'**입니다. 우리 앱은 이 문제를 해결하는 방향으로 설계되어야 합니다.")

    # --- Part 3: Hypothesis & Expansion (가설 검증 및 확장성) ---
    def plot_pain_correlation(self):
        st.divider()
        st.markdown("#### 🤯 Part 3. 그 외 주목 포인트 및 가설 검증")
        st.markdown("##### [시각화 1] 구독 관리 어려움의 상관관계 가설 검증")
        
        if 'service_count' in self.df.columns and 'pain_management' in self.df.columns:
            fig = px.scatter(self.df, x='service_count', y='pain_management', size='fee_service_total',
                             color='user_seg',
                             labels={'service_count': '구독 서비스 개수', 'pain_management': '관리 어려움 (7점)', 'user_seg': '쿼터'},
                             title="구독 개수/비용이 높을수록 관리가 어려워질까?")
            st.plotly_chart(fig, use_container_width=True)
            
            correlation = self.df['service_count'].corr(self.df['pain_management'])
            if correlation > 0.4:
                st.error(f"📈 **가설 검증 성공:** 상관계수 {correlation:.2f}로, 구독 개수가 많아질수록 관리 어려움이 유의미하게 증가함이 입증되었습니다.")
            elif correlation > 0.1:
                st.info(f"🧐 **가설 검증 결과:** 상관계수 {correlation:.2f}입니다. 약한 상관관계가 있으나, 개수 외의 요인도 작용하고 있습니다.")
            else:
                st.info(f"🧐 **가설 검증 결과:** 상관계수 {correlation:.2f}입니다. 개수 자체보다는 구독 비용이나 서비스 종류가 피로도에 더 큰 영향을 미칠 수 있습니다.")

    def plot_market_expansion(self):
        st.markdown("##### [시각화 2] 시장 확장성 (카테고리별 점유율)")
        if self.service_cols:
            # 바이너리로 전처리된 데이터 합산
            counts = self.df[self.service_cols].sum().sort_values(ascending=False)
            counts.index = [idx.replace('service_current_', '').upper() for idx in counts.index]
            
            # 데이터가 모두 0인 경우 방지
            if counts.sum() > 0:
                fig = px.bar(x=counts.index, y=counts.values, title="카테고리별 구독 현황", 
                             labels={'x': '카테고리', 'y': '구독자 수'},
                             color=counts.values, color_continuous_scale='Purples')
                # Y축 범위 자동 조절 및 정수 표시
                fig.update_layout(yaxis=dict(tickformat="d"))
                st.plotly_chart(fig, use_container_width=True)
                
                # 순위 분석
                valid_counts = counts[counts > 0]
                if len(valid_counts) > 1:
                    top_2_category = valid_counts.index[1]
                    st.success(f"🚀 **확장 전략:** OTT와 함께 초기 서비스로 내세워야 할 카테고리는 점유율 2위인 **'{top_2_category}'**입니다.")
                else:
                    st.info("OTT 외에 다른 카테고리 구독자가 아직 적습니다.")
            else:
                st.warning("⚠️ 카테고리별 구독 데이터가 모두 0으로 집계되었습니다. 데이터 형식을 확인해주세요.")
        else:
            st.info("분석할 서비스 카테고리 컬럼이 데이터셋에 없습니다.")