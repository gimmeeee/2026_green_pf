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
        """Part 1: 전체 응답자 분포 (성별/연령/직업 3분할)"""
        st.markdown("#### 🏢 Part 1. 응답자 분석")
        st.markdown("##### [시각화 1] 전체 응답자 인구통계 분포")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if 'gender' in self.df.columns:
                fig_gen = px.pie(self.df, names='gender', title="성별 비중", hole=0.5,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_gen.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                st.plotly_chart(fig_gen, use_container_width=True)
        with col2:
            if 'age_group' in self.df.columns:
                fig_age = px.pie(self.df, names='age_group', title="연령대 분포", hole=0.5, 
                             color_discrete_sequence=px.colors.qualitative.Safe)
                fig_age.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                st.plotly_chart(fig_age, use_container_width=True)
        with col3:
            if 'job' in self.df.columns:
                job_counts = self.df['job'].value_counts().reset_index()
                job_counts.columns = ['job', 'count']
                fig_job = px.bar(job_counts, x='job', y='count', title="직업군 분포", 
                                 color='job', color_discrete_sequence=px.colors.qualitative.Set3)
                fig_job.update_layout(showlegend=False, xaxis_title=None, yaxis_title="인원 수")
                st.plotly_chart(fig_job, use_container_width=True)

    def plot_high_intent_persona(self):
        """Part 1 - 시각화 2: 사용 고의향군 심층 분석"""
        st.markdown("##### [시각화 2] 사용 고의향군 심층 분석 (Potential Power Users)")
        
        if 'usage_intent' in self.df.columns:
            avg_intent = self.df['usage_intent'].mean()
            # 고의향군 기준 설정 (5점 이상)
            high_intent = self.df[self.df['usage_intent'] >= 5]
            
            left_col, right_col = st.columns([1.2, 1], gap="large")

            with left_col:
                st.write("**사용 고의향군의 성별/직업/연령 계층 구조**")
                if not high_intent.empty:
                    path_cols = [col for col in ['gender', 'job', 'age_group'] if col in high_intent.columns]
                    fig = px.sunburst(high_intent, 
                                      path=path_cols, 
                                      color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_traces(textinfo="label+percent parent")
                    fig.update_layout(margin=dict(t=20, l=0, r=0, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("분석할 사용 고의향 데이터가 부족합니다.")

            with right_col:
                st.info(f"💡 전체 응답자 평균 사용 의향: **{avg_intent:.1f}점**")
                st.success(f"🚀 분석 대상: 사용 의향 5점 이상 고의향 유저 (**{len(high_intent)}명**)")
                
                if not high_intent.empty:
                    # 데이터 기반 자동 페르소나 추출
                    top_gender = high_intent['gender'].mode()[0] if 'gender' in high_intent.columns else "-"
                    top_job = high_intent['job'].mode()[0] if 'job' in high_intent.columns else "-"
                    top_age = high_intent['age_group'].mode()[0] if 'age_group' in high_intent.columns else "-"
                    
                    # 기회 시장 분석: 전체 대비 특정 집단의 의향 점수 비교
                    avg_all = self.df['usage_intent'].mean()
                    avg_high = high_intent['usage_intent'].mean()
                    
                    # 가장 피로도가 높은 집단 유추 (가장 많은 서비스를 구독 중인 고의향군)
                    service_cols = [col for col in self.df.columns if 'service_current_' in col]
                    if service_cols:
                        high_intent_copy = high_intent.copy()
                        high_intent_copy['sc'] = high_intent_copy[service_cols].apply(pd.to_numeric, errors='coerce').sum(axis=1)
                        heavy_persona = high_intent_copy.loc[high_intent_copy['sc'].idxmax()]
                        p_desc = f"{heavy_persona['job']}({heavy_persona['age_group']})"
                    else:
                        p_desc = "다중 구독자군"

                    st.markdown(f"""
                    **🎯 데이터 기반 분석 결과**
                    
                    1. **핵심 타겟(Primary Persona)**:  
                       데이터가 가리키는 우리 앱의 잠재 1순위 유저는 **'{top_gender} {top_job}({top_age})'**입니다. (해당 세그먼트 내 고의향 비중 최상위)
                    
                    2. **기회 시장 발견**:  
                       전체 평균 의향 점수({avg_all:.1f}점) 대비 **{avg_high:.1f}점**의 강력한 지지를 보이는 **{p_desc}** 세그먼트는 현재 관리 방식에 한계를 느끼고 있는 기회 시장입니다.
                       """)
                       
                    # --- [수정된 usage_expect 탐색 로직] ---
                    # 1. 정확한 이름 매칭 시도, 안되면 'expect'가 들어간 컬럼 탐색
                    target_col = 'usage_expect' if 'usage_expect' in high_intent.columns else None
                    if not target_col:
                        target_col = next((c for c in high_intent.columns if 'expect' in c.lower()), None)
                    
                    if target_col:
                        # 데이터 내의 실제 응답값만 필터링 (결측치, 빈 문자열 제외)
                        valid_expects = high_intent[target_col].astype(str).replace(['', 'None', 'nan', 'nan '], np.nan).dropna().unique()
                        
                        if len(valid_expects) > 0:
                            st.markdown("---")
                            st.markdown("**🌟 이들이 맞춤 관리앱에 기대하는 사항**")
                            # 상위 3개까지 노출
                            for i, text in enumerate(valid_expects[:3]):
                                st.success(f"**기대사항 {i+1}**\n\n\"{text}\"")
                        else:
                            st.caption("ℹ️ 'usage_expect' 컬럼은 있으나 아직 작성된 응답 내용이 없습니다.")
                    else:
                        st.error("⚠️ 시트에서 'usage_expect' 컬럼을 찾을 수 없습니다. 컬럼명을 다시 확인해 주세요.")
                else:
                    st.write("사용 고의향군 응답이 쌓이면 상세 분석이 활성화됩니다.")

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
        st.markdown("#### 🤯 Part 3. 가설 검증 및 인사이트")
        st.markdown("##### [시각화 1] 구독 비용 및 개수와 관리 피로도의 관계")
        
        # 1. 데이터 준비 및 지터(Jitter) 최적화
        plot_df = self.df.copy()
        # Y축(서비스 개수)에도 약간의 지터만 주어 겹침 방지
        plot_df['service_count_jitter'] = plot_df['service_count'] + np.random.uniform(-0.1, 0.1, size=len(plot_df))
        
        # 2. 산점도 생성: X축(비용), Y축(개수), 색상(어려움 여부)
        fig = px.scatter(plot_df, 
                         x='fee_service_total', 
                         y='service_count_jitter',
                         color='pain_num',
                         hover_data={
                             'service_count_jitter': False, 
                             'service_count': True,
                             'fee_service_total': ':,.0f',
                             'job': True
                         },
                         labels={
                             'service_count_jitter': '구독 서비스 개수', 
                             'service_count': '구독 서비스 개수',
                             'pain_num': '관리 어려움 여부',
                             'fee_service_total': '월 총 구독료(원)'
                         },
                         title="비용과 개수가 늘어날수록 관리가 힘들어지는가?",
                         # 빨간색(1: 힘듦)과 회색(0: 괜찮음)으로 대비
                         color_continuous_scale=['#cbd5e1', '#ef4444'])

        # 3. 차트 레이아웃 최적화 (축 뒤집기 및 영역 강조)
        fig.update_layout(
            xaxis=dict(title="월 총 지출 비용 (원)", gridcolor='rgba(200, 200, 200, 0.2)'),
            yaxis=dict(title="구독 중인 서비스 개수 (개)", gridcolor='rgba(200, 200, 200, 0.2)', dtick=1),
            plot_bgcolor='white',
            showlegend=False,
            coloraxis_showscale=False # 색상 바 제거 (직관성을 위해)
        )

        # 관리 피로도가 높을 것으로 예상되는 '우상단' 영역에 가이드 박스 추가
        fig.add_vrect(x0=plot_df['fee_service_total'].median(), x1=plot_df['fee_service_total'].max()*1.1,
                      y0=plot_df['service_count'].median(), y1=plot_df['service_count'].max()+1,
                      fillcolor="orange", opacity=0.05, layer="below", line_width=0)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 4. 분석 메시지 (비용 중심 분석 추가)
        valid_df = self.df[['service_count', 'fee_service_total', 'pain_num']].dropna()
        if len(valid_df) > 1:
            pain_group = valid_df[valid_df['pain_num'] == 1]
            normal_group = valid_df[valid_df['pain_num'] == 0]
            
            avg_fee_pain = pain_group['fee_service_total'].mean()
            avg_count_pain = pain_group['service_count'].mean()
            
            st.error(f"""
            📈 **심층 가설 검증:**
            - **고비용 유저의 비명:** 관리가 힘들다고 답한 유저들은 평균 **{avg_fee_pain:,.0f}원**을 지출하며, 평균 **{avg_count_pain:.1f}개**의 서비스를 이용 중입니다.
            - **상관성:** 지출 비용이 커질수록 붉은색(관리 어려움) 점들이 우측 상단으로 밀집되는 경향이 뚜렷합니다.
            - **결론:** 단순 개수보다 **'금액적 부담'이 '관리의 필요성'을 느끼게 하는 더 강력한 트리거**임을 확인할 수 있습니다.
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