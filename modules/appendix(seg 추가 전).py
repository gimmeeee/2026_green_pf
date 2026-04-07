import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
from config import BRAND_COLORS

def show_appendix_page(df):
    # ---------------------------------------------------------
    # 0. 에러 방지용 세션 초기화 (app.py의 chat_open 누락 대응)
    # ---------------------------------------------------------    
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ---------------------------------------------------------
    # 1. UI 스타일 설정 (CSS)
    # ---------------------------------------------------------
    st.markdown(f"""
        <style>
            /* 1. 체크박스 위젯 전체: 오른쪽 정렬 강제 */
            div[data-testid="stSidebar"] .stCheckbox {{
                display: flex !important;
                justify-content: flex-end !important;
                width: 100% !important;
                margin-top: -30px !important; /* 제목 라인으로 올리기 */
            }}
            
            /* 2. 체크박스 내부 라벨: 여백 제거 및 밀착 */
            div[data-testid="stSidebar"] .stCheckbox > label {{
                gap: 2px !important;
                padding: 0 !important;
                min-width: unset !important;
                justify-content: flex-end !important;
            }}

            /* 3. '전체' 텍스트: 타이틀보다 확실히 작게 (9px) */
            div[data-testid="stSidebar"] .stCheckbox label p {{
                font-size: 9px !important; 
                white-space: nowrap !important;
                color: {BRAND_COLORS.SUB_TEXT} !important;
                letter-spacing: -0.5px !important;
                line-height: 1 !important;
            }}

            /* 4. 체크박스 네모 박스: 크기 대폭 축소 (0.65배) */
            div[data-testid="stSidebar"] .stCheckbox [data-testid="stWidgetLabel"] div:first-child {{
                transform: scale(0.65) !important; 
                transform-origin: right center !important;
                margin: 0 !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 2. 세션 상태 및 필터 로직 초기화, 데이터 전처리
    # ---------------------------------------------------------
    if df is None or df.empty:
        st.warning("분석할 데이터가 로드되지 않았습니다.")
        return

    working_df = df.copy()
    
    # 숫자형 컬럼 자동 변환
    ott_fee_cols = [c for c in working_df.columns if 'ott_fee_' in c]
    numeric_cols = [
        'fee_service_total', 'ott_time_total', 
        'ott_imp_volume', 'ott_imp_original', 'ott_imp_quality', 
        'ott_imp_algo', 'ott_imp_price', 'ott_imp_ux'
    ] + ott_fee_cols

    for col in numeric_cols:
        if col in working_df.columns:
            working_df[col] = pd.to_numeric(working_df[col], errors='coerce').fillna(0)

    # ---------------------------------------------------------
    # 3. 사이드바 필터 시스템
    # ---------------------------------------------------------
    if 'filters' not in st.session_state:
        st.session_state.filters = {
            'gender': sorted(working_df['gender'].unique().tolist()),
            'job': sorted(working_df['job'].unique().tolist()),
            'age_group': sorted(working_df['age_group'].unique().tolist())
        }

    def render_sidebar_filter(label, key, options):
        # 1. 필터 상태 및 체크박스 버전 초기화
            all_key = f"all_{key}_state"
            version_key = f"{key}_version"
            
            if all_key not in st.session_state:
                st.session_state[all_key] = True
            if version_key not in st.session_state:
                st.session_state[version_key] = 0

            # 현재 실제 데이터와 세션의 일치 여부 확인
            is_now_all = set(options).issubset(set(st.session_state.filters[key]))

            cols_head = st.sidebar.columns([4, 1.8])    
            with cols_head[0]:
                st.markdown(f"<div style='font-size:14px; font-weight:700; padding-top:5px;'>{label}</div>", unsafe_allow_html=True)

            with cols_head[1]:
                # 핵심: key 뒤에 version을 붙여 위젯을 강제로 새로고침함
                check_val = st.checkbox(
                    "전체", 
                    value=st.session_state[all_key], 
                    key=f"all_{key}_widget_v{st.session_state[version_key]}"
                )
                
                # 체크박스 조작 시 처리
                if check_val != st.session_state[all_key]:
                    st.session_state[all_key] = check_val
                    st.session_state.filters[key] = options if check_val else []
                    st.rerun()

            # 2. 버튼 클릭 핸들러
            def handle_btn_click(opt):
                if opt in st.session_state.filters[key]:
                    st.session_state.filters[key].remove(opt)
                else:
                    st.session_state.filters[key].append(opt)
                
                # 버튼을 누르면 '전체' 상태를 계산하고, 체크박스 버전을 올려서 강제 갱신
                new_all_state = set(options).issubset(set(st.session_state.filters[key]))
                st.session_state[all_key] = new_all_state
                st.session_state[version_key] += 1 # 이 값이 바뀌면 위젯이 새로 그려짐
                st.rerun()

            # 3. 버튼 레이아웃 및 클릭 로직
            btn_cols = st.sidebar.columns(2)
            long_opts = ["파트타임/프리랜서", "파트타임", "프리랜서"]
            short_opts = [opt for opt in options if opt not in long_opts]

            # 버튼 클릭 시 해당 항목만 넣거나 빼기 (반 버튼)
            for i, opt in enumerate(short_opts):
                active = opt in st.session_state.filters[key]
                # 여기서 handle_btn_click(opt)를 호출합니다.
                if btn_cols[i % 2].button(opt, key=f"btn_{key}_{opt}_v{st.session_state[version_key]}", 
                                        use_container_width=True, 
                                        type="primary" if active else "secondary"):
                    handle_btn_click(opt)
            # (파트타임/프리랜서용 긴 버튼) 동일하게 적용
            for opt in long_opts:
                if opt in options:
                    active = opt in st.session_state.filters[key]
                    # 여기서도 handle_btn_click(opt)를 호출합니다.
                    if st.sidebar.button(opt, key=f"btn_{key}_{opt}_long_v{st.session_state[version_key]}", 
                                        use_container_width=True,
                                        type="primary" if active else "secondary"):
                        handle_btn_click(opt)

    # 사이드바 필터 실행
    st.sidebar.markdown("---")
    render_sidebar_filter("성별", 'gender', sorted(working_df['gender'].unique().tolist()))
    st.sidebar.markdown("---")
    job_order = ["학생", "직장인", "자영업자", "전업주부", "파트타임/프리랜서"]
    actual_jobs = [j for j in job_order if j in working_df['job'].unique()]
    render_sidebar_filter("직업군", 'job', actual_jobs)
    st.sidebar.markdown("---")
    render_sidebar_filter("연령대", 'age_group', sorted(working_df['age_group'].unique().tolist()))

    # 필터링 적용
    selected_mask = (
        working_df['gender'].isin(st.session_state.filters['gender']) & 
        working_df['job'].isin(st.session_state.filters['job']) & 
        working_df['age_group'].isin(st.session_state.filters['age_group'])
    )
    f_df = working_df[selected_mask]

    if f_df.empty:
        st.error("조건에 맞는 데이터가 없습니다.")
        return

    # ---------------------------------------------------------
    # 4. 본문 대시보드 출력
    # ---------------------------------------------------------
    st.markdown("## 📊 데이터 부록: 구독 행태 심층 탐색기")
    
    if f_df.empty:
        st.error("⚠️ 선택하신 조건에 해당하는 응답자가 없습니다. 필터를 조정해 주세요.")
        return

    # [상단 요약 지표]
    m1, m2, m3, m4 = st.columns([1, 1.2, 2.5, 1.2])
    with m1: st.metric("응답 인원", f"{len(f_df)}명")
    with m2: st.metric("평균 월구독료", f"{int(f_df['fee_service_total'].mean()):,}원")
    with m3:
        avg_ott_count = f_df['ott_current'].apply(lambda x: len(str(x).split(',')) if pd.notna(x) and x != '없음' else 0).mean()
        avg_ott_fee = f_df[ott_fee_cols].sum(axis=1).mean()
        st.write("**OTT 이용 요약 (평균)**")
        st.caption(f"개수: {avg_ott_count:.1f}개 / 구독료: {int(avg_ott_fee):,}원")
    with m4:
        if 'pain_management' in f_df.columns:
            rate = (f_df['pain_management'] == '예').mean() * 100
            st.metric("관리 어려움", f"{rate:.1f}%")

    st.markdown("---")

    # --- 시각화 섹션 1 : 성향 및 효율 ---
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