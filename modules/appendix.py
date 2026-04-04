import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from config import BRAND_COLORS

def show_appendix_page(df):
    st.markdown("## 📊 데이터 부록: 구독 행태 심층 탐색기")
    st.write("로데이터(Raw Data)를 기반으로 특정 그룹의 구독 가치관과 소비 패턴을 실시간으로 분석합니다.")

    if df is None or df.empty:
        st.warning("분석할 데이터가 로드되지 않았습니다.")
        return

    # 컬럼명 전처리
    working_df = df.copy()
    
    # 1. 숫자형 변환 (에러 방지용)
    ott_fee_cols = [c for c in working_df.columns if 'ott_fee_' in c]
    numeric_cols = [
        'fee_service_total', 'ott_time_total', 
        'ott_imp_volume', 'ott_imp_original', 'ott_imp_quality', 
        'ott_imp_algo', 'ott_imp_price', 'ott_imp_ux'
    ] + ott_fee_cols

    for col in numeric_cols:
        if col in working_df.columns:
            working_df[col] = pd.to_numeric(working_df[col], errors='coerce').fillna(0)

    # --- 사이드바 필터 ---
    st.sidebar.subheader("🔎 그룹 필터링")

    all_genders = sorted(working_df['gender'].unique().tolist()) if 'gender' in working_df.columns else []
    selected_genders = st.sidebar.multiselect("성별 선택", options=all_genders, default=all_genders)
    
    all_jobs = sorted(working_df['job'].unique().tolist())
    selected_jobs = st.sidebar.multiselect("직업군 선택", options=all_jobs, default=all_jobs)
    
    all_ages = sorted(working_df['age_group'].unique().tolist())
    selected_ages = st.sidebar.multiselect("연령대 선택", options=all_ages, default=all_ages)

    # 필터링 적용
    mask = (
        working_df['gender'].isin(selected_genders) & 
        working_df['job'].isin(selected_jobs) & 
        working_df['age_group'].isin(selected_ages)
    )
    f_df = working_df[mask]

    # --- 수정사항 2: 응답자 없을 때 메시지 처리 ---
    if f_df.empty:
        st.error("⚠️ 선택하신 조건에 해당하는 응답자가 없습니다. 필터를 조정해 주세요.")
        return

    # --- 수정사항 1: 상단 요약 지표 변경 ---
    m1, m2, m3, m4 = st.columns([1, 1.2, 2.5, 1.2])
    
    with m1:
        st.metric("응답 인원수", f"{len(f_df)}명")
        
    with m2:
        # AQ2: 전체 구독료 평균
        avg_total_fee = f_df['fee_service_total'].mean()
        st.metric("평균 월구독료(전체)", f"{int(avg_total_fee):,}원")
        
    with m3:
        def count_ott(x):
            if pd.isna(x) or x == '없음': return 0
            return len(str(x).split(','))
        avg_ott_count = f_df['ott_current'].apply(count_ott).mean()
        avg_ott_fee = f_df[ott_fee_cols].sum(axis=1).mean()
        avg_time = f_df['ott_time_total'].mean()
        
        st.write("**OTT 이용 요약 (평균)**")
        st.caption(f"개수: {avg_ott_count:.1f}개 / 구독료: {int(avg_ott_fee):,}원 / 시청: {int(avg_time)}분")
        
    with m4:
        if 'pain_management' in f_df.columns:
            difficulty_rate = (f_df['pain_management'] == '예').mean() * 100
            st.metric("관리 어려움", f"{difficulty_rate:.1f}%")

    st.markdown("---")

    # --- 시각화 섹션 1 ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🎯 구독 성향 (Radar Chart)")
        radar_map = {
            'ott_imp_volume': '콘텐츠 양',
            'ott_imp_original': '오리지널/독점작',
            'ott_imp_quality': '화질/동시접속 수',
            'ott_imp_algo': '추천 알고리즘 정확도',
            'ott_imp_price': '구독료',
            'ott_imp_ux': '앱 사용 편의성'
        }

        radar_keys = list(radar_map.keys())
        radar_labels = list(radar_map.values())

        fig_radar = go.Figure()

        # 전체 평균
        fig_radar.add_trace(go.Scatterpolar(
            r=working_df[radar_keys].mean().tolist(), 
            theta=radar_labels, 
            fill='toself', 
            name='전체 평균',
            line_color=BRAND_COLORS.SUB_TEXT,
            fillcolor='rgba(124, 128, 133, 0.2)'
        ))

        # 필터 그룹
        fig_radar.add_trace(go.Scatterpolar(
            r=f_df[radar_keys].mean().tolist(), 
            theta=radar_labels, 
            fill='toself', 
            name='선택 그룹',
            line_color=BRAND_COLORS.MAIN_MINT,
            fillcolor='rgba(19, 214, 162, 0.3)'
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 7]),
                bgcolor=BRAND_COLORS.TRANSPARENT
            ),
            paper_bgcolor=BRAND_COLORS.TRANSPARENT,
            plot_bgcolor=BRAND_COLORS.TRANSPARENT,
            font=dict(color=None),
            height=400,
            margin=dict(t=30, b=30, l=50, r=50)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        st.subheader("💸 비용 대비 시청 효율")
        fig_scatter = px.scatter(
            f_df, x='ott_time_total', y='fee_service_total',
            color='user_seg' if 'user_seg' in f_df.columns else None,
            size='fee_service_total',
            hover_data=['job', 'age_group'],
            labels={'ott_time_total': '주간 시청시간(분)', 'fee_service_total': '월 구독료(원)'},
            color_discrete_sequence=BRAND_COLORS.CHART_CATEGORICAL
        )
        fig_scatter.update_layout(
            paper_bgcolor=BRAND_COLORS.TRANSPARENT,
            plot_bgcolor=BRAND_COLORS.TRANSPARENT,
            height=400
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")

    # --- 시각화 섹션 2 ---
    col3, col4 = st.columns([1, 1])

    with col3:
        st.subheader("❌ 주요 해지 사유")
        reason_cols = [c for c in f_df.columns if 'ott_cancel_reason_' in c and c != 'ott_cancel_reason_primary']
        if not f_df.empty and reason_cols:
            reasons = f_df[reason_cols].apply(lambda x: x.map({True: 1, False: 0, 'TRUE': 1, 'FALSE': 0})).sum().sort_values(ascending=True)
            labels = [c.replace('ott_cancel_reason_', '') for c in reasons.index]
            # 주의/해지 맥락이므로 POINT_CORAL 적용
            fig_bar = px.bar(
                x=reasons.values, y=labels, orientation='h', 
                color_discrete_sequence=[BRAND_COLORS.POINT_CORAL]
            )
            fig_bar.update_layout(
                paper_bgcolor=BRAND_COLORS.TRANSPARENT,
                plot_bgcolor=BRAND_COLORS.TRANSPARENT,
                xaxis_title="응답 수", yaxis_title=None
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with col4:
        st.subheader("💬 사용자 리얼 보이스")
        voice_col = 'pain_point_open' # 보내주신 리스트의 마지막 컬럼
        if voice_col in f_df.columns:
            voices = f_df[voice_col].dropna().unique()
            if len(voices) > 0:
                for v in voices[:5]:
                    st.info(f"\"{v}\"")
            else:
                st.write("의견이 없습니다.")