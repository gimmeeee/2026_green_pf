import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
from config import BRAND_COLORS

def show_appendix_page(df):
    # region 0. 에러 방지용 세션 초기화 (app.py의 chat_open 누락 대응)
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    # endregion

    # region 1. UI 스타일 설정 (CSS)
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

            /* 5. 전체 화면 압축 및 상단 잘림 해결 (교정본) */
            .block-container {{
                padding-top: 3rem !important; /* 상단 여백을 늘려 잘림 방지 */
                padding-bottom: 0rem !important;
            }}
            h2 {{ font-size: 22px !important; margin-bottom: 12px !important; }}
            .chart-sub-title {{ 
                font-size: 14px; font-weight: 700; color: #475569; 
                margin-bottom: 8px; margin-top: 10px;
            }}
            [data-testid="stMetricValue"] {{ font-size: 18px !important; }}
            [data-testid="stMetricLabel"] {{ font-size: 11px !important; }}

            /* 6. 랭킹카드 스타일 */
            <style>
            .ranking-card {{ background-color: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; }}
            .ranking-text {{ font-size: 13px; font-weight: 600; color: #1e293b; }}

            /* 7. 자유로운 레이아웃을 위한 디자인 추가 */
            .info-card {{
                background: white;
                padding: 18px;
                border-radius: 16px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.05); /* 그리드 느낌을 빼주는 그림자 */
                border: 1px solid #f1f5f9;
                margin-bottom: 15px;
            }}
            .voc-bubble {{
                background: #fff5f5;
                border-left: 4px solid {BRAND_COLORS.POINT_CORAL};
                padding: 12px;
                border-radius: 0 12px 12px 0;
                margin-bottom: 10px;
                font-size: 12px;
            }}
            .ranking-tag {{
                display: inline-block;
                padding: 2px 8px;
                background: {BRAND_COLORS.MAIN_MINT};
                color: white;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 800;
                margin-bottom: 5px;
            }}
        </style>
    """, unsafe_allow_html=True)
    # endregion

    # region 2. 세션 상태 및 필터 로직 초기화, 데이터 전처리
    if df is None or df.empty:
        st.warning("분석할 데이터가 로드되지 않았습니다.")
        return

    working_df = df.copy()
    
    # [수정] TypeError 방지를 위한 수치형 컬럼 리스트 및 강제 변환
    ott_fee_cols = [c for c in working_df.columns if 'ott_fee_' in c]
    # 시청 시간 컬럼 리스트 추가 (TypeError의 주요 원인)
    ott_time_cols = [c for c in working_df.columns if 'ott_time_' in c]
    
    numeric_cols = [
        'fee_service_total', 'ott_time_total', 
        'ott_imp_volume', 'ott_imp_original', 'ott_imp_quality', 
        'ott_imp_algo', 'ott_imp_price', 'ott_imp_ux'
    ] + ott_fee_cols + ott_time_cols

    for col in numeric_cols:
        if col in working_df.columns:
            # 문자열 콤마 제거 및 수치 변환 처리
            working_df[col] = pd.to_numeric(
                working_df[col].astype(str).str.replace(',', ''), 
                errors='coerce'
            ).fillna(0)

    # [추가] 불리언/체크박스 데이터 수치화 (경험률/해지사유 차트용)
    bool_like_cols = [c for c in working_df.columns if 'service_ever_' in c or 'ott_cancel_reason_' in c or 'ott_current_' in c]
    for col in bool_like_cols:
        if col != 'ott_cancel_reason_primary':
            working_df[col] = working_df[col].replace({'TRUE': 1, 'FALSE': 0, True: 1, False: 0}).fillna(0)
            working_df[col] = pd.to_numeric(working_df[col], errors='coerce').fillna(0)
    # endregion

    # region 3. 사이드바 필터 시스템
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
    # endregion

    # region 4. 본문 대시보드

    # region 4-1. 시각화 컴포넌트 (함수 정의 섹션)
    def render_kpi_metrics(f_df):
        """최상단 요약 지표"""
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("분석 인원", f"{len(f_df)}명")
        k2.metric("평균 구독료", f"{int(f_df['fee_service_total'].mean()):,}원")
        k3.metric("OTT 이탈 경험", f"{(f_df['ott_cancel'] == '예').mean()*100:.1f}%")
        k4.metric("평균 시청시간", f"{int(f_df['ott_time_total'].mean())}분")

    def render_category_bar(f_df, height=380):
        """카테고리별 경험 vs 현재이용 막대 차트"""
        cat_map = {
            "ott": "OTT", "shopping": "쇼핑/멤버십", "food": "장보기/식음료",
            "edu": "도서/교육", "cleaning": "세탁/청소", "pack": "짐 보관",
            "media": "미디어", "aisw": "AI/SW", "game": "게임", "etc": "기타"
        }
        cat_plot = []
        for key, label in cat_map.items():
            ever_col = f"service_ever_{key}"
            curr_col = f"service_current_{key}"
            
            # [해결 로직] 
            # 1. pd.to_numeric(..., errors='coerce') -> 문자열 "TRUE"를 숫자 1로 바꾸거나, 실패 시 NaN으로 만듦
            # 2. fillna(0) -> NaN을 0으로 채움
            # 3. sum() -> 이제 안전하게 숫자로 합산됨
            
            ever_val = 0
            if ever_col in f_df.columns:
                # 혹시라도 불리언/문자열이 섞여있을 경우를 대비해 확실하게 숫자로 변환 후 합산
                ever_series = pd.to_numeric(f_df[ever_col].replace({'TRUE': 1, 'FALSE': 0, 'True': 1, 'False': 0}), errors='coerce')
                ever_val = ever_series.fillna(0).sum()
                
            curr_val = 0
            if curr_col in f_df.columns:
                curr_series = pd.to_numeric(f_df[curr_col].replace({'TRUE': 1, 'FALSE': 0, 'True': 1, 'False': 0}), errors='coerce')
                curr_val = curr_series.fillna(0).sum()
            
            # 합산 결과가 float일 수 있으므로 안전하게 int로 변환하여 추가
            cat_plot.append({'Category': label, '구분': '경험함', '인원': int(ever_val)})
            cat_plot.append({'Category': label, '구분': '현재이용', '인원': int(curr_val)})
        
        plot_df = pd.DataFrame(cat_plot)
        
        # 시각화 부분
        fig = px.bar(
            plot_df, 
            x='Category', 
            y='인원', 
            color='구분', 
            barmode='group',
            text='인원',
            color_discrete_map={'경험함': '#e2e8f0', '현재이용': BRAND_COLORS.MAIN_MINT}
        )
        
        fig.update_traces(textposition='outside', textfont_size=11, textfont_weight='bold')
        fig.update_layout(
            height=height, 
            margin=dict(t=30, b=0, l=0, r=0), 
            xaxis_title=None, 
            yaxis_title=None,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def render_value_radar(f_df, working_df, height=380):
        """사용자 가치관 레이더 차트"""
        radar_map = {
            'ott_imp_volume': '콘텐츠 양', 'ott_imp_original': '오리지널/독점작', 'ott_imp_quality': '화질/접속수',
            'ott_imp_algo': '추천 정확도', 'ott_imp_price': '구독료', 'ott_imp_ux': '앱 편의성'
        }
        r_keys = list(radar_map.keys())
        r_labels = list(radar_map.values())

        def get_clean_mean(target_df, keys):
            temp_df = target_df[keys].copy()
            for k in keys:
                temp_df[k] = pd.to_numeric(temp_df[k], errors='coerce').fillna(0)
            return temp_df.mean().tolist()

        try:
            avg_total = get_clean_mean(working_df, r_keys) # 전체 평균
            avg_selected = get_clean_mean(f_df, r_keys)    # 선택 그룹 평균

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=avg_total, theta=r_labels, fill='toself', name='전체 평균', line_color='#cbd5e1'))
            fig.add_trace(go.Scatterpolar(r=avg_selected, theta=r_labels, fill='toself', name='선택 그룹', line_color=BRAND_COLORS.MAIN_MINT))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=False, range=[0, 7])), 
                height=height,
                margin=dict(t=60, b=40, l=40, r=40), 
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=0, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"레이더 차트 생성 중 오류가 발생했습니다: {e}")

    def render_brand_ranking(f_df, mode='pop'):
        """브랜드 랭킹 카드 (mode: 'pop'은 인원수, 'time'은 시청시간)"""
        brand_cols = [c for c in f_df.columns if 'ott_current_' in c and c not in ['ott_current', 'ott_current_none', 'ott_current_etc']]
        
        if mode == 'pop':
            title, color = "👥 이용자 수 순위", BRAND_COLORS.MAIN_MINT
            data = f_df[brand_cols].sum().sort_values(ascending=False).head(5)
            suffix = "명"
        else:
            title, color = "⏳ 주평균 시청시간", "#64748b"
            time_cols = [f'ott_time_{c.split("_")[-1]}' for c in brand_cols if f'ott_time_{c.split("_")[-1]}' in f_df.columns]
            data = f_df[time_cols].mean().sort_values(ascending=False).head(5)
            suffix = "분"

        st.markdown(f"<p style='font-size:12px; font-weight:700; color:#64748b;'>{title}</p>", unsafe_allow_html=True)
        for i, (col, val) in enumerate(data.items()):
            b_name = col.split('_')[-1].upper()
            st.markdown(f"""
                <div style='margin-bottom: 10px; padding: 8px; border-radius: 8px; background: #f8fafc; border-left: 4px solid {color};'>
                    <span style='font-size:11px; font-weight:800;'>{i+1}위</span> <b>{b_name}</b> <span style='float:right; font-size:12px;'>{int(val)}{suffix}</span>
                </div>
            """, unsafe_allow_html=True)

    def render_cancel_reasons(f_df, height=300):
        """해지 사유 가로 바 차트"""
        reason_cols = [c for c in f_df.columns if 'ott_cancel_reason_' in c and c != 'ott_cancel_reason_primary']
        reasons = f_df[reason_cols].sum().sort_values().tail(5)
        fig = px.bar(x=reasons.values, y=[c.replace('ott_cancel_reason_', '').capitalize() for c in reasons.index],
                    orientation='h', color_discrete_sequence=[BRAND_COLORS.POINT_CORAL])
        fig.update_layout(height=height, margin=dict(t=0, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None,
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    def render_voc_bubbles(f_df):
        """VOC 말풍선"""
        voc_list = f_df['pain_point_open'].replace(['nan', '없음', '아니오', 'X'], pd.NA).dropna().unique()
        v_cols = st.columns(2)
        for i, v in enumerate(voc_list[:4]):
            v_cols[i % 2].markdown(f"<div class='voc-bubble'>“{v}”</div>", unsafe_allow_html=True)
    # endregion

    # region 4-2. 메인 페이지 함수 (레이더/배치)
    if f_df.empty:
        st.error("조건에 맞는 데이터가 없습니다.")
    else:
        st.markdown("## 📊 데이터 부록: 구독 행태 심층 분석")
        # [배치 1] 핵심 지표 (가로 전체 활용)
        render_kpi_metrics(f_df)

        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        # [배치 2] 거시 분석 (카테고리 vs 가치관)
        st.markdown("<div class='chart-sub-title'>1️⃣ 구독 카테고리 이용 현황 및 중요 가치</div>", unsafe_allow_html=True)
        row2_c1, row2_c2 = st.columns([2.2, 1])
        with row2_c1:
            render_category_bar(f_df, height=420)
        with row2_c2:
            render_value_radar(f_df, df, height=420)

        st.markdown("---")

        # [배치 3] 미시 분석 (이용자 순위 vs 시간 순위 vs 해지 사유)
        st.markdown("<div class='chart-sub-title'>2️⃣ OTT 서비스 상세 이용 행태 분석</div>", unsafe_allow_html=True)
        row3_c1, row3_c2, row3_c3 = st.columns([1, 1, 1.2])
        with row3_c1:
            render_brand_ranking(f_df, mode='pop')
        with row3_c2:
            render_brand_ranking(f_df, mode='time')
        with row3_c3:
            render_cancel_reasons(f_df, height=300)

        # [배치 4] 사용자 목소리 (VOC)
        st.markdown("<div class='chart-sub-title'>3️⃣ 사용자 페인포인트 (생생한 목소리)</div>", unsafe_allow_html=True)
        render_voc_bubbles(f_df)

    # endregion