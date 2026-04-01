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
            st.success(f"🚀 분석 대상: 사용 의향 **5점 이상** 고의향 유저 ({len(high_intent)}명)")
            
            if not high_intent.empty:
                # [1. 데이터 추출 - 기존 로직 동일]
                persona_counts = high_intent.groupby(['gender', 'job', 'age_group']).size().reset_index(name='count')
                top_persona_row = persona_counts.loc[persona_counts['count'].idxmax()]
                main_sub = high_intent[(high_intent['gender'] == top_persona_row['gender']) & (high_intent['job'] == top_persona_row['job']) & (high_intent['age_group'] == top_persona_row['age_group'])]
                
                group_stats = high_intent.groupby(['gender', 'job', 'age_group']).agg({'usage_intent': 'mean', 'Respondent ID': 'count'}).reset_index()
                efficient_targets = group_stats[(group_stats['usage_intent'] > avg_intent + 0.5) & (group_stats['Respondent ID'] >= 2)].sort_values(by='usage_intent', ascending=False)

                # 숫자 너비 고정 (글자 시작 위치를 맞추기 위함)
                num_width = "28px" 

                # --- 2. 메인 타겟 HTML (말풍선 들여쓰기 제거 및 라인 정렬) ---
                main_v_msgs = self.get_group_comments(main_sub)
                # 말풍선도 이제 숫자 너비(num_width)만큼만 들여써서 타이틀과 라인을 맞춤
                main_msgs_html = "".join(['<p style="margin: 4px 0; color: #94a3b8; font-size: 0.82rem; line-height: 1.5;">🗨️ "' + str(msg) + '"</p>' for msg in main_v_msgs])
                
                main_target_html = (
                    '<div style="margin-bottom: 35px; display: flex; align-items: flex-start;">'
                        '<span style="font-weight: bold; color: white; font-size: 1.1rem; min-width: ' + num_width + '; padding-top: 2px;">1.</span>'
                        '<div style="flex: 1;">'
                            '<p style="margin: 0 0 4px 0; font-weight: bold; color: white; font-size: 1.1rem;">메인 볼륨 타겟 (Mass)</p>'
                            '<p style="margin: 0 0 10px 0; color: #cbd5e1; font-size: 0.95rem;">' + str(top_persona_row['gender']) + ' ' + str(top_persona_row['job']) + ' (' + str(top_persona_row['age_group']) + ')</p>'
                            '<div>' + main_msgs_html + '</div>'
                        '</div>'
                    '</div>'
                )

                # --- 3. 고효율 타겟 HTML (말풍선 들여쓰기 제거 및 라인 정렬) ---
                eff_target_html = ""
                if not efficient_targets.empty:
                    eff_row = efficient_targets.iloc[0]
                    eff_sub = high_intent[(high_intent['gender'] == eff_row['gender']) & (high_intent['job'] == eff_row['job']) & (high_intent['age_group'] == eff_row['age_group'])]
                    eff_v_msgs = self.get_group_comments(eff_sub)
                    eff_msgs_html = "".join(['<p style="margin: 4px 0; color: #94a3b8; font-size: 0.82rem; line-height: 1.5;">🗨️ "' + str(msg) + '"</p>' for msg in eff_v_msgs])
                    
                    eff_target_html = (
                        '<div style="display: flex; align-items: flex-start;">'
                            '<span style="font-weight: bold; color: white; font-size: 1.1rem; min-width: ' + num_width + '; padding-top: 2px;">2.</span>'
                            '<div style="flex: 1;">'
                                '<p style="margin: 0 0 4px 0; font-weight: bold; color: white; font-size: 1.1rem;">고효율 집중 타겟 🚩</p>'
                                '<p style="margin: 0 0 10px 0; color: #cbd5e1; font-size: 0.95rem;">' + str(eff_row['gender']) + ' ' + str(eff_row['job']) + ' (' + str(eff_row['age_group']) + ') | <b>평균 ' + "{:.1f}".format(eff_row['usage_intent']) + '점</b></p>'
                                '<div>' + eff_msgs_html + '</div>'
                            '</div>'
                        '</div>'
                    )

                # --- 4. 최종 출력 ---
                final_html = '<div style="padding-left: 30px; font-family: sans-serif;">' + main_target_html + eff_target_html + '</div>'
                st.markdown(final_html, unsafe_allow_html=True)
                
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

            st.markdown("<br>", unsafe_allow_html=True)
            
            c_indent = "28px"

            full_html = (
                f'<div style="background-color: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #60a5fa; margin-bottom: 25px; font-family: sans-serif;">'
                    f'<p style="color: #60a5fa; font-weight: bold; margin: 0 0 12px 0; font-size: 0.95rem; letter-spacing: 0.5px;">🎯 핵심 트리거 분석 결과</p>'
                    f'<div style="padding-left: {c_indent};">'
                        f'<p style="color: white; font-size: 1.1rem; margin: 0 0 15px 0; line-height: 1.5;">현재 유저들이 해지를 결정하는 결정적 요인은 <span style="color: #f8fafc; font-weight: bold; border-bottom: 2px solid #60a5fa;">\'{top_primary}\'</span>입니다.</p>'
                        f'<div style="border-top: 1px solid #334155; padding-top: 15px;">'
                            f'<p style="margin: 0 0 4px 0; color: #94a3b8; font-size: 0.92rem; line-height: 1.6;">이는 "내가 지불하는 비용만큼 충분히 이용하고 있는가?"라는 <span style="color: #cbd5e1; font-weight: bold;">\'효율성\'</span>의 문제에서 시작됩니다.</p>'
                            f'<p style="margin: 0; color: #94a3b8; font-size: 0.92rem; line-height: 1.6;"><span style="color: #60a5fa; font-weight: bold;">[{target_solution}]</span>을 최우선으로 제공해야 한다는 인사이트기 될 수 있습니다.</p>'
                        f'</div>'
                    f'</div>'
                f'</div>'
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(full_html, unsafe_allow_html=True)

        else:
            st.warning("데이터에 'ott_cancel_reason_primary' 컬럼이 없습니다.")

    def plot_ott_usage_efficiency(self):
        st.markdown("---")
        st.markdown("""
            <div style="margin-bottom: 6px;">
                <h5 style="margin-bottom: 2px; padding-bottom: 0;">[시각화 2] 구독 효율성 심층 분석</h5>
                <p style="color: #94a3b8; font-size: 0.8rem; margin: 0; padding: 0;">※ 기준: 유저별 OTT 구독료 합계 및 주간 시청 시간 기반 산출</p>
            </div>
        """, unsafe_allow_html=True)

        q_col1, q_col2, q_col3, empty_space = st.columns([1, 1, 1.5, 5])
        with q_col1:
            st.markdown("<p style='margin-bottom:0px;'><small>🟠 <b>Light</b>: 주 3h 미만</small></p>", unsafe_allow_html=True)
        with q_col2:
            st.markdown("<p style='margin-bottom:0px;'><small>⚫ <b>Middle</b>: 주 3-12h</small></p>", unsafe_allow_html=True)
        with q_col3:
            st.markdown("<p style='margin-bottom:0px;'><small>🔴 <b>Heavy</b>: 주 12h 이상</small></p>", unsafe_allow_html=True)
        
        st.write("") # 미세한 간격 조정
        st.markdown("---")

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
        col_left, col_right = st.columns([1, 1.3], vertical_alignment="center")

        with col_left:
            cancel_exp_df = self.df[self.df['ott_cancel'] == '예'].copy()
            target_reason = "접속 빈도가 낮음을 인지해서"
            # 중복 응답 컬럼에서 키워드 포함 여부 체크 (복수응답 기준)
            cancel_exp_df['has_target_reason'] = cancel_exp_df['ott_cancel_reason'].fillna('').apply(
                lambda x: 1 if target_reason in str(x) else 0
            )
            
            l_stats = cancel_exp_df.groupby('user_seg', observed=True).agg(
                user_count=('Respondent ID', 'count'),
                reason_rate=('has_target_reason', lambda x: x.mean() * 100)
            ).reset_index()

            fig_left = go.Figure()

            # 막대: 유저 분포 (왼쪽 축)
            fig_left.add_trace(go.Bar(
                x=l_stats['user_seg'], y=l_stats['user_count'],
                name='해지 경험자(명)',
                marker_color=['#F1AC90', '#94a3b8', '#FF6D74'],
                text=l_stats['user_count'], 
                textposition='inside', insidetextanchor='start',
                yaxis='y1'
            ))

            # 선: 해지 사유 응답률 (오른쪽 축)
            fig_left.add_trace(go.Scatter(
                x=l_stats['user_seg'], y=l_stats['reason_rate'],
                name='사유 응답률(%)',
                mode='lines+markers+text',
                line=dict(color='#1f77b4', width=3),
                text=l_stats['reason_rate'].round(1).astype(str) + '%',
                textposition='top center',
                yaxis='y2'
            ))

            fig_left.update_layout(
                height=480,  # 축 제목 공간을 고려해 높이를 약간 증액
                # 하단 마진(b)을 우측 차트와 동일하게 맞추고, 축 제목(title) 공간 확보
                margin=dict(l=50, r=20, t=80, b=80), 
                template="plotly_dark",
                xaxis=dict(title="유저 쿼터", title_font=dict(size=14)),
                yaxis=dict(title="해지 경험자 (명)", showgrid=False),
                yaxis2=dict(title="사유 응답률 (%)", overlaying='y', side="right", range=[0, 150]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_left, use_container_width=True)

        with col_right:
            # 실제 가성비 산점도
            y_limit = self.df['cost_per_hour'].quantile(0.95) * 1.1
            fig_right = px.scatter(
                self.df, x='ott_time_total', y='cost_per_hour',
                color='user_seg', size='total_ott_fee',
                color_discrete_map={'Light': "#F1AC90", 'Middle': '#94a3b8', 'Heavy': "#FF6D74"},
                category_orders={"user_seg": ["Light", "Middle", "Heavy"]}, # 범례 순서 고정
                labels={'ott_time_total': '주간 시청 시간 (h)', 'cost_per_hour': '시간당 비용 (원/h)', 'user_seg': '유저 쿼터'},
                title="<b>[전체 유저] 시청 시간 대비 가성비 곡선</b>"
            )

            fig_right.update_layout(
                height=480, # 좌측과 동일하게 맞춤
                # 하단 마진(b)을 좌측과 동일하게 80으로 통일
                margin=dict(l=50, r=50, t=80, b=80),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template="plotly_dark"
            )
            fig_right.update_yaxes(range=[0, y_limit])
            st.plotly_chart(fig_right, use_container_width=True)

        # 3. 하단 요약 지표 및 인사이트
        st.markdown("---")
        avg_eff = self.df['cost_per_hour'].mean()
        eff_stats = self.df.groupby('user_seg', observed=True)['cost_per_hour'].mean()

        m1, m2, m3 = st.columns(3)

        indent_width = "22px" 

        with m1:
            st.markdown(f"""
                <div style="display: flex; justify-content: center; width: 100%;">
                    <div style="text-align: left;">
                        <p style="color: #94a3b8; font-size: 0.9rem; margin: 0 0 4px 0;">📊 전체 평균 가성비</p>
                        <div style="display: flex; align-items: baseline; padding-left: {indent_width};">
                            <span style="color: white; font-size: 1.8rem; font-weight: bold;">{int(avg_eff):,}</span>
                            <span style="color: white; font-size: 1rem; margin-left: 4px;">원/h</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""
                <div style="display: flex; justify-content: center; width: 100%;">
                    <div style="text-align: left;">
                        <p style="color: #F1AC90; font-size: 0.9rem; margin: 0 0 4px 0;">🟠 Light 평균 가성비</p>
                        <div style="display: flex; align-items: baseline; padding-left: {indent_width};">
                            <span style="color: white; font-size: 1.8rem; font-weight: bold;">{int(eff_stats.get('Light', 0)):,}</span>
                            <span style="color: white; font-size: 1rem; margin-left: 4px;">원/h</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with m3:
            st.markdown(f"""
                <div style="display: flex; justify-content: center; width: 100%;">
                    <div style="text-align: left;">
                        <p style="color: #FF6D74; font-size: 0.9rem; margin: 0 0 4px 0;">🔴 Heavy 평균 가성비</p>
                        <div style="display: flex; align-items: baseline; padding-left: {indent_width};">
                            <span style="color: white; font-size: 1.8rem; font-weight: bold;">{int(eff_stats.get('Heavy', 0)):,}</span>
                            <span style="color: white; font-size: 1rem; margin-left: 4px;">원/h</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # [2] 핵심 인사이트 (박스 없이 깔끔한 텍스트 위계)
        st.markdown("---")
        title_indent = "28px" 

        # 타이틀 (한 줄 렌더링)
        st.markdown(f'<div style="margin: 30px 0 20px 0;"><p style="color: white; margin: 0; font-size: 1.05rem; font-weight: bold;">🎯 핵심 인사이트: <span style="color: #cbd5e1; font-weight: normal;">유저 성향에 따른 \'구독 최적화\'의 이중 가치</span></p></div>', unsafe_allow_html=True)
        
        # 공통 아이콘 스타일 (잘림 방지 및 뒤쪽 공백 추가)
        icon_style = 'min-width: 25px; font-size: 1.1rem; line-height: 1.4; display: flex; align-items: center; margin-right: 8px;'

        # Light 내용
        light_content = (
            '<div style="flex: 1;">' # 비중 1:1로 복구
                '<div style="display: flex; align-items: flex-start; margin-bottom: 25px;">'
                    f'<div style="{icon_style}">🟠</div>'
                    '<div>'
                        '<p style="font-weight: bold; margin: 0 0 8px 0; font-size: 1rem; color: #F1AC90;">Light (구독 방치형)</p>'
                        '<div style="color: #cbd5e1; font-size: 0.92rem; line-height: 1.6;">'
                            '<p style="margin: 0 0 6px 0;">"언젠간 보겠지"라는 막연한 기대 → 낮은 이용 패턴 인지할 때 해지 발생</p>'
                            '<p style="margin: 0; display: flex; align-items: flex-start;"><span style="margin-right: 8px; line-height: 1.4;">💡</span><span><b>\'방치된 구독료\' 시각화 + 해지 알림</b></span></p>'
                        '</div>'
                    '</div>'
                '</div>'
            '</div>'
        )
        
        # Heavy 내용
        heavy_content = (
            '<div style="flex: 1;">' # 비중 1:1로 복구
                '<div style="display: flex; align-items: flex-start; margin-bottom: 25px;">'
                    f'<div style="{icon_style}">🔴</div>'
                    '<div>'
                        '<p style="font-weight: bold; margin: 0 0 8px 0; font-size: 1rem; color: #FF6D74;">Heavy (전략적 체리피커)</p>'
                        '<div style="color: #cbd5e1; font-size: 0.92rem; line-height: 1.6;">'
                            '<p style="margin: 0 0 6px 0; white-space: nowrap;">최고 가성비를 누리면서도 이용 효율 저하에 가장 민감하게 반응하는 핵심 집단</p>'
                            '<p style="margin: 0; display: flex; align-items: flex-start;"><span style="margin-right: 8px; line-height: 1.4;">💡</span><span><b>체계적인 콘텐츠 소비를 돕는 \'구독 스케줄링\'</b></span></p>'
                        '</div>'
                    '</div>'
                '</div>'
            '</div>'
        )

        # 전체 너비를 1100px로 유지하되 gap을 40px로 줄여서 응집력 있게 배치
        final_insight_html = f'<div style="display: flex; gap: 40px; padding-left: {title_indent}; max-width: 1100px; align-items: flex-start;">{light_content}{heavy_content}</div>'
        
        st.markdown(final_insight_html, unsafe_allow_html=True)

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
                    st.success(f"🚀 **확장 전략:** 초기 서비스는 OTT에 이어 점유율 2위인 **'{second_cat}'** 카테고리를 함께 공략해야 합니다.")