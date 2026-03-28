import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

class SkinVisualizer:
    def __init__(self, df):
        self.df = df
        self.cols = df.columns

    def plot_target_distribution(self):
        st.markdown("##### 1. 고객 타겟 분포")
        # 연령대 분포 (Q1)
        fig = px.pie(self.df, names=self.cols[1], hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)

    def plot_skin_concerns(self):
        st.markdown("##### 2. 피부 고민 Top 6")
        # 다중 선택(Q3) 처리
        concerns = self.df[self.cols[3]].str.get_dummies(sep=', ').sum().sort_values()
        fig = px.bar(concerns, orientation='h', color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)

    def plot_visit_vs_reason(self):
        st.markdown("##### 3. 방문 패턴 및 홈케어 사유 분석")
        fig = px.bar(self.df, x=self.cols[4], color=self.cols[5], barmode='group')
        st.plotly_chart(fig, use_container_width=True)

    def plot_cost_analysis(self):
        st.markdown("##### 4. 월 최대 지출 가능 비용")
        fig = px.histogram(self.df, x=self.cols[9], color_discrete_sequence=['#FF6666'])
        st.plotly_chart(fig, use_container_width=True)

    def plot_selection_criteria(self):
        st.markdown("##### 5. 에스테틱 선택 핵심 요소")
        fig = px.funnel_area(names=self.df[self.cols[11]].value_counts().index,
                             values=self.df[self.cols[11]].value_counts().values)
        st.plotly_chart(fig, use_container_width=True)