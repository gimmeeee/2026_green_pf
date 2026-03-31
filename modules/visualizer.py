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

        # 5. 수치형 변환 및 통합 구독료 계산
        num_fields = ['usage_intent', 'ott_time_total', 'fee_service_total']
        for field in num_fields:
            if field in self.df.columns:
                self.df[field] = pd.to_numeric(self.df[field], errors='coerce').fillna(0)

    def plot_demographic_all(self):
        """Part 1: 전체 응답자 분포 (성별/연령/직업 3분할)"""
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

    def get_group_comments(self, sub_df, col_name='usage_expect', max_items=3):
        """특정 그룹의 주관식 응답(usage_expect)에서 의미 없는 답변을 제외하고 추출"""
        if col_name not in sub_df.columns:
            return []
        
        # 1. 기본적인 전처리 (결측치 제거 및 문자열 변환)
        raw_comments = sub_df[col_name].dropna().astype(str).unique().tolist()
        
        # 2. 필터링할 무의미한 단어들 (불용어 설정)
        invalid_texts = [
            '없음', '없습니다', '아니오', '아니요', '생각나지 않음', 
            '딱히', '모름', '모르겠음', '데이터 없음', '않음', '무료'
        ]
        
        # 3. 필터링 로직: 공백 제거 후 글자 수가 너무 적거나 불용어에 포함되면 제외
        filtered_comments = [
            msg for msg in raw_comments 
            if len(msg.strip()) > 2  # 최소 2글자 이상 (ex: '음', '넵' 등 제외)
            and not any(invalid in msg for invalid in invalid_texts)
        ]
        
        return filtered_comments[:max_items]

    def plot_high_intent_persona(self):
        """Part 1 - 시각화 2: 사용 고의향군 심층 분석"""
        st.markdown("##### [시각화 2] 사용 고의향군 심층 분석 (Potential Power Users)")
        
        # 고의향군 필터링 (5점 이상)
        high_intent = self.df[self.df['usage_intent'] >= 5].copy()
        avg_intent = self.df['usage_intent'].mean()
        
        left_col, right_col = st.columns([1.2, 1])

        with left_col:
            # 선버스트 차트: 성별 -> 직업 -> 연령 순으로 계층 구조 시각화
            fig_sun = px.sunburst(
                high_intent, 
                path=['gender', 'job', 'age_group'], 
                values='usage_intent',
                title="고의향군 인구통계 분포 (성별 > 직업 > 연령)",
                color='usage_intent',
                color_continuous_scale='RdBu_r',
                height=700,
            )
            # 퍼센트와 라벨이 함께 나오도록 수정
            fig_sun.update_traces(
                textinfo="label+percent parent",
                hovertemplate='<b>%{label}</b><br>사용의향 합계: %{value}<br>비중: %{percentParent:.1%}'
            )
            st.plotly_chart(fig_sun, use_container_width=True)

        with right_col:
            st.markdown(f"### 🎯 핵심 타겟 리포트")
            st.info(f"💡 전체 응답자 평균 사용 의향: **{avg_intent:.1f}점**")
            st.success(f"🚀 분석 대상: 사용 의향 5점 이상 고의향 유저 (**{len(high_intent)}명**)")
            
            if not high_intent.empty:
                # 1. 메인 페르소나 데이터 추출
                persona_counts = high_intent.groupby(['gender', 'job', 'age_group']).size().reset_index(name='count')
                top_persona_row = persona_counts.loc[persona_counts['count'].idxmax()]
                
                # [추가] 메인 타겟에 해당하는 데이터 필터링
                main_sub = high_intent[
                    (high_intent['gender'] == top_persona_row['gender']) & 
                    (high_intent['job'] == top_persona_row['job']) & 
                    (high_intent['age_group'] == top_persona_row['age_group'])
                ]

                # 2. 고효율 페르소나 데이터 추출
                group_stats = high_intent.groupby(['gender', 'job', 'age_group']).agg({
                    'usage_intent': 'mean',
                    'Respondent ID': 'count'
                }).reset_index()
                
                efficient_targets = group_stats[
                    (group_stats['usage_intent'] > avg_intent + 0.5) & 
                    (group_stats['Respondent ID'] >= 2)
                ].sort_values(by='usage_intent', ascending=False)
                
                # --- 메인 타겟 출력 ---
                st.markdown(f"""
                **1. 메인 볼륨 타겟 (Mass)**
                - **그룹**: {top_persona_row['gender']} {top_persona_row['job']} ({top_persona_row['age_group']})
                """)
                
                # 주관식 답변 출력 (함수 호출)
                main_v_msgs = self.get_group_comments(main_sub) 
                for msg in main_v_msgs:
                    st.caption(f"🗨️ \"{msg}\"")

                # --- 고효율 타겟 출력 ---
                if not efficient_targets.empty:
                    eff_row = efficient_targets.iloc[0]
                    
                    # [추가] 고효율 타겟에 해당하는 데이터 필터링
                    eff_sub = high_intent[
                        (high_intent['gender'] == eff_row['gender']) & 
                        (high_intent['job'] == eff_row['job']) &
                        (high_intent['age_group'] == eff_row['age_group'])
                    ]

                    st.markdown(f"""
                    **2. 고효율 집중 타겟 (Niche & High-Value) 🚩**
                    - **그룹**: **{eff_row['gender']} {eff_row['job']} ({eff_row['age_group']})**
                    - **평균 의향**: **{eff_row['usage_intent']:.1f}점**
                    """)
                    
                    # 주관식 답변 출력 (함수 호출)
                    eff_v_msgs = self.get_group_comments(eff_sub) 
                    for msg in eff_v_msgs:
                        st.caption(f"🗨️ \"{msg}\"")
                
            else:
                st.warning("분석할 데이터가 부족합니다.")

    def plot_cancel_trigger_analysis(self):
        st.markdown("##### [시각화 1] 해지 트리거 분석")
        col1, col2 = st.columns(2)
        
        # 공통 레이아웃 설정
        common_layout = dict(
            coloraxis_showscale=False,
            showlegend=False,
            xaxis_title="응답 수",
            yaxis_title=None,
            height=450,
            margin=dict(l=220, r=20, t=50, b=50) # 긴 텍스트를 위한 왼쪽 여백 통일
        )

        # --- [col1] 전체 해지 사유 (복수 응답) ---
        with col1:
            if 'ott_cancel_reason' in self.df.columns:
                # 데이터 처리
                reasons = self.df['ott_cancel_reason'].astype(str).str.split(',').explode().str.strip()
                reasons = reasons[reasons.str.lower() != 'nan']
                counts = reasons.value_counts().sort_values(ascending=True)
                
                # 차트 생성
                fig = px.bar(counts, orientation='h', title="전체 해지 사유 (복수 응답)", 
                             color=counts.values, color_continuous_scale='Reds')
                
                # 레이아웃 적용
                line_widths = [1 if val <= 5 else 0 for val in counts.values]
                fig.update_traces(
                    marker_line_width=line_widths, # 계산된 리스트 적용
                    marker_line_color='lightgrey', # 연한 회색 테두리
                    text=counts.values,
                    textposition='outside',
                    cliponaxis=False
                )
                fig.update_layout(**common_layout)
                fig.update_yaxes(automargin=True)
                st.plotly_chart(fig, use_container_width=True)
                
        # --- [col2] 결정적 해지 사유 (단수 응답) ---
        with col2:
            if 'ott_cancel_reason_primary' in self.df.columns:
                primary_series = self.df['ott_cancel_reason_primary'].astype(str).str.strip()
                primary_series = primary_series[primary_series.str.lower() != 'nan']
                counts_p = primary_series.value_counts().sort_values(ascending=True)
            
                fig_p = px.bar(counts_p, orientation='h', title="결정적 해지 사유 (단일 응답)",
                            color=counts_p.values, color_continuous_scale='Blues')
            
                line_widths_p = [1 if val <= 5 else 0 for val in counts_p.values] 
                fig_p.update_traces(
                    marker_line_width=line_widths_p, 
                    marker_line_color='lightgrey',
                    text=counts_p.values, # 이제 단수 응답 숫자가 제대로 나옵니다
                    textposition='outside',
                    cliponaxis=False
                )
                fig_p.update_layout(**common_layout)
                fig_p.update_yaxes(automargin=True)
                st.plotly_chart(fig_p, use_container_width=True)

        if 'ott_cancel_reason_primary' in self.df.columns:
            
            # 가장 높은 비중의 결정적 사유 가져오기
            primary_counts = self.df['ott_cancel_reason_primary'].value_counts()
            top_primary = primary_counts.index[0] if not primary_counts.empty else "비용 부담"

            solution_dict = {
                "접속 빈도가 낮음을 인지해서": "유저의 시청 데이터를 분석해 '돈만 내고 안 보는 서비스'를 선제적으로 알려주는 기능",
                "비싸서": "구독료 합산 관리 및 인원 모집을 통한 계정 공유/할인 최적화 제안",
                "보고싶은 콘텐츠가 적거나 없어서": "여러 OTT의 신작 및 종료 예정작을 통합하여 볼거리를 끊임없이 추천하는 기능",
                "다른 OTT를 이용하기 위해": "기존 OTT의 일시 정지(해지)와 신규 OTT 가입을 원클릭으로 전환해주는 스케줄링 기능",
                "보던 시리즈가 끝나서": "시리즈 완결 시점에 맞춰 자동 해지 예약을 돕거나 다음 관심작을 찾아주는 알림 기능",
                "자동결제 알림을 보고 (앱 push, 카드결제 문자 등)": "결제일 3일 전 미리 알림을 주고, 불필요한 결제를 막아주는 결제 방어 기능"
            }
            
            # 매칭되는 솔루션 문구 (없으면 기본값)
            target_solution = solution_dict.get(top_primary, "유저의 Pain-point를 즉각 해결하는 맞춤형 관리 도구")

            st.info(f"🎯 **Insight: 현재 해지 결정의 핵심 트리거는 '{top_primary}'입니다.**")
            
            st.markdown(f"""
            유저가 해지를 결심하는 본질적인 이유는 '내가 지불하는 비용만큼 충분히 이용하고 있는가?'라는 **효율성의 문제**에서 시작됩니다.<br>
            이는 우리가 [<b>{target_solution}</b>]을 제공해야 한다는 인사이트가 될 수 있습니다.
            """, unsafe_allow_html=True)

            st.markdown("<br><br>", unsafe_allow_html=True)

        else:
            st.warning("데이터에 'ott_cancel_reason_primary' 컬럼이 없습니다.")

    def plot_ott_usage_efficiency(self):
        st.markdown("##### [시각화 2] 구독 효율성 분석")

        with st.expander("💡 시청 쿼터(Engagement Level) 정의 및 분석 기준", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.markdown("**🌱 Light **\n\n주 3시간 미만 시청.\n가성비가 낮고 이탈 리스크가 높음")
            c2.markdown("**🌿 Middle **\n\n주 3~12시간 시청.\n안정적인 이용 행태를 보이는 메인 볼륨")
            c3.markdown("**🔥 Heavy **\n\n주 12시간 이상 시청.\n다수 서비스 구독 중이나 시간당 비용은 최저")
            st.caption("※ 효율성 분석은 유저가 지불하는 모든 OTT 구독료 합계(넷플릭스, 티빙 등)를 기준으로 산출되었습니다.")

        # 1. 총 구독료 계산 (제시된 모든 OTT 컬럼 합산)
        fee_cols = [
            'ott_fee_netflix', 'ott_fee_tving', 'ott_fee_wavve', 
            'ott_fee_disney', 'ott_fee_couplay', 'ott_fee_watcha', 
            'ott_fee_laftel', 'ott_fee_etc'
        ]

        # 데이터프레임에 해당 컬럼이 있는지 확인 후 합산 (결측치는 0 처리)
        available_fee_cols = [c for c in fee_cols if c in self.df.columns]

        for col in available_fee_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)

        self.df['total_ott_fee'] = self.df[available_fee_cols].sum(axis=1)

        self.df['cost_per_hour'] = self.df.apply(
            lambda x: x['total_ott_fee'] / x['ott_time_total'] if x['ott_time_total'] > 0 else 0, 
            axis=1
        )
        
        if 'user_seg' in self.df.columns:
            # 공백 제거 및 첫 글자만 대문자로 변환 (예: middle -> Middle)
            self.df['user_seg'] = self.df['user_seg'].astype(str).str.strip().str.capitalize()
            
            # 카테고리 순서 고정 (그래프 정렬용)
            self.df['user_seg'] = pd.Categorical(
                self.df['user_seg'], 
                categories=['Light', 'Middle', 'Heavy'], 
                ordered=True
            )

        # 2. 차트 레이아웃 분할 (좌: 분포 막대, 우: 효율성 산점도)
        col_left, col_right = st.columns([1, 1.5])

        with col_left:
            # 유저 쿼터별 분포 (세로 막대)
            if 'user_seg' in self.df.columns:
                order = ['Light', 'Middle', 'Heavy']
                counts = self.df['user_seg'].value_counts().reindex(order).fillna(0).reset_index()
                counts.columns = ['Segment', 'Count']
                
                fig_bar = px.bar(
                    counts, x='Segment', y='Count', color='Segment',
                    text='Count',
                    color_discrete_map={'Light': '#cbd5e1', 'Middle': '#94a3b8', 'Heavy': '#E50914'},
                    title="시청 쿼터별 유저 분포"
                )

                fig_bar.update_traces(texttemplate='%{text}명', textposition='outside')
                fig_bar.update_layout(showlegend=False, yaxis_title="응답자 수", height=450)
                st.plotly_chart(fig_bar, use_container_width=True)

        with col_right:
            # 실제 가성비 산점도
            y_limit = self.df['cost_per_hour'].quantile(0.95) * 1.1
            fig_scat = px.scatter(
                self.df, x='ott_time_total', y='cost_per_hour',
                color='user_seg' if 'user_seg' in self.df.columns else None,
                size='total_ott_fee',
                hover_data=['total_ott_fee', 'gender', 'age_group'],
                color_discrete_map={'Light': '#cbd5e1', 'Middle': '#94a3b8', 'Heavy': '#E50914'},
                labels={'ott_time_total': '주간 시청 시간 (h)', 'cost_per_hour': '시간당 비용 (원/h)'},
                title="시청 시간 대비 구독 효율성 (가성비 곡선)"
            )

            fig_scat.update_layout(
                height=500,
                # 여백(margin)을 충분히 주어 축 라벨이 잘리지 않게 함
                margin=dict(l=50, r=20, t=60, b=50),
                # 범례를 차트 상단으로 옮겨서 가로 공간 확보
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # 축 범위 조정
            fig_scat.update_yaxes(range=[0, y_limit], gridcolor='#f0f0f0')
            fig_scat.update_xaxes(gridcolor='#f0f0f0')
            
            st.plotly_chart(fig_scat, use_container_width=True)

        # 3. 하단 요약 지표 및 인사이트
        avg_total_fee = self.df['total_ott_fee'].mean()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("평균 총 구독료", f"{int(avg_total_fee):,}원")
        
        if 'user_seg' in self.df.columns:
            eff_stats = self.df.groupby('user_seg')['cost_per_hour'].mean()
            if 'Heavy' in eff_stats:
                m2.metric("Heavy 평균 가성비", f"{int(eff_stats['Heavy']):,}원/h", "최고 효율")
            if 'Light' in eff_stats:
                m3.metric("Light 평균 가성비", f"{int(eff_stats['Light']):,}원/h", "최저 효율", delta_color="inverse")

        st.success(f"""
        **💡 분석 결과 요약:**
        - 유저들은 평균적으로 월 **{int(avg_total_fee):,}원**의 OTT 구독료를 지불하고 있습니다.
        - **Heavy 유저**는 다소 높은 구독료를 지불함에도 불구하고, 압도적인 이용량 덕분에 가장 낮은 시간당 비용을 보입니다.
        - **Light 유저**의 경우 시간당 비용이 {int(eff_stats['Light']):,}원으로 매우 높아, 경제적 관점에서 가장 먼저 구독 해지를 고려할 확률이 높은 집단입니다.
        """)

    def plot_segment_reason_correlation(self):
        """유저 세그먼트(시청 쿼터)별 해지 사유 연결 분석"""
        st.markdown("##### [시각화 3] 시청 쿼터별 해지 사유 심층 연결")
        
        # 1. 데이터 준비 여부 확인
        if 'user_seg' not in self.df.columns or 'ott_cancel_reason_primary' not in self.df.columns:
            st.warning("세그먼트 데이터 또는 해지 사유 데이터가 부족합니다.")
            return

        target_reason = "접속 빈도가 낮음을 인지해서"
        
        # 2. 분석용 임시 데이터프레임 생성
        # 'user_seg'는 카테고리형이므로 문자열로 변환하여 처리
        analysis_df = self.df.copy()
        analysis_df['is_target_reason'] = (analysis_df['ott_cancel_reason_primary'] == target_reason)
        
        # 3. 그룹별 응답 비중 계산 (%)
        # 각 세그먼트 내에서 해당 사유를 선택한 사람의 비율 산출
        segment_stats = analysis_df.groupby('user_seg', observed=True)['is_target_reason'].mean() * 100
        segment_stats = segment_stats.reset_index()
        segment_stats.columns = ['Segment', 'Response_Rate']

        # 4. 시각화 (그룹별 막대 차트)
        fig = px.bar(
            segment_stats, 
            x='Segment', 
            y='Response_Rate',
            text='Response_Rate',
            color='Segment',
            title=f"유저 그룹별 '{target_reason}' 선택 비중",
            labels={'Response_Rate': '선택 비중 (%)', 'Segment': '시청 쿼터'},
            color_discrete_map={'Light': '#E50914', 'Middle': '#94a3b8', 'Heavy': '#cbd5e1'} # Light를 강조
        )

        fig.update_traces(
            texttemplate='%{text:.1f}%', 
            textposition='outside'
        )
        
        fig.update_layout(
            yaxis_title="결정적 사유 응답 비중 (%)",
            showlegend=False,
            height=400,
            margin=dict(t=50, b=50)
        )

        # 5. 화면 배치
        col_chart, col_text = st.columns([1.5, 1])
        
        with col_chart:
            st.plotly_chart(fig, use_container_width=True)
            
        with col_text:
            st.markdown(f"### 🧐 연결 인사이트")
            
            # 데이터에 따른 동적 메시지 생성
            light_rate = segment_stats.loc[segment_stats['Segment'] == 'Light', 'Response_Rate'].values[0]
            heavy_rate = segment_stats.loc[segment_stats['Segment'] == 'Heavy', 'Response_Rate'].values[0]
            
            diff_factor = light_rate / heavy_rate if heavy_rate > 0 else 0

            st.write(f"""
            - **가설 검증**: 가성비 곡선에서 확인한 최저 효율 집단(**Light**)은 실제로 **'{target_reason}'**을 해지 사유로 꼽는 비율이 가장 높게 나타납니다.
            - **결과**: Light 유저의 응답률은 **{light_rate:.1f}%**로, Heavy 유저({heavy_rate:.1f}%) 대비 약 **{diff_factor:.1f}배** 높은 수치를 보입니다.
            - **전략**: 이는 '이용량 부족'이 단순한 느낌이 아니라, 실제 **구독료에 대한 손실감**으로 이어져 해지를 실행하게 만드는 핵심 기제임을 증명합니다.
            """)

    def plot_pain_correlation(self):
        st.divider()
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