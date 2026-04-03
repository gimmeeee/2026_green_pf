import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def show_appendix_page(df):
    st.markdown("## 📊 데이터 부록: 구독 행태 심층 탐색기")
    st.write("로데이터(Raw Data)를 기반으로 특정 그룹의 구독 가치관과 소비 패턴을 실시간으로 분석합니다.")

    if df is None or df.empty:
        st.warning("분석할 데이터가 로드되지 않았습니다.")
        return

    # 1. 실제 컬럼명에 맞춘 매핑 (보내주신 리스트 기준)
    column_mapping = {
        'ott_imp_volume': 'pref_quantity',
        'ott_imp_original': 'pref_exclusive',
        'ott_imp_quality': 'pref_quality',
        'ott_imp_algo': 'pref_recommend',
        'ott_imp_price': 'pref_price',
        'ott_imp_ux': 'pref_convenience'
    }
    
    # 안전하게 컬럼명 변경 (기존 데이터 보존을 위해 copy 사용)
    working_df = df.copy()
    working_df = working_df.rename(columns=column_mapping)

    # 2. 필수 컬럼 숫자형 변환 (에러 방지)
    # fee_service_total, ott_time_total 등은 이미 리스트에 있으므로 그대로 사용
    numeric_targets = [
        'fee_service_total', 'ott_time_total', 
        'pref_quantity', 'pref_exclusive', 'pref_quality', 
        'pref_recommend', 'pref_price', 'pref_convenience'
    ]
    
    for col in numeric_targets:
        if col in working_df.columns:
            working_df[col] = pd.to_numeric(working_df[col], errors='coerce').fillna(0)

    # --- 사이드바 필터 ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔎 그룹 필터링")
    
    all_jobs = sorted(working_df['job'].unique().tolist()) if 'job' in working_df.columns else []
    selected_jobs = st.sidebar.multiselect("직업군 선택", options=all_jobs, default=all_jobs)
    
    all_ages = sorted(working_df['age_group'].unique().tolist()) if 'age_group' in working_df.columns else []
    selected_ages = st.sidebar.multiselect("연령대 선택", options=all_ages, default=all_ages)

    # 필터링 적용
    mask = working_df['job'].isin(selected_jobs) & working_df['age_group'].isin(selected_ages)
    f_df = working_df[mask]

    # --- 상단 핵심 지표 ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("분석 대상", f"{len(f_df)}명")
    with m2:
        avg_fee = f_df['fee_service_total'].mean() if not f_df.empty else 0
        st.metric("평균 구독료", f"{int(avg_fee):,}원")
    with m3:
        avg_time = f_df['ott_time_total'].mean() if not f_df.empty else 0
        st.metric("주간 시청시간", f"{int(avg_time)}분")
    with m4:
        churn_rate = (f_df['ott_cancel'] == '예').mean() * 100 if not f_df.empty else 0
        st.metric("해지 경험률", f"{churn_rate:.1f}%")

    st.markdown("---")

    # --- 시각화 섹션 1 ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🎯 구독 성향 (Radar Chart)")
        radar_labels = {
            'pref_quantity': '양', 'pref_exclusive': '독점 콘텐츠', 'pref_quality': '화질/음질',
            'pref_recommend': '추천 알고리즘', 'pref_price': '가격', 'pref_convenience': '사용 편의성'
        }
        categories = list(radar_labels.values())
        radar_keys = list(radar_labels.keys())
        
        fig_radar = go.Figure()
        # 전체 평균
        fig_radar.add_trace(go.Scatterpolar(
            r=working_df[radar_keys].mean().tolist(), theta=categories, fill='toself', 
            name='전체 평균', line_color='rgba(180, 180, 180, 0.5)'
        ))
        # 필터 그룹
        if not f_df.empty:
            fig_radar.add_trace(go.Scatterpolar(
                r=f_df[radar_keys].mean().tolist(), theta=categories, fill='toself', 
                name='선택 그룹', line_color='#00D1B2'
            ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 7])), height=400)
        st.plotly_chart(fig_radar, use_container_width=True)

    with col2:
        st.subheader("💸 비용 대비 시청 효율")
        if not f_df.empty:
            fig_scatter = px.scatter(
                f_df, x='ott_time_total', y='fee_service_total',
                color='user_seg' if 'user_seg' in f_df.columns else None,
                hover_data=['job', 'age_group'],
                labels={'ott_time_total': '주간 시청시간(분)', 'fee_service_total': '월 구독료(원)'},
                color_discrete_sequence=px.colors.qualitative.Pastel
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
            fig_bar = px.bar(x=reasons.values, y=labels, orientation='h', color_discrete_sequence=['#FF6B6B'])
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