import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time
import re
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

            /* KPI 카드 배경 및 테두리 슬림화 */
            [data-testid="stMetric"] {{
                background-color: #f8fafc;
                border: 1px solid #f1f5f9;
                padding: 8px 12px !important;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            }}
            /* 메트릭 값 폰트 및 간격 조절 */
            [data-testid="stMetricValue"] {{
                font-size: 20px !important; 
                line-height: 1.2 !important;
            }}
            [data-testid="stMetricLabel"] {{ 
                font-size: 11px !important; 
                margin-bottom: -5px !important;
            }}

            /* 6. 랭킹카드 스타일 */
            .ranking-container {{
                background: transparent; /* 배경색 제거 (이중 박스 느낌 방지) */
                border-radius: 0px;
                padding: 0px;           /* 패딩 제거 */
                border: none;           /* 테두리 제거 */
            }}
            .rank-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 14px 4px !important;  /* 아이템 간격 살짝 조정 */
                border-bottom: 1px solid #f1f5f9;
            }}
            .rank-item:last-child {{ border-bottom: none; }}
            /* 랭킹 카드(sub_col1, sub_col2) 사이의 간격을 넓히는 설정 */
            div[data-testid="column"]:has(.rank-item) {{
                padding-left: 5px !important;
                padding-right: 5px !important;
            }}
            .rank-number {{
                font-size: 11px;
                font-weight: 800;
                color: {BRAND_COLORS.MAIN_MINT};
                margin-right: 8px;
            }}
            .rank-name {{
                font-size: 13px;
                font-weight: 600;
                color: #334155;
            }}
            .rank-value {{
                font-size: 12px;
                color: #64748b;
                font-weight: 500;
            }}

            /* 7. 공간 압축을 위한 최적화 레이아웃 */
            /* 차트와 텍스트를 감싸는 기본 카드 (그림자 제거, 여백 축소) */
            .info-card {{
                background: #ffffff;
                padding: 10px; /* 18px에서 축소 */
                border-radius: 12px;
                border: 1px solid #f1f5f9;
                margin-bottom: 8px; /* 간격 축소 */
            }}

            /* VOC 말풍선 (세로 길이 대폭 압축) */
            .voc-bubble {{
                background: #fff5f5;
                border-left: 3px solid {BRAND_COLORS.POINT_CORAL};
                padding: 6px 12px; /* 상하 여백 축소 */
                border-radius: 4px 10px 10px 4px;
                margin-bottom: 5px; /* 다음 말풍선과의 간격 축소 */
                font-size: 11px; /* 폰트 살짝 축소 */
                line-height: 1.4;
            }}

            /* 랭킹 강조 태그 (순위 표시용) */
            .ranking-tag {{
                display: inline-block;
                padding: 1px 6px;
                background: {BRAND_COLORS.MAIN_MINT};
                color: white;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 800;
                margin-right: 5px;
            }}

            /* 1. 그리드 카드 공통 스타일 (박스 규격 고정) */
            .grid-card {{
                background: white;
                padding: 12px 15px;
                border-radius: 12px;
                border: 1px solid #eff1f3;
                box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                margin-bottom: 10px;
                overflow: hidden; /* 내부 요소가 넘치지 않게 */
            }}

            /* 통합 KPI 바: 글자가 깨지지 않게 최소 너비와 flex 설정 강화 */
            .kpi-wrapper {{
                display: flex;
                flex-direction: row; /* 가로 방향 강제 */
                justify-content: space-around;
                align-items: center;
                background: white;
                padding: 20px 10px;
                border-radius: 12px;
                border: 1px solid #eff1f3;
                box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                margin-bottom: 25px;
                width: 100%;
            }}
            .kpi-unit {{ 
                text-align: center; 
                flex: 1;
                min-width: 100px; /* 항목이 너무 좁아지지 않게 */
            }}
            .kpi-label {{ 
                font-size: 12px; 
                color: #64748b; 
                margin-bottom: 4px;
                white-space: nowrap; /* 줄바꿈 방지 */
            }}
            .kpi-val {{ 
                font-size: 22px; 
                font-weight: 800; 
                color: #1e293b;
                white-space: nowrap; /* 줄바꿈 방지 */
            }}
            
            /* 그리드 타이틀 스타일 */
            .grid-title {{
                font-size: 13px; font-weight: 700; color: #475569;
                margin-bottom: 10px; display: flex; align-items: center; gap: 5px;
            }}
            /* 모든 컨테이너 내부 패딩 통일 */
            div[data-testid="stVerticalBlock"] > div > div > div[data-testid="stVerticalBlock"] {{
                padding: 0px !important;
                gap: 0.5rem !important;
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
        """한 줄로 압축된 슬림형 KPI 바"""
        # 1. 데이터 계산
        # [1] 분석 샘플수
        sample_count = str(len(f_df))
        
        # [2] 평균 구독료 (전체 서비스 합계: fee_service_total)
        avg_total_fee_val = f_df['fee_service_total'].mean() if 'fee_service_total' in f_df.columns else 0
        avg_total_fee = format(int(avg_total_fee_val), ',')

        # [3] OTT 평균 구독 개수 (True/False 컬럼들을 합산)
        ott_current_cols = [
            'ott_current_netflix', 'ott_current_tving', 'ott_current_wavve', 
            'ott_current_disney', 'ott_current_couplay', 'ott_current_watcha', 
            'ott_current_laftel', 'ott_current_etc'
        ]
        # 존재하는 컬럼만 필터링해서 합산
        available_ott_cols = [col for col in ott_current_cols if col in f_df.columns]
        if available_ott_cols:
            avg_ott_count_val = f_df[available_ott_cols].sum(axis=1).mean()
        else:
            avg_ott_count_val = 0
        avg_ott_count = format(avg_ott_count_val, '.1f')

        # [4] OTT 평균 월구독료 (각 OTT 요금 컬럼 합산)
        ott_fee_cols = [
            'ott_fee_netflix', 'ott_fee_tving', 'ott_fee_wavve', 
            'ott_fee_disney', 'ott_fee_couplay', 'ott_fee_watcha', 
            'ott_fee_laftel', 'ott_fee_etc'
        ]
        available_fee_cols = [col for col in ott_fee_cols if col in f_df.columns]
        if available_fee_cols:
            # 각 행별로 OTT 요금을 모두 더한 뒤 평균 계산
            avg_ott_fee_val = f_df[available_fee_cols].sum(axis=1).mean()
        else:
            avg_ott_fee_val = 0
        avg_ott_fee = format(int(avg_ott_fee_val), ',')

        # [5] 이탈 경험률 (ott_cancel)
        cancel_rate_val = (f_df['ott_cancel'] == '예').mean() * 100 if 'ott_cancel' in f_df.columns else 0
        cancel_rate = format(cancel_rate_val, '.1f')

        # 2. 문자열 조립 (f-string/중괄호 충돌 원천 차단)
        html_code = (
            '<div style="display: flex; flex-direction: row; justify-content: space-between; align-items: center; '
            'background: white; padding: 15px 10px; border-radius: 12px; border: 1px solid #eff1f3; '
            'box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 25px; width: 100%;">'
            
            '<div style="text-align: center; flex: 1;">'
            '<div style="font-size: 11px; color: #64748b; white-space: nowrap; margin-bottom: 2px;">분석 샘플수</div>'
            '<div style="font-size: 19px; font-weight: 800; color: #1e293b; white-space: nowrap;">' + sample_count + '명</div>'
            '</div>'
            '<div style="width:1px; height:20px; background:#f1f5f9;"></div>'

            '<div style="text-align: center; flex: 1.2;">'
            '<div style="font-size: 11px; color: #64748b; white-space: nowrap; margin-bottom: 2px;">평균 구독료</div>'
            '<div style="font-size: 19px; font-weight: 800; color: #1e293b; white-space: nowrap;">' + avg_total_fee + '원</div>'
            '</div>'
            '<div style="width:1px; height:20px; background:#f1f5f9;"></div>'

            '<div style="text-align: center; flex: 1.2;">'
            '<div style="font-size: 11px; color: #64748b; white-space: nowrap; margin-bottom: 2px;">OTT 평균 구독 개수</div>'
            '<div style="font-size: 19px; font-weight: 800; color: #1e293b; white-space: nowrap;">' + avg_ott_count + '개</div>'
            '</div>'
            '<div style="width:1px; height:20px; background:#f1f5f9;"></div>'

            '<div style="text-align: center; flex: 1.2;">'
            '<div style="font-size: 11px; color: #64748b; white-space: nowrap; margin-bottom: 2px;">OTT 평균 월구독료</div>'
            '<div style="font-size: 19px; font-weight: 800; color: #1e293b; white-space: nowrap;">' + avg_ott_fee + '원</div>'
            '</div>'
            '<div style="width:1px; height:20px; background:#f1f5f9;"></div>'

            '<div style="text-align: center; flex: 1;">'
            '<div style="font-size: 11px; color: #64748b; white-space: nowrap; margin-bottom: 2px;">OTT 이탈 경험률</div>'
            '<div style="font-size: 19px; font-weight: 800; color: #1e293b; white-space: nowrap;">' + cancel_rate + '%</div>'
            '</div>'
            '</div>'
        )

        st.markdown(html_code, unsafe_allow_html=True)

    def render_category_dot_plot(f_df, height=320):
        """막대 대신 덤벨(Lollipop) 차트로 공간 압축 및 가독성 확보"""
        cat_map = {
            "ott": "OTT", "shopping": "쇼핑/멤버십", "media": "미디어", 
            "aisw": "AI/SW", "food": "장보기/식음료", "edu": "도서/교육", 
            "game": "게임", "cleaning": "세탁/청소", "pack": "짐 보관", "etc": "기타"
        }
        
        plot_data = []
        for key, label in cat_map.items():
            ever_s = pd.to_numeric(f_df[f"service_ever_{key}"].replace({'TRUE':1,'FALSE':0,True:1,False:0}), errors='coerce').fillna(0)
            curr_s = pd.to_numeric(f_df[f"service_current_{key}"].replace({'TRUE':1,'FALSE':0,True:1,False:0}), errors='coerce').fillna(0)
            
            ever_val = int(ever_s.sum())
            curr_val = int(curr_s.sum())
            
            plot_data.append({'Category': label, '값': ever_val, '구분': '경험함'})
            plot_data.append({'Category': label, '값': curr_val, '구분': '현재이용'})

        pdf = pd.DataFrame(plot_data)
        
        # 1. 배경 선 (덤벨의 막대 부분) 생성
        fig = go.Figure()
        
        for cat in cat_map.values():
            cat_df = pdf[pdf['Category'] == cat]
            fig.add_trace(go.Scatter(
                x=cat_df['값'], y=[cat, cat],
                mode='lines',
                line=dict(color='#e2e8f0', width=4),
                showlegend=False,
                hoverinfo='none'
            ))

        # 2. 경험함/현재이용 점(Dot) 추가 + ,호버 템플릿
        for g, color, size in zip(['경험함', '현재이용'], ['#cbd5e1', BRAND_COLORS.MAIN_MINT], [10, 14]):
            g_df = pdf[pdf['구분'] == g]

            display_color = color if g == '현재이용' else "#6D6F72"
            custom_hover = f"<span style='color:{display_color}; font-weight:bold'>{g}</span><br>%{{y}}: %{{x}}<extra></extra>"

            fig.add_trace(go.Scatter(
                x=g_df['값'], y=g_df['Category'],
                mode='markers+text',
                name=g,
                marker=dict(color=color, size=size), # 차트 점 색상은 기존 유지
                text=g_df['값'] if g == '현재이용' else "", 
                textposition="middle right",
                textfont=dict(size=10, color='#475569', family="Pretendard"),
                hovertemplate=custom_hover
            ))

        fig.update_layout(
            height=height,
            margin=dict(t=30, b=30, l=10, r=20),
            xaxis=dict(showgrid=True, gridcolor='#f1f5f9', title=None),
            yaxis=dict(autorange="reversed", title=None), # 상위 항목이 위로 오게
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=0.98, xanchor="right", x=1.01),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
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
            # 1. 전체 평균 (호버 텍스트 색상을 더 진한 회색 #6D6F72로 설정)
            fig.add_trace(go.Scatterpolar(
                r=avg_total, theta=r_labels, fill='toself', name='전체 평균', 
                line_color='#cbd5e1',
                hovertemplate="<span style='color:#6D6F72; font-weight:bold'>전체 평균</span><br>%{theta}: %{r:.1f}점<extra></extra>"
            ))
            
            # 2. 선택 그룹 (호버 텍스트 색상을 메인 민트로 설정)
            fig.add_trace(go.Scatterpolar(
                r=avg_selected, theta=r_labels, fill='toself', name='선택 그룹', 
                line_color=BRAND_COLORS.MAIN_MINT,
                hovertemplate=f"<span style='color:{BRAND_COLORS.MAIN_MINT}; font-weight:bold'>선택 그룹</span><br>%{{theta}}: %{{r:.1f}}점<extra></extra>"
            ))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=False, range=[0, 7]),
                        angularaxis=dict(linecolor='rgba(200, 200, 200, 0.4)', linewidth=1),
                        domain=dict(x=[0, 1], y=[0.05, 1])), 
                height=height,
                margin=dict(t=30, b=30, l=30, r=40), 
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
                hoverlabel=dict(
                    font=dict(size=12, family="Pretendard"), 
                    align="left",
                    bgcolor="white",
                    bordercolor="#e2e8f0",
                    showarrow=False
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"레이더 차트 생성 중 오류가 발생했습니다: {e}")

    def render_brand_ranking(f_df, mode='pop'):
        """브랜드 랭킹 카드 (mode: 'pop'은 인원수, 'time'은 시청시간)"""
        brand_cols = [c for c in f_df.columns if 'ott_current_' in c and c not in ['ott_current', 'ott_current_none', 'ott_current_etc']]
        
        if mode == 'pop':
            title, suffix = "👥 이용자 수 순위", "명"
            data = f_df[brand_cols].sum().sort_values(ascending=False).head(5)
        else:
            title, suffix = "⏳ 주평균 시청시간", "분"
            time_cols = [f'ott_time_{c.split("_")[-1]}' for c in brand_cols if f'ott_time_{c.split("_")[-1]}' in f_df.columns]
            data = f_df[time_cols].mean().sort_values(ascending=False).head(5)

        # 1. 제목 생성
        title_html = f"<p style='font-size:12px; font-weight:700; color:#64748b; margin-top:-5px; margin-bottom:5px;'>{title}</p>"
    
        # 2. 리스트 아이템 생성 (가장 안전한 join 방식)
        items_list = []
        for i, (col, val) in enumerate(data.items()):
            b_name = col.split('_')[-1].upper()
            item = (
                f"<div class='rank-item'>"
                f"<div><span class='rank-number'>{i+1}위</span><span class='rank-name'>{b_name}</span></div>"
                f"<div class='rank-value'>{int(val)}{suffix}</div>"
                f"</div>"
            )
            items_list.append(item)
        
        # 3. 전체 결합 및 렌더링
        full_content = f"{title_html}<div class='ranking-container'>{''.join(items_list)}</div>"
        
        # [중요] 반드시 st.write나 일반 호출이 아닌 unsafe_allow_html=True를 포함한 st.markdown 사용
        st.markdown(full_content, unsafe_allow_html=True)

    def render_cancel_reasons(f_df, height=300):
        """해지 사유 가로 바 차트"""
        column_mapping = {
            'ott_cancel_reason_series': '보던 시리즈 종료',
            'ott_cancel_reason_low_usage': '접속 빈도 낮음',
            'ott_cancel_reason_alert': '자동결제 알림 보고',
            'ott_cancel_reason_switching': '타 OTT 이동',
            'ott_cancel_reason_contents': '콘텐츠 부족',
            'ott_cancel_reason_price': '가격 부담',
            'ott_cancel_reason_etc': '기타'
            }
        
        # 데이터 추출 (해지 경험자 대상)
        target_df = f_df[f_df['ott_cancel'] == '예'].copy()

        # 에러 방지: 데이터가 없으면 안내 문구 출력 후 종료
        if target_df.empty:
            st.info("해지 사유 데이터가 없습니다.")
            return

        # 빈도 계산
        counts_dict = {}
        for col, label in column_mapping.items():
            if col in target_df.columns:
                counts_dict[label] = target_df[col].fillna(0).astype(int).sum()
            else:
                counts_dict[label] = 0

        # '기타' 상세 내용만 ott_cancel_reason 컬럼에서 별도로 추출
        etc_details = []
        if 'ott_cancel_reason' in target_df.columns:
            # 모든 응답을 쉼표로 쪼갠 뒤 '기타('가 포함된 텍스트만 필터링
            all_reasons = target_df['ott_cancel_reason'].dropna().str.split(',').explode().str.strip()
            for resp in all_reasons:
                if '기타' in resp:
                    # 괄호 안의 내용만 추출 (예: 기타(화질 불만) -> 화질 불만)
                    detail = re.findall(r'\((.*?)\)', resp)
                    if detail:
                        etc_details.append(detail[0])
                    elif len(resp) > 2: # '기타' 두 글자보다 길면 상세 내용으로 간주
                        etc_details.append(resp.replace('기타', '').strip())

        # 차트용 정렬 데이터 생성
        sorted_counts = pd.Series(counts_dict).sort_values(ascending=True)
        plot_labels = sorted_counts.index.tolist()
        plot_values = sorted_counts.values.tolist()

        # 호버 텍스트 구성
        unique_etc = list(dict.fromkeys([d for d in etc_details if d]))
        etc_hover_list = "• " + "<br>• ".join(unique_etc[:7]) if unique_etc else "상세 내용 없음"
        if len(unique_etc) > 7: etc_hover_list += "<br>..."

        hover_texts = []
        for label in plot_labels:
            if label == '기타':
                hover_texts.append(etc_hover_list) # 기타만 상세 리스트 전달
            else:
                hover_texts.append("") # 나머지는 빈 값

        fig = go.Figure(go.Bar(
            x=plot_values,
            y=plot_labels,
            orientation='h',
            marker_color=BRAND_COLORS.MAIN_MINT,
            text=plot_values,
            textposition='outside',
            textfont=dict(size=11, color=BRAND_COLORS.LIGHT_TEXT),
            customdata=hover_texts,
            hovertemplate=(
                "%{y}: %{x}<br>" + 
                "%{customdata}<extra></extra>"
            ),
            cliponaxis=False
        ))

        fig.update_layout(
            height=height,
            margin=dict(t=10, b=10, l=40, r=20),
            xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
            yaxis=dict(tickfont=dict(size=12, color=BRAND_COLORS.LIGHT_TEXT)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hoverlabel=dict(bgcolor="white", font_size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    def render_voc_bubbles(f_df):
        """VOC 말풍선"""
        items_html = "" # 초기화
    
        # 1. 데이터 추출
        raw_voc = f_df['pain_point_open'].dropna().astype(str).tolist()

        # 2. 강력한 블랙리스트 (원본 유지)
        final_blacklist = [
            '없음', '딱히', '생각', '않음', '생각나지', '모르겠음', '안남', '안나요', '안나',
            '생각나지 않음', '기타', '없습니다', '생각이', '없어요', '아니오', 'X', 'x', 'nan', '그냥', '글쎄요', '모르겠어요', '.....'
        ]

        # 3. 유사 문구 통합용 키워드 맵 (원본 유지)
        similarity_map = {
            "콘텐츠가 어느 OTT에 있는지 확인이 번거로움": ["어느 OTT", "어디에 있는지", "어디에서 서비스", "콘텐츠 검색", "컨텐츠 검색"],
            "해지 절차가 복잡하고 찾기 어려움": ["해지 방법", "해지 버튼", "탈퇴", "해지 절차", "여러 단계"],
            "자동 결제 알림 누락 및 갱신 불만": ["자동 결제", "결제 알림", "자동 갱신", "몰래 결제"],
            "구독료 대비 이용 빈도 낮음": ["가격", "비싸", "금액", "돈", "이용 빈도"]
        }

        refined_voc = []
        seen = set()

        for text in raw_voc:
            clean_text = text.strip()
            
            if any(bad_word in clean_text for bad_word in final_blacklist) or len(clean_text) <= 1: 
                continue
                
            display_text = clean_text
            for rep, kws in similarity_map.items():
                if any(kw in clean_text for kw in kws):
                    display_text = rep
                    break
            
            if display_text not in seen:
                refined_voc.append(display_text)
                seen.add(display_text)

        if not refined_voc: return ""

        # f-string 대신 % 포맷팅이나 일반 결합을 사용하여 중괄호 충돌 방지
        for v in refined_voc:
            style = (
                "padding: 8px 10px; "
                "border-bottom: 1px solid #f1f5f9; "
                "font-size: 13px; "
                "line-height: 1.4; "
                "color: #334155; "
                "display: block;"
            )
            # 태그가 깨지지 않도록 가장 원시적인 방법으로 조립
            items_html += '<div style="' + style + '">“' + str(v) + '”</div>'
        
        return items_html
    
    def render_cancel_reason_heatmap(f_df, height=280):
        # 1. 해지 사유 컬럼 리스트 (Boolean 데이터)
        cancel_cols = [
            'ott_cancel_reason_series', 'ott_cancel_reason_low_usage',
            'ott_cancel_reason_alert', 'ott_cancel_reason_switching',
            'ott_cancel_reason_contents', 'ott_cancel_reason_price',
            'ott_cancel_reason_etc'
        ]
        
        # 한글 라벨 매핑
        labels = ['보던 시리즈 종료', '접속 빈도 낮음', '자동결제 알림 보고', '타 OTT 이동', '콘텐츠 부족', '가격 부담', '기타']
        
        # 2. 해지 경험이 있는 사람만 필터링 및 데이터 추출
        cancel_df = f_df[f_df['ott_cancel'] == '예'][cancel_cols].fillna(False).astype(int)
        
        if cancel_df.empty:
            st.info("해지 경험 데이터가 부족하여 히트맵을 표시할 수 없습니다.")
            return

        # 3. 공통 발생 행렬(Co-occurrence Matrix) 계산
        # 행렬 곱을 통해 두 사유가 동시에 True(1)인 횟수를 구함
        co_matrix = cancel_df.T @ cancel_df
        
        # 4. 히트맵 시각화
        fig = go.Figure(data=go.Heatmap(
            z=co_matrix.values,
            x=labels,
            y=labels,
            colorscale=[[0, BRAND_COLORS.LIGHT_CARD], [1, BRAND_COLORS.MAIN_MINT]], 
            text=co_matrix.values,
            texttemplate="%{text}",
            textfont=dict(size=11, color=BRAND_COLORS.LIGHT_TEXT),
            hoverinfo='none',
            colorbar=dict(
                thickness=15,
                outlinecolor='rgba(0,0,0,0)', # 테두리 투명하게
                bordercolor='rgba(0,0,0,0)',  # 외곽선 투명하게
                tickfont=dict(size=10, color=BRAND_COLORS.SUB_TEXT),
                len=0.9
            )
        ))

        fig.update_layout(
            height=height,
            margin=dict(t=15, b=30, l=10, r=10),
            xaxis=dict(side='bottom', tickfont=dict(size=10, color=BRAND_COLORS.SUB_TEXT)),
            yaxis=dict(tickfont=dict(size=10, color=BRAND_COLORS.SUB_TEXT), autorange='reversed'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # endregion

    # region 4-2. 메인 페이지 함수 (레이더/배치)
    if f_df.empty:
        st.error("조건에 맞는 데이터가 없습니다.")
    else:
        st.markdown("## 📊 데이터 부록: 구독 행태 심층 분석")

       # [Layer 1] 통합 KPI 카드
        render_kpi_metrics(f_df)

    # 2. 메인 분석 그리드 (덤벨 / 랭킹 / 레이더)
    CARD_HEIGHT = 310
    row1_col1, row1_col2, row1_col3 = st.columns([1.6, 1.2, 1.4])

    with row1_col1:
        with st.container(border=True):
            st.markdown("<div class='grid-title'>🎯 카테고리별 유지율</div>", unsafe_allow_html=True)
            render_category_dot_plot(f_df, height=CARD_HEIGHT)

    with row1_col2:
        with st.container(border=True):
            st.markdown("<div class='grid-title'>🏆 브랜드별 랭킹</div>", unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

            # gap='large'를 추가하여 두 랭킹 사이를 벌립니다.
            sub_col1, sub_col2 = st.columns(2, gap="medium")

            with sub_col1:
                render_brand_ranking(f_df, mode='pop')

            with sub_col2:
                render_brand_ranking(f_df, mode='time')

            st.markdown(
                f"<div style='height:19px'></div>",
                unsafe_allow_html=True
            )

    with row1_col3:
        with st.container(border=True):
            st.markdown("<div class='grid-title'>🕸️ 중요 가치 비교</div>", unsafe_allow_html=True)
            render_value_radar(f_df, df, height=CARD_HEIGHT)

    # 3. 하단 상세 그리드 (해지 사유 top5 / 히트맵 / VOC)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    row2_col1, row2_col2, row2_col3 = st.columns([1, 1.6, 0.4]) 

    COMMON_HEIGHT = 300

    with row2_col1:
        with st.container(border=True):
            st.markdown("<div class='grid-title'>📊 해지 사유</div>", unsafe_allow_html=True)
            render_cancel_reasons(f_df, height=COMMON_HEIGHT) 

    with row2_col2:
        with st.container(border=True):
            st.markdown("<div class='grid-title'>🔗 사유 간 복합 관계</div>", unsafe_allow_html=True)
            render_cancel_reason_heatmap(f_df, height=COMMON_HEIGHT)

    with row2_col3:
        with st.container(border=True):
            st.markdown("<div class='grid-title'>💬 VOC-OTT앱 불편한 점</div>", unsafe_allow_html=True)

            # 함수에서 HTML 내용만 가져옴
            voc_content = render_voc_bubbles(f_df)

            custom_css = f"""
            <style>
                .voc-outer-frame {{
                    padding: 0px 2px 10px 2px !important; 
                }}
                .voc-viewport {{
                    position: relative;
                    height: {COMMON_HEIGHT + 6}px; 
                    overflow: hidden;
                }}
                .voc-scroll-area {{
                    height: 100%;
                    overflow-y: auto;
                    scrollbar-width: none;
                    -ms-overflow-style: none;
                    padding-bottom: 60px !important;
                }}
                .voc-scroll-area::-webkit-scrollbar {{
                    display: none;
                }}
                .voc-viewport::after {{
                    content: '';
                    position: absolute;
                    bottom: 0; left: 0; right: 0; height: 50px;
                    z-index: 5;
                    pointer-events: none;
                    background: linear-gradient(to top, rgba(255,255,255,1) 0%, rgba(255,255,255,0) 100%);
                }}
            </style>
            """
            
            # 레이아웃 조립
            main_html = f"""
            <div class="voc-outer-frame">
                <div class="voc-viewport">
                    <div class="voc-scroll-area">
                        {voc_content}
                        <div style="height: 10px;"></div>
                    </div>
                </div>
            </div>
            """
            
            st.markdown(custom_css + main_html, unsafe_allow_html=True)
    # endregion