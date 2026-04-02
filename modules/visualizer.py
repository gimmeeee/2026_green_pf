import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np
from config import BRAND_COLORS

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

        # 6. 차트 레이아웃 설정
        self.common_layout = dict(
            title_font_color=BRAND_COLORS.SUB_TEXT,
            plot_bgcolor=BRAND_COLORS.TRANSPARENT,
            paper_bgcolor=BRAND_COLORS.TRANSPARENT,
        )

    def plot_demographic_all(self):
        """Part 1: 전체 응답자 분포 (성별/연령/직업 3분할)"""
        st.markdown(f"<h5 style='font-weight:600; margin-bottom:6px;'>📊 1. 전체 응답자 인구통계 분포</h5>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        demo_layout_base = {
            **self.common_layout,
            "margin": dict(t=40, b=40, l=10, r=10),
            "showlegend": True
        }
        
        with col1:
            if 'gender' in self.df.columns:
                fig_gen = px.pie(self.df, names='gender', title="성별 비중", hole=0.6,
                                 color_discrete_sequence=BRAND_COLORS.CHART_CATEGORICAL)
                # 범례 위치만 추가 설정 (타이틀 컬러는 common_layout에서 자동으로 적용)
                fig_gen.update_layout(**demo_layout_base, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                fig_gen.update_traces(hovertemplate="gender= <b>%{label}</b><br>%{value}<extra></extra>")
                st.plotly_chart(fig_gen, use_container_width=True, config={'displayModeBar': False})
                
        with col2:
            if 'age_group' in self.df.columns:
                age_counts = self.df['age_group'].value_counts().reset_index()
                age_counts.columns = ['age_group', 'count']
                fig_age = px.pie(age_counts, names='age_group', values='count', title="연령대 분포", hole=0.6,
                                 color_discrete_sequence=BRAND_COLORS.CHART_CATEGORICAL)
                
                # fig_age 변수로 정확히 호출
                fig_age.update_layout(**demo_layout_base, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                fig_age.update_traces(hovertemplate="age_group= <b>%{label}</b><br>%{value}<extra></extra>")
                st.plotly_chart(fig_age, use_container_width=True, config={'displayModeBar': False})
                
        with col3:
            if 'job' in self.df.columns:
                job_counts = self.df['job'].value_counts().reset_index()
                job_counts.columns = ['job', 'count']
                fig_job = px.bar(job_counts, x='job', y='count', title="직업군 분포", 
                                 color_discrete_sequence=BRAND_COLORS.CHART_MAIN)
                
                # 공통 레이아웃 적용 후 바 차트 특화 설정만 덮어쓰기
                fig_job.update_layout(**demo_layout_base)
                fig_job.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
                
                fig_job.update_traces(hovertemplate="job= <b>%{x}</b><br>%{y}<extra></extra>", marker_line_width=0)
                st.plotly_chart(fig_job, use_container_width=True, config={'displayModeBar': False})


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
        for _ in range(4): st.write("")
        st.markdown(f"<h5 style='font-weight:600; margin-bottom:6px;'>📊 2. 사용 고의향군 심층 분석 (Potential Power Users)</h5>", unsafe_allow_html=True)
        
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
                color='usage_intent', # 수치형 데이터
                color_continuous_scale=BRAND_COLORS.SUNBURST_SCALE,
                height=700,
            )
            fig_sun.update_layout(**self.common_layout,
                margin=dict(t=40, b=20, l=20, r=20), 
                coloraxis_showscale=False,
            )
            # 퍼센트와 라벨이 함께 나오도록 수정
            fig_sun.update_traces(
                textinfo="label+percent parent",
                hovertemplate='<b>%{label}</b><br>사용의향 합계: %{value}<br>비중: %{percentParent:.1%}',
                marker_line_width=1.5,
                marker_line_color="rgba(255, 255, 255, 0.3)", 
                insidetextorientation='radial',
            )
            st.plotly_chart(fig_sun, use_container_width=True)

        with right_col:
            if not high_intent.empty:
                # 1. 데이터 추출
                persona_counts = high_intent.groupby(['gender', 'job', 'age_group']).size().reset_index(name='count')
                top_p = persona_counts.loc[persona_counts['count'].idxmax()]
                main_sub = high_intent[(high_intent['gender'] == top_p['gender']) & (high_intent['job'] == top_p['job']) & (high_intent['age_group'] == top_p['age_group'])]
                
                group_stats = high_intent.groupby(['gender', 'job', 'age_group']).agg({'usage_intent': 'mean', 'Respondent ID': 'count'}).reset_index()
                eff_targets = group_stats[(group_stats['usage_intent'] > avg_intent + 0.5) & (group_stats['Respondent ID'] >= 2)].sort_values(by='usage_intent', ascending=False)

                # --- 2. CSS 스타일 정의 ---
                st.markdown("""
                    <style>
                    .report-container { margin-top: 60px; font-family: sans-serif; padding-left: 15px; }
                    .report-title { color: #0D9488 !important; font-size: 1.4rem; margin-bottom: 18px; font-weight: 700; }
                    .summary-box { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; margin-bottom: 35px; }
                    
                    /* border-left를 없애는 대신 padding-left를 22px 주어 들여쓰기 유지 */
                    .target-card { display: flex; align-items: flex-start; margin-bottom: 40px; padding-left: 22px; }
                    
                    .target-num { font-weight: bold; font-size: 1.15rem; min-width: 32px; color: #64748b !important; }
                    .target-label { font-weight: bold; font-size: 1.15rem; margin: 0 0 4px 0; color: #1e293b !important; }
                    .target-desc { margin: 0 0 10px 0; color: #475569 !important; font-size: 0.95rem; }
                    .needs-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; margin-right: 8px; vertical-align: middle; }
                    .needs-text { margin: 6px 0; color: #64748b !important; font-size: 0.88rem; line-height: 1.6; }
                    .point-mint { color: #0D9488 !important; font-weight: bold; }
                            
                    /* 사용자가 다크모드일 때만 적용되는 설정 */
                    @media (prefers-color-scheme: dark) {
                        .report-container { color: #E2E8F0; }
                        .summary-box { 
                            background-color: #1E293B; 
                            border: 1px solid #334155; 
                        }
                        .target-label { color: #F8FAFC !important; }
                        .target-desc { color: #94A3B8 !important; }
                        .needs-text { color: #CBD5E1 !important; }
                    }
                    </style>
                """, unsafe_allow_html=True)

                # --- 3. HTML 조립 (포매팅 없이 순수 문자열 결합) ---
                
                # [메인 타겟 리스트]
                main_items = ""
                for msg in self.get_group_comments(main_sub):
                    main_items += '<p class="needs-text"><span class="needs-badge" style="background-color: #F1F5F9; color: #475569;">Needs</span> "' + str(msg) + '"</p>'

                # [고효율 타겟 섹션]
                eff_section = ""
                if not eff_targets.empty:
                    eff_row = eff_targets.iloc[0]
                    eff_sub = high_intent[(high_intent['gender'] == eff_row['gender']) & (high_intent['job'] == eff_row['job']) & (high_intent['age_group'] == eff_row['age_group'])]
                    eff_items = ""
                    for msg in self.get_group_comments(eff_sub):
                        eff_items += '<p class="needs-text"><span class="needs-badge" style="background-color: #F1F5F9; color: #475569;">Needs</span> "' + str(msg) + '"</p>'
                    
                    eff_section = '<div class="target-card">' + \
                                  '<span class="target-num">2.</span>' + \
                                  '<div style="flex: 1;">' + \
                                  '<p class="target-label">고효율 집중 타겟 🚩</p>' + \
                                  '<p class="target-desc">' + str(eff_row["gender"]) + ' ' + str(eff_row["job"]) + ' (' + str(eff_row["age_group"]) + ') | <span class="point-mint">평균 ' + str(round(eff_row["usage_intent"], 1)) + '점</span></p>' + \
                                  '<div>' + eff_items + '</div>' + \
                                  '</div></div>'

                # [최종 통합 출력]
                final_html = '<div class="report-container">' + \
                             '<h3 class="report-title">🎯 핵심 타겟 리포트</h3>' + \
                             '<div class="summary-box"><p style="margin: 0; color: #475569 !important; font-size: 0.95rem; line-height: 1.8;">' + \
                             '<span style="margin-left: 3px; margin-right: 9.5px;">💡</span> 전체 응답자 평균 사용 의향: <b>' + str(round(avg_intent, 1)) + '점</b><br>' + \
                             '<span style="margin-right: 8px;">🚀</span> 분석 대상: 사용 의향 <span class="point-mint">5점 이상</span> 고의향 유저 (' + str(len(high_intent)) + '명)</p></div>' + \
                             '<div class="target-card">' + \
                             '<span class="target-num">1.</span>' + \
                             '<div style="flex: 1;">' + \
                             '<p class="target-label">메인 볼륨 타겟 (Mass)</p>' + \
                             '<p class="target-desc">' + str(top_p["gender"]) + ' ' + str(top_p["job"]) + ' (' + str(top_p["age_group"]) + ')</p>' + \
                             '<div>' + main_items + '</div></div></div>' + \
                             eff_section + '</div>'

                st.markdown(final_html, unsafe_allow_html=True)
                
            else:
                st.warning("분석 데이터가 부족합니다.")

    def plot_cancel_trigger_analysis(self):
        st.markdown(f"<h5 style='font-weight:600; margin-bottom:6px;'>📊 1. 해지 트리거 분석</h5>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        # --- # --- [col1] 전체 해지 사유 ---
        with col1:
            if 'ott_cancel_reason' in self.df.columns:
                # 데이터 전처리 (nan 제거 및 카운트)
                reasons = self.df['ott_cancel_reason'].astype(str).str.split(',').explode().str.strip()
                reasons = reasons[reasons.str.lower() != 'nan']
                counts = reasons.value_counts().sort_values(ascending=True)
                
                borders = ['#E0E0E0' if v <= 5 else 'rgba(0,0,0,0)' for v in counts.values]
                line_widths = [1 if v <= 5 else 0 for v in counts.values]

                fig = px.bar(counts, orientation='h', template=None,
                             color=counts.values, 
                             color_continuous_scale=["#FFF6F5", "#FACEC8", "#F1A197"]) # 연함 -> 진함
                
                fig.update_traces(
                    text=counts.values, textposition='outside', textfont=dict(size=12), 
                    cliponaxis=False,
                    marker=dict(line=dict(color=borders, width=line_widths))
                )

                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    title=dict(text="<b>전체 해지 사유 (복수 응답)</b>", font=dict(size=16, color=BRAND_COLORS.SUB_TEXT), x=0, y=0.98, xanchor='left', yanchor='top'),
                    xaxis=dict(title=dict(text="응답 수", font=dict(size=12)), tickfont=dict(size=12), gridcolor="#F0F0F0", showgrid=True, zeroline=False),
                    yaxis=dict(title=None, tickfont=dict(size=12), showline=False, automargin=True, ticksuffix="   "),
                    height=450, margin=dict(l=50, r=50, t=50, b=50), 
                    showlegend=False,
                    coloraxis_showscale=False # 우측 컬러바 제거
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, theme=None)
                
        with col2:
            if 'ott_cancel_reason_primary' in self.df.columns:
                primary_series = self.df['ott_cancel_reason_primary'].astype(str).str.strip()
                primary_series = primary_series[primary_series.str.lower() != 'nan']
                counts_p = primary_series.value_counts().sort_values(ascending=True)
            
                borders_p = ['#E0E0E0' if v <= 5 else 'rgba(0,0,0,0)' for v in counts.values]
                line_widths_p = [1 if v <= 5 else 0 for v in counts.values]

                fig_p = px.bar(counts_p, orientation='h', template=None,
                               color=counts_p.values,
                               color_continuous_scale=["#ECFFF9", "#ABE6D6", "#0BB085"])
        
                fig_p.update_traces(
                    text=counts_p.values, textposition='outside', textfont=dict(size=12), 
                    cliponaxis=False,
                    marker=dict(line=dict(color=borders_p, width=line_widths_p))
                )

                fig_p.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    title=dict(text="<b>결정적 해지 사유 (단일 응답)</b>", font=dict(size=16, color=BRAND_COLORS.SUB_TEXT), x=0, y=0.98, xanchor='left', yanchor='top'),
                    xaxis=dict(title=dict(text="응답 수", font=dict(size=12)), tickfont=dict(size=12), gridcolor="#F0F0F0", showgrid=True, zeroline=False),
                    yaxis=dict(title=None, tickfont=dict(size=12), showline=False, automargin=True, ticksuffix="   "),
                    height=450, margin=dict(l=50, r=50, t=50, b=50),
                    showlegend=False,
                    coloraxis_showscale=False # 우측 컬러바 제거
                )
                st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False}, theme=None)

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
                f'<div style="background-color: #F0FDFA; padding: 22px; border-radius: 12px; border-left: 5px solid #2DD4BF; margin-bottom: 25px; font-family: sans-serif; border: 1px solid #CCFBF1;">'
                    f'<p style="color: #0D9488; font-weight: bold; margin: 0 0 12px 0; font-size: 0.95rem; letter-spacing: 0.5px;">🎯 핵심 트리거 분석 결과</p>'
                    f'<div style="padding-left: {c_indent};">'
                        f'<p style="color: #111827; font-size: 1.1rem; margin: 0 0 15px 0; line-height: 1.5; font-weight: 600;">현재 유저들이 해지를 결정하는 결정적 요인은 <span style="color: #0D9488; font-weight: bold; border-bottom: 2px solid #2DD4BF;">\'{top_primary}\'</span>입니다.</p>'
                        f'<div style="border-top: 1px solid #CCFBF1; padding-top: 15px;">'
                            f'<p style="margin: 0 0 8px 0; color: #374151; font-size: 0.92rem; line-height: 1.6;">이는 "내가 지불하는 비용만큼 충분히 이용하고 있는가?"라는 <span style="color: #059669; font-weight: bold;">\'효율성\'</span>의 문제에서 시작됩니다.</p>'
                            f'<p style="margin: 0; color: #374151; font-size: 0.92rem; line-height: 1.6;"><span style="color: #0D9488; font-weight: bold;">[{target_solution}]</span>을 최우선으로 제공해야 한다는 인사이트를 줍니다.</p>'
                        f'</div>'
                    f'</div>'
                f'</div>'
            )

            st.markdown(full_html, unsafe_allow_html=True)

        else:
            st.warning("데이터에 'ott_cancel_reason_primary' 컬럼이 없습니다.")

    def plot_ott_usage_efficiency(self):
        st.markdown("---")
        st.markdown("""
            <div style="margin-bottom: 6px;">
                <h5 style="margin-bottom: 4px; padding-bottom: 0;">📊 2. 구독 효율성 심층 분석</h5>
                <p style="color: #94a3b8; font-size: 0.8rem; margin: 0; padding: 0;">※ 기준: 유저별 OTT 구독료 합계 및 주간 시청 시간 기반 산출</p>
            </div>
        """, unsafe_allow_html=True)

        # 2. HTML로 범례 한 줄 배치 (gap을 직접 조절 가능)
        st.markdown("""
            <div style="display: flex; gap: 32px; align-items: center; margin-top: 6px; margin-bottom: 10px;">
                <span style="font-size: 0.8rem;">🟠 <b>Light</b>: 주 3h↓</span>
                <span style="font-size: 0.8rem;">⚫ <b>Middle</b>: 주 3-12h</span>
                <span style="font-size: 0.8rem;">🔴 <b>Heavy</b>: 주 12h↑</span>
            </div>
        """, unsafe_allow_html=True)
        
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
                name='해지 경험자 (명)',
                marker_color=['#F1AC90', "#c5cbd3", '#FF6D74'],
                text=l_stats['user_count'], 
                textposition='inside', insidetextanchor='start',
                yaxis='y1'
            ))

            # 선: 해지 사유 응답률 (오른쪽 축)
            fig_left.add_trace(go.Scatter(
                x=l_stats['user_seg'], y=l_stats['reason_rate'],
                name='해지 사유 응답률 (%)',
                mode='lines+markers+text',
                line=dict(color=BRAND_COLORS.MAIN_MINT, width=3), # Config 참조
                marker=dict(size=8, color=BRAND_COLORS.MAIN_MINT, line=dict(color='white', width=1)),
                text=l_stats['reason_rate'].round(1).astype(str) + '%',
                textposition='top center',
                textfont=dict(color=BRAND_COLORS.MAIN_MINT, size=11), # 텍스트 색상까지 통일
                yaxis='y2'
            ))

            fig_left.update_layout(
                height=480,  # 축 제목 공간을 고려해 높이를 약간 증액
                # 하단 마진(b)을 우측 차트와 동일하게 맞추고, 축 제목(title) 공간 확보
                margin=dict(l=50, r=60, t=80, b=80), 
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                # [수정] 타이틀 추가: 해지 경험자 & 민감도 키워드 반영
                title=dict(
                    text="<b>[해지 경험자] '접속 빈도 낮음' 선택률</b>",
                    font=dict(size=16, color=BRAND_COLORS.SUB_TEXT),
                    x=0, y=0.98, xanchor='left', yanchor='top'
                ),
                xaxis=dict(title="유저 쿼터", title_font=dict(size=13), tickfont=dict(size=12), zeroline=False),
                yaxis=dict(title="해지 경험자 (명)", title_font=dict(size=12), showgrid=True, gridcolor="#F0F0F0", zeroline=False),
                yaxis2=dict(
                    # [수정] standoff를 추가하여 텍스트 겹침 방지
                    title=dict(text="해지 사유 응답률 (%)", font=dict(size=12), standoff=15), 
                    overlaying='y', 
                    side="right", 
                    range=[0, 100],
                    showgrid=False, 
                    zeroline=False,
                    automargin=True  # 여백 자동 계산 활성화
                ),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                showlegend=True
            )
            st.plotly_chart(fig_left, use_container_width=True, theme=None) # theme=None으로 테마 고정

        with col_right:
            # 1. 가성비 산점도 생성 (변수명: fig_right)
            y_limit = self.df['cost_per_hour'].quantile(0.95) * 1.1
            
            fig_right = px.scatter(
                self.df, x='ott_time_total', y='cost_per_hour',
                color='user_seg', size='total_ott_fee',
                color_discrete_map={'Light': "#F1AC90", 'Middle': '#c5cbd3', 'Heavy': "#FF6D74"},
                category_orders={"user_seg": ["Light", "Middle", "Heavy"]},
                labels={'ott_time_total': '주간 시청 시간 (h)', 'cost_per_hour': '시간당 비용 (원/h)', 'user_seg': '유저 쿼터'}
            )

            # 2. 레이아웃 업데이트 (이제 fig_right가 정의되었으므로 에러가 나지 않습니다)
            fig_right.update_layout(
                height=480,
                margin=dict(l=50, r=50, t=80, b=80),
                paper_bgcolor="rgba(0,0,0,0)", # 배경 투명화
                plot_bgcolor="rgba(0,0,0,0)",  # 차트 영역 투명화
                title=dict(
                    text="<b>[전체 응답자] 시청 시간 대비 가성비 곡선</b>",
                    font=dict(size=16, color=BRAND_COLORS.SUB_TEXT), # 왼쪽과 색상/크기 통일
                    x=0, y=0.98, xanchor='left', yanchor='top'
                ),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(
                    title_font=dict(size=13), 
                    tickfont=dict(size=12), 
                    gridcolor="#F0F0F0", 
                    zeroline=False
                ),
                yaxis=dict(
                    range=[0, y_limit], 
                    title_font=dict(size=13), 
                    tickfont=dict(size=12), 
                    gridcolor="#F0F0F0", 
                    zeroline=False
                )
            )
            
            # 3. 차트 출력 (theme=None 필수)
            st.plotly_chart(fig_right, use_container_width=True, theme=None)

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
                        <p style="font-size: 0.9rem; margin: 0 0 4px 0;">⚫ 전체 평균 가성비</p>
                        <div style="display: flex; align-items: baseline; padding-left: {indent_width};">
                            <span style="font-size: 1.8rem; font-weight: bold;">{int(avg_eff):,}</span>
                            <span style="font-size: 1rem; margin-left: 4px;">원/h</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""
                <div style="display: flex; justify-content: center; width: 100%;">
                    <div style="text-align: left;">
                        <p style="color: #f79872; font-size: 0.9rem; margin: 0 0 4px 0;">🟠 Light 평균 가성비</p>
                        <div style="display: flex; align-items: baseline; padding-left: {indent_width};">
                            <span style="font-size: 1.8rem; font-weight: bold;">{int(eff_stats.get('Light', 0)):,}</span>
                            <span style="font-size: 1rem; margin-left: 4px;">원/h</span>
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
                            <span style="font-size: 1.8rem; font-weight: bold;">{int(eff_stats.get('Heavy', 0)):,}</span>
                            <span style="font-size: 1rem; margin-left: 4px;">원/h</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # [2] 핵심 인사이트 (박스 없이 깔끔한 텍스트 위계)
        st.markdown("---")
        icon_style = 'min-width: 25px; font-size: 1.1rem; line-height: 1.4; display: flex; align-items: center; margin-right: 8px;'
        desc_style = 'font-size: 0.92rem; line-height: 1.6;'

        # 2. 전체를 중앙으로 모으는 컨테이너 렌더링
        st.markdown(f'''
            <div style="max-width: 1100px; margin: 0 auto; padding: 0 20px;">
                
                <div style="margin: 30px 0 30px 0; text-align: center;">
                    <h5 style="margin: 0; font-size: 1.05rem; font-weight: bold;">
                        🎯 핵심 인사이트: <span style="font-weight: normal;">유저 성향에 따른 '구독 최적화'의 이중 가치</span>
                    </h5>
                </div>

                <div style="display: flex; gap: 60px; justify-content: center; align-items: flex-start;">
                    
                    <div style="flex: 1; min-width: 300px;">
                        <div style="display: flex; align-items: flex-start; margin-bottom: 25px;">
                            <div style="{icon_style}">🟠</div>
                            <div>
                                <p style="font-weight: bold; margin: 0 0 8px 0; font-size: 1rem; color: #f79872;">Light (구독 방치형)</p>
                                <div style="{desc_style}">
                                    <p style="margin: 0 0 6px 0;">"언젠간 보겠지"라는 막연한 기대 → 낮은 이용 패턴 인지할 때 해지 발생</p>
                                    <p style="margin: 0; display: flex; align-items: flex-start;">
                                        <span style="margin-left: 2px; margin-right: 8px; line-height: 1.4;">💡</span>
                                        <span><b>'방치된 구독료' 시각화 + 해지 알림</b></span>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div style="flex: 1; min-width: 300px;">
                        <div style="display: flex; align-items: flex-start; margin-bottom: 25px;">
                            <div style="{icon_style}">🔴</div>
                            <div>
                                <p style="font-weight: bold; margin: 0 0 8px 0; font-size: 1rem; color: #FF6D74;">Heavy (전략적 체리피커)</p>
                                <div style="{desc_style}">
                                    <p style="margin: 0 0 6px 0;">최고 가성비를 누리면서도 이용 효율 저하에 가장 민감하게 반응하는 핵심 집단</p>
                                    <p style="margin: 0; display: flex; align-items: flex-start;">
                                        <span style="margin-left: 2px; margin-right: 8px; line-height: 1.4;">💡</span>
                                        <span><b>체계적인 콘텐츠 소비를 돕는 '구독 스케줄링'</b></span>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        ''', unsafe_allow_html=True)

    def plot_pain_correlation(self):
        st.markdown(f"<h5 style='font-weight:600; margin-bottom:6px;'>📊 1. 구독 비용 및 개수와 관리 피로도의 관계</h5>", unsafe_allow_html=True)
        
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
        st.markdown(f"<h5 style='font-weight:600; margin-bottom:6px;'>📊 2. 구독 카테고리별 점유율</h5>", unsafe_allow_html=True)
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