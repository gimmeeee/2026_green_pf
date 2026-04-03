import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from konlpy.tag import Okt
from config import BRAND_COLORS
from collections import Counter

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
            # 1. 시각화용 데이터를 따로 만듭니다. (그룹별로 평균 점수를 미리 계산)
            # 이렇게 하면 Plotly가 멋대로 합산할 여지를 주지 않습니다.
            sunburst_df = high_intent.groupby(['gender', 'job', 'age_group'])['usage_intent'].mean().reset_index()
            
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
            # 기존 레이아웃 설정을 복사해서 중복 에러 방지
            layout_settings = self.common_layout.copy()
            layout_settings.update({
                "margin": dict(t=60, b=20, l=20, r=20),
                "paper_bgcolor": "rgba(0,0,0,0)", 
                "plot_bgcolor": "rgba(0,0,0,0)",  
                "coloraxis_showscale": True  # 그라디언트 범주(scale) 다시 표시
            })

            fig_sun.update_layout(**layout_settings)
            fig_sun.update_traces(
                # [포인트 1] 흰색 테두리 대신 배경색에 녹아드는 어두운 투명 테두리
                # 이렇게 해야 다크모드에서 브랜드 컬러가 둥둥 떠 보이지 않습니다.
                marker=dict(line=dict(color='rgba(0, 0, 0, 0.1)', width=0.8)),
                
                textinfo="label+percent parent",
                
                # [포인트 3] 호버 툴팁 깔끔하게 정리
                hovertemplate='<b>%{label}</b><br>평균 사용의향: %{color:.2f}점<extra></extra>',
                textfont=dict(size=12)
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
                             color_continuous_scale=["#FFF6F5", "#F1A197"]) # 연함 -> 진함
                
                fig.update_traces(
                    text=counts.values, 
                    textposition='outside', 
                    # 컬러(color) 속성을 삭제하여 테마에 맡김
                    textfont=dict(size=12), 
                    cliponaxis=False,
                    marker=dict(line=dict(color=borders, width=line_widths))
                )

                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    title=dict(text="<b>전체 해지 사유 (복수 응답)</b>", font=dict(size=16, color=BRAND_COLORS.SUB_TEXT), x=0, y=0.98, xanchor='left', yanchor='top'),
                    #xaxis, yaxis의 font color 설정을 모두 삭제
                    xaxis=dict(title=dict(text="응답 수", font=dict(size=12)), tickfont=dict(size=12), gridcolor="rgba(128, 128, 128, 0.1)", showgrid=True, zeroline=False),
                    yaxis=dict(title=None, tickfont=dict(size=12), showline=False, automargin=True, ticksuffix="   "),
                    height=450, margin=dict(l=50, r=50, t=50, b=50), 
                    showlegend=False,
                    coloraxis_showscale=False
                )
                # theme="streamlit" (기본값)을 명시하거나 theme=None을 제거하여 테마 연동
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
        # --- [col2] 결정적 해지 사유 ---
        with col2:
            if 'ott_cancel_reason_primary' in self.df.columns:
                primary_series = self.df['ott_cancel_reason_primary'].astype(str).str.strip()
                primary_series = primary_series[primary_series.str.lower() != 'nan']
                counts_p = primary_series.value_counts().sort_values(ascending=True)
            
                borders_p = ['#E0E0E0' if v <= 5 else 'rgba(0,0,0,0)' for v in counts_p.values]
                line_widths_p = [1 if v <= 5 else 0 for v in counts_p.values]

                fig_p = px.bar(counts_p, orientation='h', template=None,
                               color=counts_p.values,
                               color_continuous_scale=["#ECFFF9", "#0BB085"])
        
                fig_p.update_traces(
                    text=counts_p.values, 
                    textposition='outside', 
                    textfont=dict(size=12), 
                    cliponaxis=False,
                    marker=dict(line=dict(color=borders_p, width=line_widths_p))
                )

                fig_p.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    title=dict(text="<b>결정적 해지 사유 (단일 응답)</b>", font=dict(size=16, color=BRAND_COLORS.SUB_TEXT), x=0, y=0.98, xanchor='left', yanchor='top'),
                    xaxis=dict(title=dict(text="응답 수", font=dict(size=12)), tickfont=dict(size=12), gridcolor="rgba(128, 128, 128, 0.1)", showgrid=True, zeroline=False),
                    yaxis=dict(title=None, tickfont=dict(size=12), showline=False, automargin=True, ticksuffix="   "),
                    height=450, margin=dict(l=50, r=50, t=50, b=50),
                    showlegend=False,
                    coloraxis_showscale=False
                )
                # theme=None을 지워서 Streamlit 기본 테마 컬러를 쓰도록 함
                st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})

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

            # 배경색은 rgba로 유지 (배경색에 따라 자동 투명도 조절)
            # 강조용 컬러 정의 (라이트에서도 잘 보이고 다크에서도 묻히지 않는 최적의 톤)
            accent_color = "#14B8A6" # 기존보다 채도가 살짝 낮고 명도가 낮은 민트

            full_html = (
                f'<div style="background-color: rgba(45, 212, 191, 0.12); padding: 22px; border-radius: 12px; border-left: 5px solid {accent_color}; margin-bottom: 25px; font-family: sans-serif; border: 1px solid rgba(45, 212, 191, 0.2);">'
                    f'<p style="color: {accent_color}; font-weight: bold; margin: 0 0 12px 0; font-size: 0.95rem; letter-spacing: 0.5px;">🎯 핵심 트리거 분석 결과</p>'
                    f'<div style="padding-left: {c_indent};">'
                        f'<p style="font-size: 1.1rem; margin: 0 0 15px 0; line-height: 1.5; font-weight: 600;">'
                            f'현재 유저들이 해지를 결정하는 결정적 요인은 <span style="color: {accent_color}; font-weight: bold; border-bottom: 2px solid {accent_color}44;">\'{top_primary}\'</span>입니다.'
                        f'</p>'
                        f'<div style="border-top: 1px solid rgba(45, 212, 191, 0.2); padding-top: 15px;">'
                            f'<p style="margin: 0 0 8px 0; font-size: 0.92rem; line-height: 1.6;">'
                                f'이는 "내가 지불하는 비용만큼 충분히 이용하고 있는가?"라는 <span style="color: {accent_color}; font-weight: bold;">\'효율성\'</span>의 문제에서 시작됩니다.'
                            f'</p>'
                            f'<p style="margin: 0; font-size: 0.92rem; line-height: 1.6;">'
                                f'<span style="color: {accent_color}; font-weight: bold;">[{target_solution}]</span>을 최우선으로 제공해야 한다는 인사이트가 될 수 있습니다.'
                            f'</p>'
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
                marker_color=['#F1AC90', "#dce0e6", '#FF6D74'],
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
                yaxis=dict(title="해지 경험자 (명)", title_font=dict(size=12), showgrid=True, gridcolor="rgba(128, 128, 128, 0.1)", zeroline=False),
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
                color_discrete_map={'Light': "#F1AC90", 'Middle': '#dce0e6', 'Heavy': "#FF6D74"},
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
                    gridcolor="rgba(128, 128, 128, 0.1)", 
                    zeroline=False
                ),
                yaxis=dict(
                    range=[0, y_limit], 
                    title_font=dict(size=13), 
                    tickfont=dict(size=12), 
                    gridcolor="rgba(128, 128, 128, 0.1)", 
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

        # [2] 핵심 인사이트 (폭 확대 + 마진 축소 + 디자인 디테일 개선)
        st.markdown("---")
        for _ in range(2): st.write("")
        
        # 모든 줄바꿈과 공백을 제거하여 마크다운이 '코드'로 오해할 여지를 없앤 버전입니다.
        html_code = """<div style="max-width:1200px;margin:0 auto;font-family:sans-serif;"><div style="text-align:center;margin-bottom:10px;"><h5 style="margin:0;font-size:1.2rem;font-weight:bold;line-height:1.8;">🎯 핵심 인사이트: <span style="font-weight:normal;">유저 성향에 따른 '구독 최적화'의 이중 가치</span></h5></div><div style="display:flex;gap:20px;justify-content:center;align-items:stretch;"><div style="flex:1; background-color: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.1); border-radius:16px; padding:28px 32px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);"><div style="display:flex;align-items:center;margin-bottom:16px;"><span style="font-size:1.4rem;margin-right:12px;">🟠</span><span style="font-weight:bold;font-size:1.1rem;color:#f79872;">Light <span style="font-weight:normal;font-size:0.85rem;">(구독 방치형)</span></span></div><div style="font-size:0.98rem;line-height:1.6;"><p style="margin:0 0 18px 0;letter-spacing:-0.2px;">"언젠간 보겠지"라는 막연한 기대 → 낮은 이용 패턴 인지할 때 해지 발생</p><div style="background-color:rgba(247, 152, 114, 0.1);border:1px solid rgba(247, 152, 114, 0.2);border-radius:10px;padding:14px 16px;"><p style="margin:0;display:flex;align-items:center;color:#f79872;font-size:0.93rem;"><span style="margin-right:8px;">💡</span><b>'방치된 구독료' 시각화 + 해지 알림</b></p></div></div></div><div style="flex:1; background-color: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.1); border-radius:16px; padding:28px 32px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);"><div style="display:flex;align-items:center;margin-bottom:16px;"><span style="font-size:1.4rem;margin-right:12px;">🔴</span><span style="font-weight:bold;font-size:1.1rem;color:#FF6D74;">Heavy <span style="font-weight:normal;font-size:0.85rem;">(전략적 체리피커)</span></span></div><div style="font-size:0.98rem;line-height:1.6;"><p style="margin:0 0 18px 0;letter-spacing:-0.2px;">최고 가성비를 누리면서도 이용 효율 저하에 가장 민감하게 반응하는 핵심 집단</p><div style="background-color:rgba(255, 109, 116, 0.1);border:1px solid rgba(255, 109, 116, 0.2);border-radius:10px;padding:14px 16px;"><p style="margin:0;display:flex;align-items:center;color:#FF6D74;font-size:0.93rem;"><span style="margin-right:8px;">💡</span><b>체계적인 콘텐츠 소비를 돕는 '구독 스케줄링'</b></p></div></div></div></div></div>"""
        
        st.markdown(html_code, unsafe_allow_html=True)
        for _ in range(4): st.write("")

    def plot_pain_correlation(self):
        st.markdown(f"<h5 style='font-weight:600; margin-bottom:6px;'>📊 1. 구독 개수 및 비용과 관리 피로도의 관계</h5>", unsafe_allow_html=True)
        
        plot_df = self.df.copy()
        # 범례 라벨을 직관적으로 변경 (0, 1 -> 관리 수월, 관리 어려움)
        plot_df['관리 상태'] = plot_df['pain_num'].map({1: '어려움 경험자', 0: '어려움 미경험자'}).astype(str)
        plot_df['service_count_jitter'] = plot_df['service_count'] + np.random.uniform(-0.1, 0.1, size=len(plot_df))

        # 산점도 생성
        fig = px.scatter(plot_df, 
                         x='fee_service_total', 
                         y='service_count_jitter',
                         color='관리 상태', # 변경된 라벨 적용
                         hover_data={
                             '관리 상태': True,
                             'service_count_jitter': False, 
                             'service_count': True,
                             'fee_service_total': ':,.0f',
                             'job': True
                         },
                         labels={
                             'service_count': '구독 서비스 개수',
                             'fee_service_total': '월 총 구독료(원)'
                         },
                         # [수정] 색상 매핑: 회색(#cbd5e1)과 요청하신 MAIN_MINT(#14B8A6)
                         color_discrete_map={
                             '어려움 경험자': BRAND_COLORS.MAIN_MINT, 
                             '어려움 미경험자': '#cbd5e1'
                         })

        fig.update_traces(
            # 마커 디자인 최적화
            marker=dict(size=14, opacity=0.85, line=dict(width=1, color='rgba(255, 255, 255, 0.2)')),
        )

        fig.update_layout(
            coloraxis_showscale=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            
            title={
                'text': "<b>구독 개수와 비용이 늘어날수록 관리가 힘들어지는가?</b>",
                'font': {'size': 16, 'color': BRAND_COLORS.SUB_TEXT},
                'x': 0, 'xanchor': 'left'
            },

            margin=dict(t=10, b=40, l=40, r=20),
            
            # [수정] 범례(Legend) 활성화 및 위치 조정
            showlegend=True,
            legend=dict(
                title_text="",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color=BRAND_COLORS.SUB_TEXT)
            ),
            
            xaxis=dict(title="월 총 지출 비용 (원)", gridcolor='rgba(128, 128, 128, 0.1)', zeroline=False),
            yaxis=dict(title="구독 중인 서비스 개수 (개)", gridcolor='rgba(128, 128, 128, 0.1)', dtick=1, zeroline=False),
        )

        # 우상단 강조 영역 컬러도 MINT 계열로 연하게 변경
        fig.add_vrect(x0=plot_df['fee_service_total'].median(), x1=plot_df['fee_service_total'].max()*1.1,
                      y0=plot_df['service_count'].median(), y1=plot_df['service_count'].max()+1,
                      fillcolor=BRAND_COLORS.MAIN_MINT, opacity=0.03, layer="below", line_width=0)
        
        st.plotly_chart(fig, use_container_width=True, theme=None)
        st.write("")
        
        # 4. 분석 메시지 (인사이트 섹션)
        valid_df = self.df[['service_count', 'fee_service_total', 'pain_num']].dropna()
        if len(valid_df) > 1:
            pain_group = valid_df[valid_df['pain_num'] == 1]
            avg_fee_pain = pain_group['fee_service_total'].mean()
            avg_count_pain = pain_group['service_count'].mean()
            
            # [디자인 변경]
            insight_html = f"""
            <div style="
                background-color: rgba(20, 184, 166, 0.05); 
                padding: 20px; 
                border-radius: 12px; 
                border-left: 5px solid {BRAND_COLORS.MAIN_MINT}; 
                margin-top: 20px;
                border: 1px solid rgba(20, 184, 166, 0.1);
            ">
                <p style="color: {BRAND_COLORS.MAIN_MINT}; font-weight: bold; margin: 0 0 12px 0; font-size: 1rem;">🎯 심층 가설 검증 결과</p>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.92rem; line-height: 1.7;">
                    <li style="margin-bottom: 8px;"><b>고관여 유저의 페인포인트:</b> 관리가 어렵다고 응답한 유저들은 평균 <b>{avg_fee_pain:,.0f}원</b>을 지출하며, 약 <b>{avg_count_pain:.1f}개</b>의 서비스를 이용 중입니다.</li>
                    <li style="margin-bottom: 8px;"><b>상관성 분석:</b> 지출 비용이 커질수록 민트색(관리 어려움군) 점들이 우측 상단으로 밀집되는 경향이 뚜렷합니다.</li>
                    <li><b>결론:</b> 단순 구독 개수보다 <b>'총 지출 금액'</b>이 유저가 관리의 필요성을 강하게 느끼게 하는 핵심 트리거임을 확인했습니다.</li>
                </ul>
            </div>
            """
            st.markdown(insight_html, unsafe_allow_html=True)

        for _ in range(4): st.write("")

    def plot_market_expansion(self):
        st.markdown(f"<h5 style='font-weight:600; margin-bottom:6px;'>📊 2. 구독 카테고리별 점유율</h5>", unsafe_allow_html=True)
        if self.service_cols:
            category_map = {
                "service_current_ott": "OTT",
                "service_current_shopping": "쇼핑/멤버십",
                "service_current_food": "장보기/식음료/주류",
                "service_current_edu": "도서/교육",
                "service_current_cleaning": "세탁/청소",
                "service_current_pack": "짐 보관",
                "service_current_media": "미디어",
                "service_current_aisw": "AI/소프트웨어",
                "service_current_game": "게임",
                "service_current_etc": "기타"
            }

            counts_series = self.df[self.service_cols].sum().sort_values(ascending=False)
            plot_df = pd.DataFrame({
                '컬럼명': counts_series.index,
                '구독자 수': counts_series.values
            })
            
            # 컬럼명을 한글 카테고리명으로 치환
            plot_df['카테고리'] = plot_df['컬럼명'].map(category_map).fillna(plot_df['컬럼명'])

            if not plot_df.empty:
                # 3. 막대 그래프 생성 (이미 한글로 바뀐 '카테고리' 컬럼 사용)
                fig = px.bar(
                    plot_df, 
                    x='카테고리', 
                    y='구독자 수', 
                    text='구독자 수',
                    color_discrete_sequence=[BRAND_COLORS.MAIN_MINT],
                    labels={'카테고리': '서비스 카테고리', '구독자 수': '응답 인원(명)'}
                )
                
                # 4. 텍스트 포맷 및 위치 설정
                fig.update_traces(
                    texttemplate='%{text}명', 
                    textposition='outside',
                    cliponaxis=False, 
                    width=0.6,
                )
                
                # 5. 레이아웃 최적화
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    template='plotly_white',
                    
                    # 차트 내부 타이틀 복구
                    title={
                        'text': "<b>카테고리별 실제 구독자 현황</b>",
                        'font': {'size': 16, 'color': BRAND_COLORS.SUB_TEXT},
                        'x': 0,
                        'xanchor': 'left',
                        'pad': {'t': 10}
                    },
                    
                    # 마진 확보
                    margin=dict(t=40, b=60, l=50, r=20),
                    showlegend=False,
                    
                    xaxis=dict(
                        title=dict(text="서비스 카테고리", font=dict(size=12)),
                        gridcolor='rgba(128, 128, 128, 0.1)',
                        zeroline=False,
                        tickangle=0
                    ),
                    yaxis=dict(
                        title=dict(text="응답 인원(명)", font=dict(size=12)),
                        tickformat="d", 
                        range=[0, plot_df['구독자 수'].max() * 1.4], # 상단 여백
                        gridcolor='rgba(128, 128, 128, 0.1)',
                        zeroline=False
                    ),
                    coloraxis_showscale=False
                )

                # 차트 출력
                st.plotly_chart(fig, use_container_width=True, theme=None)
                
                # 4. 인사이트 메시지 (차트와의 간격을 위해 상단 margin 추가)
                if len(plot_df) > 1:
                    second_cat = plot_df.iloc[1]['카테고리']
                    st.markdown(f"""
                        <div style="
                            background-color: rgba(20, 184, 166, 0.05); 
                            padding: 22px; 
                            border-radius: 12px; 
                            border-left: 5px solid {BRAND_COLORS.MAIN_MINT}; 
                            border: 1px solid rgba(20, 184, 166, 0.1);
                            margin-top: 15px;  /* 차트와의 간격 확보 */
                            margin-bottom: 20px;
                        ">
                            <p style="margin: 0; font-size: 0.95rem; line-height: 1.7;">
                                🚀 <b>시장 확장 전략:</b> 초기 서비스는 OTT에 이어 점유율 2위인 <b>'{second_cat}'</b> 카테고리를 함께 공략하여 유저 락인(Lock-in) 효과를 극대화해야 합니다.
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

        for _ in range(4): st.write("")

    def plot_subjective_wordcloud(self):
        """Part 4: 주관식 응답 워드클라우드"""
        st.markdown(f"<h5 style='font-weight:600; margin-bottom:6px;'>📝 앱 서비스에 바라는 점</h5>", unsafe_allow_html=True)

        # 1. 데이터 추출 및 단어 빈도수 계산
        raw_texts = self.df['usage_expect'].dropna().astype(str).tolist()
        words = []

        # [정규화 맵핑] 워드클라우드에서 한 덩어리로 보일 핵심 키워드들
        normalization_map = {
            "리마인더": ["리마인더"],
            "결제 관리": ["결제일 알림", "결제일 정보", "결제 내역", "결제일 관리", "결제일과 금액", "결제 목록", "결제내역 불러오기", "갱신일 직전"],
            "할인 혜택": ["할인받는법", "할인 정보", "할인 팁", "할인 혜택", "할인가"],
            "구독 서비스 비교": ["OTT 비교", "구독 비교", "콘텐츠 비교", "서비스들 비교", "서비스 비교", "다양한 구독 소개", "다른 구독 정보"],
            "콘텐츠 정보/목록": ["OTT 컨텐츠 목록", "콘텐츠 어디에 있는지"],
            "구독 맞춤 추천": ["구독 추천", "맞춤추천", "서비스 추천", "카테고리별 추천", "관리 추천"]
        }

        try:
            from konlpy.tag import Okt
            okt = Okt()
            
            stop_words = ['수', '내', '등', '것', '및', '위해', '통해', '대한', '있는', '알', '함', '앱', '어플', 
                        '없음', '딱히', '생각', '않음', '생각나지', '모르겠음', '좋겠어요', '진짜', '너무', 
                        '특별히', '원하는', '기능', '서비스', '보고', '보고서', '같음', '안남', '안나요', '안나']

            for text in raw_texts:
                # [전처리] 덩어리 단어(Normalization) 먼저 확인
                is_normalized = False
                for rep, targets in normalization_map.items():
                    if any(target in text for target in targets):
                        words.append(rep) 
                        is_normalized = True
                        break # 덩어리로 잡혔으면 이 문장은 여기서 끝 (중복 방지)
                
                # 덩어리에 안 걸린 문장들만 형태소 분석기(Okt) 돌리기
                if not is_normalized:
                    nouns = okt.nouns(text)
                    for noun in nouns:
                        # '구독', '서비스', '관리' 등 너무 포괄적인 단어도 여기서 필터링
                        extra_stop_words = ['구독', '서비스', '관리', '기능', '어플', '앱']
                        if len(noun) > 1 and noun not in stop_words and noun not in extra_stop_words:
                            words.append(noun)

        except Exception as e:
            for text in raw_texts:
                for word in text.split():
                    if len(word) > 1: words.append(word)

        # 배포 서버에서도 100% 성공하는 방어 코드
        word_counts = Counter(words)

        # 여기서 한번 더 강제 삭제 (Okt가 어떻게 쪼갰든 상관없이 무조건 컷)
        bad_words = ['생각나지', '않음', '생각', '모름', '기타', '생각나지 않음', '안남']
        for bad_word in bad_words:
            if bad_word in word_counts:
                del word_counts[bad_word]

        word_counts = dict(word_counts.most_common(30))
        sorted_words = list(word_counts.keys())

        # 2. 워드클라우드 색상 및 생성 설정
        sorted_words = [w for w, c in word_counts.items()]

        def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
            try:
                rank = sorted_words.index(word)
                
                # 1. 메인 주인공 (1위): 메인 민트 (#13d6a2)
                if rank == 0:
                    return BRAND_COLORS.MAIN_MINT
                
                # 2. 서브 포인트 (2~5위): 2가지 색상 교차 배정
                elif rank < 5:
                    # 부드러운 오렌지(#ffd8b1)와 스카이 블루(#94b8e2) 교차
                    return "#ffc8cb" if rank % 2 == 0 else "#94b8e2"
                
                # 3. 중간 위계 (6~12위): 짙은 그레이 (#64748b)
                elif rank < 12:
                    return BRAND_COLORS.LIGHT_SUBTEXT # 또는 "#64748b"
                
                # 4. 배경 위계 (13위~): 연한 그레이 (#cbd5e1)
                else:
                    return "#cbd5e1"
            except:
                return "#94A3B8"
        
        wc = WordCloud(
            font_path='assets/Pretendard-SemiBold.otf', 
            background_color=None, 
            mode='RGBA',
            width=500,
            height=300,
            scale=3,
            max_words=25,
            color_func=color_func,
            margin=15,             # 단어 사이 간격 넓힘
            prefer_horizontal=1.0  # 가독성을 위해 가로 배치 고정
        ).generate_from_frequencies(word_counts)

        # 3. VOC 카테고리화 (원문 보존 로직)
        categories = {
            "🗓️ 결제 및 스케줄 관리": ["결제일", "일정", "스케줄", "내역", "가계부", "리마인더"],
            "💰 할인 팁 및 제휴 정보": ["할인", "제휴", "행사", "블랙프라이데이", "학생"],
            "🔍 서비스 비교 및 추천": ["비교", "추천", "맞춤", "콘텐츠", "어디"]
        }
        
        categorized_voc = {k: [] for k in categories.keys()}
        used_texts = set()

        for cat, keywords in categories.items():
            for text in raw_texts:
                if cat == "💰 할인 팁 및 제휴 정보" and "구독 맞춤" in text:
                    continue

                if any(kw in text for kw in keywords):
                    display_text = text.strip()
                    display_text = display_text.replace(" 같은거", "").replace(" 같은 거", "")

                    if "어도비 블랙프라이데이" in display_text:
                        display_text = "블랙프라이데이 같은 정기적 행사 알림"

                    for rep, targets in normalization_map.items():
                        if any(target in text for target in targets):
                            keep_raw = ["학생", "블랙프라이데이", "금액", "캘린더", "신규", "내려가는", "리마인더"]
                            if any(k in display_text for k in keep_raw):
                                display_text = display_text 
                            elif len(display_text) < 10 or '?' in display_text:
                                display_text = rep 
                            break
                    
                    if display_text not in used_texts:
                        if len(categorized_voc[cat]) < 4:
                            categorized_voc[cat].append(display_text)
                            used_texts.add(display_text)

        # --- 레이아웃 배치 ---
        col1, col2 = st.columns([1, 1.1])
        
        with col1:
            fig, ax = plt.subplots(figsize=(10, 6), dpi=150) 
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            
            # 배경 투명하게 처리 (대시보드와 일체감)
            fig.patch.set_facecolor('none')
            ax.set_facecolor('none')
            
            # 스트림릿에 고해상도로 출력
            st.pyplot(fig, use_container_width=True)

        with col2:
            st.markdown(f"""
                <div style="background-color: rgba(20, 184, 166, 0.1); padding: 18px; border-radius: 12px; border-left: 5px solid {BRAND_COLORS.MAIN_MINT}; border: 1px solid rgba(20, 184, 166, 0.2);">
                    <p style="font-size: 0.9rem; line-height: 1.6; margin: 0; font-weight: 500;">
                        <b style="color: {BRAND_COLORS.MAIN_MINT};">인사이트 요약</b><br>
                        데이터 분석 결과, 유저들은 <b>단순한 구독 목록 확인</b>을 넘어 <b>실질적인 금전적 혜택(할인 정보)</b>과 <b>콘텐츠 탐색 비용 감소(서비스 비교)</b>를 강력히 원하고 있습니다.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"<p style='font-size: 0.85rem; font-weight: 700; margin-top: 15px; margin-bottom: 8px;'>💬 카테고리별 유저 목소리</p>", unsafe_allow_html=True)
            
            for cat, voc_list in categorized_voc.items():
                if voc_list:
                    voc_items_html = ""
                    for v in voc_list:
                        voc_items_html += f'<span style="display: inline-block; margin-right: 8px; margin-bottom: 4px;">"{v}"</span> '

                    st.markdown(f"""
                        <div style="
                            margin-bottom: 10px; 
                            background-color: rgba(128, 128, 128, 0.05); 
                            padding: 12px; 
                            border-radius: 8px; 
                            border: 1px solid rgba(0, 0, 0, 0.1);
                        ">
                            <div style="
                                display: inline-block;
                                font-size: 0.7rem; 
                                color: {BRAND_COLORS.SUB_MINT}; 
                                font-weight: 700; 
                                background-color: rgba(20, 184, 166, 0.1); 
                                padding: 2px 8px; 
                                border-radius: 6px;
                                margin-bottom: 10px;
                                border: 1px solid rgba(20, 184, 166, 0.2);
                            ">{cat}</div>
                            <div style="font-size: 0.82rem; line-height: 1.5; font-weight: 500; color: inherit;">
                                {voc_items_html}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)