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
                background: #f8fafc;
                border-radius: 12px;
                padding: 12px;
                border: 1px solid #f1f5f9;
            }}
            .rank-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 6px 0;
                border-bottom: 1px solid #f1f5f9;
            }}
            .rank-item:last-child {{ border-bottom: none; }}
            .rank-number {{
                font-size: 10px;
                font-weight: 800;
                color: {BRAND_COLORS.MAIN_MINT};
                margin-right: 6px;
            }}
            .rank-name {{
                font-size: 12px;
                font-weight: 600;
                color: #334155;
            }}
            .rank-value {{
                font-size: 11px;
                color: #64748b;
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

        # 2. 경험함/현재이용 점(Dot) 추가
        for g, color, size in zip(['경험함', '현재이용'], ['#cbd5e1', BRAND_COLORS.MAIN_MINT], [10, 14]):
            g_df = pdf[pdf['구분'] == g]
            fig.add_trace(go.Scatter(
                x=g_df['값'], y=g_df['Category'],
                mode='markers+text',
                name=g,
                marker=dict(color=color, size=size),
                text=g_df['값'] if g == '현재이용' else "", # 현재 이용수만 텍스트 노출
                textposition="middle right",
                textfont=dict(size=10, color='#475569', family="Pretendard")
            ))

        fig.update_layout(
            height=height,
            margin=dict(t=20, b=20, l=0, r=40),
            xaxis=dict(showgrid=True, gridcolor='#f1f5f9', title=None),
            yaxis=dict(autorange="reversed", title=None), # 상위 항목이 위로 오게
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
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
            title, suffix = "👥 이용자 수 순위", "명"
            data = f_df[brand_cols].sum().sort_values(ascending=False).head(5)
        else:
            title, suffix = "⏳ 주평균 시청시간", "분"
            time_cols = [f'ott_time_{c.split("_")[-1]}' for c in brand_cols if f'ott_time_{c.split("_")[-1]}' in f_df.columns]
            data = f_df[time_cols].mean().sort_values(ascending=False).head(5)

        # 1. 제목 생성
        title_html = f"<p style='font-size:12px; font-weight:700; color:#64748b; margin-bottom:5px;'>{title}</p>"
    
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

       # [Layer 1] 통합 KPI 카드
        render_kpi_metrics(f_df)

    # 2. 메인 분석 그리드 (덤벨 / 랭킹 / 레이더)
    row1_col1, row1_col2, row1_col3 = st.columns([1.4, 1, 1])

    with row1_col1:
        with st.container(border=True):
            st.markdown("<div class='grid-title'>🎯 카테고리별 유지율</div>", unsafe_allow_html=True)
            render_category_dot_plot(f_df, height=330)

    with row1_col2:
        with st.container(border=True): # 랭킹은 컨테이너 자체가 카드 역할을 함
            render_brand_ranking(f_df, mode='pop')
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            render_brand_ranking(f_df, mode='time')

    with row1_col3:
        with st.container(border=True):
            st.markdown("<div class='grid-title'>🕸️ 중요 가치 비교</div>", unsafe_allow_html=True)
            render_value_radar(f_df, df, height=330)

    # 3. 하단 상세 그리드 (해지 사유 / VOC) - 사라졌던 부분 복구!
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    row2_col1, row2_col2 = st.columns([1, 1.2])

    with row2_col1:
        with st.container(border=True):
            st.markdown("<div class='grid-title'>🚩 주요 해지 사유 (Top 5)</div>", unsafe_allow_html=True)
            render_cancel_reasons(f_df, height=200)

    with row2_col2:
        with st.container(border=True):
            st.markdown("<div class='grid-title'>💬 사용자 페인포인트</div>", unsafe_allow_html=True)
            render_voc_bubbles(f_df)

    # endregion