import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Loconomy",
    layout="wide"
)

st.title("Lost Ark Market Trends")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        white-space: pre-wrap; 
        background-color: #ffffff; 
        border-radius: 4px 4px 0 0; 
        gap: 1px; 
        padding-top: 10px; 
        padding-bottom: 10px; 
    }
    .stTabs [aria-selected="true"] { 
        background-color: #ffffff; 
        border-bottom: 2px solid #ff4b4b; 
    }
    </style>
    """, unsafe_allow_html=True)
st.info("GitHub Actions를 통해 매시간 수집된 데이터를 시각화합니다.")


# -----------------------------------------------------------------------------
# 2. 데이터 및 이벤트 로드 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def load_data(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    file_path = os.path.join(project_root, "data", file_name)

    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path)
    return df


def load_event_logs():
    events = {}
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    file_path = os.path.join(project_root, "data", "event_log.txt")

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    if ":" in line:
                        name, date_str = line.replace('"', '').split(":")
                        events[name.strip()] = date_str.strip()
                except:
                    continue
    return events


def preprocess_for_chart(df, selected_items):
    if df is None or df.empty or not selected_items:
        return pd.DataFrame()

    df_filtered = df[df['item_name'].isin(selected_items)].copy()
    if 'sub_category' in df_filtered.columns:
        df_filtered = df_filtered.drop(columns=['sub_category'])

    df_filtered = df_filtered.set_index('item_name')
    df_transposed = df_filtered.T
    df_transposed.index = pd.to_datetime(df_transposed.index, errors='coerce')

    return df_transposed


# -----------------------------------------------------------------------------
# 3. 주식 스타일 차트 그리기
# -----------------------------------------------------------------------------
def draw_stock_chart(df, title_text=""):
    if df.empty:
        st.warning("표시할 데이터가 없습니다.")
        return

    fig = go.Figure()

    for column in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df[column],
            mode='lines', name=column,
            line=dict(width=2),
            hovertemplate='%{x|%m/%d %H:%M} - %{y:,.0f} 골드<extra></extra>'
        ))

    min_date = df.index.min()
    max_date = df.index.max()

    if not pd.isnull(min_date) and not pd.isnull(max_date):
        current_ptr = min_date.replace(hour=0, minute=0, second=0)
        while current_ptr <= max_date:
            if current_ptr.weekday() == 2:
                patch_start = current_ptr.replace(hour=6, minute=0)
                patch_end = current_ptr.replace(hour=10, minute=0)
                if min_date <= patch_end and patch_start <= max_date:
                    fig.add_vrect(
                        x0=patch_start,
                        x1=patch_end,
                        fillcolor="rgba(128, 128, 128, 0.2)",
                        layer="below",
                        line_width=0,
                        annotation_text="점검",
                        annotation_position="top left",
                        annotation_font=dict(color="gray", size=10)
                    )
            current_ptr += timedelta(days=1)

        event_logs = load_event_logs()
        for name, date_str in event_logs.items():
            try:
                event_date = pd.to_datetime(date_str).replace(hour=0, minute=0)
                if min_date <= event_date <= max_date:
                    fig.add_vline(x=event_date, line_width=2, line_dash="dot", line_color="#E74C3C")
                    fig.add_annotation(
                        x=event_date, y=1.05, yref="paper",
                        text=name, showarrow=False,
                        font=dict(color="#E74C3C", size=11),
                        bgcolor="rgba(255, 255, 255, 0.9)"
                    )
            except:
                continue

    kor_days = ['월', '화', '수', '목', '금', '토', '일']
    tick_vals = pd.date_range(start=min_date.date(), end=max_date.date(), freq='D')
    tick_text = [d.strftime(f'%m/%d ({kor_days[d.weekday()]})') for d in tick_vals]

    fig.update_layout(
        title=dict(text=title_text, font=dict(size=18)),
        hovermode="x unified",
        template="plotly_white",
        xaxis=dict(
            showgrid=True,
            gridcolor='#eee',
            rangeslider=dict(visible=True),
            type="date",
            tickmode='array',
            tickvals=tick_vals,
            ticktext=tick_text,
            tick0=min_date.replace(hour=0, minute=0, second=0),
            dtick=86400000,
            tickangle=0,
        ),
        yaxis=dict(showgrid=True, gridcolor='#eee', tickformat=',', title="가격 (골드)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=80, b=20),
        height=550
    )

    st.plotly_chart(fig, use_container_width=True)


# -----------------------------------------------------------------------------
# 4. 데이터 로드 및 탭 구성
# -----------------------------------------------------------------------------
df_materials = load_data("market_materials.csv")
df_lifeskill = load_data("market_lifeskill.csv")
df_battle = load_data("market_battleitems.csv")
df_engravings = load_data("market_engravings.csv")
df_gems = load_data("market_gems.csv")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["강화 재료", "생활 재료", "배틀 아이템", "각인서", "보석"])

# --- Tab 1: 강화 재료 ---
with tab1:
    st.subheader("강화 재료 시세")
    if df_materials is not None:
        all_items = df_materials['item_name'].unique()
        default_items = ["운명의 파괴석", "운명의 파괴석 결정"]
        valid_defaults = [item for item in default_items if item in all_items]

        selected = st.multiselect("확인할 재료를 선택하세요", all_items, default=valid_defaults)
        chart_data = preprocess_for_chart(df_materials, selected)

        if not chart_data.empty:
            draw_stock_chart(chart_data, "강화 재료 시세 변동")

            st.divider()
            st.markdown("#### 교환 효율 분석")

            exchange_pairs = [
                ("찬란한 명예의 돌파석", "운명의 돌파석"),
                ("운명의 돌파석", "위대한 운명의 돌파석"),
                ("정제된 파괴강석", "운명의 파괴석"),
                ("운명의 파괴석", "운명의 파괴석 결정"),
                ("정제된 수호강석", "운명의 수호석"),
                ("운명의 수호석", "운명의 수호석 결정"),
                ("최상급 오레하 융화 재료", "아비도스 융화 재료"),
                ("아비도스 융화 재료", "상급 아비도스 융화 재료")
            ]

            show_exchange = st.checkbox("선택한 재료의 교환비 비교 보기", value=True)
            if show_exchange:
                active_pairs = [(l, h) for l, h in exchange_pairs if l in selected and h in selected]

                if not active_pairs:
                    st.caption("하위 재료와 상위 재료를 함께 선택하면 분석 차트가 나타납니다.")
                else:
                    for low, high in active_pairs:
                        st.markdown(f"##### [{high}] 교환 효율 분석")
                        df_pair = chart_data[[low, high]].copy()
                        df_pair[f"{low} (x5)"] = df_pair[low] * 5

                        draw_stock_chart(df_pair[[f"{low} (x5)", high]], f"{low} 5묶음 vs {high} 1묶음")

                        last_low_5 = df_pair[low].iloc[-1] * 5
                        last_high = df_pair[high].iloc[-1]
                        diff = last_high - last_low_5

                        if diff > 0:
                            st.success(f"**{low}** → **{high}** 교환 : 약 **{diff:,.0f} 골드** 이득")
                        elif diff < 0:
                            st.error(f"**{low}** → **{high}** 교환 : 약 **{abs(diff):,.0f} 골드** 손해")
                        else:
                            st.info("교환 가격과 구매 가격이 동일합니다.")
    else:
        st.warning("데이터 수집 중입니다.")

with tab2:
    st.subheader("생활 재료 시세")
    if df_lifeskill is not None:
        selected_cat = st.selectbox("생활 카테고리 선택", df_lifeskill['sub_category'].unique())
        filtered_items = df_lifeskill[df_lifeskill['sub_category'] == selected_cat]['item_name'].unique()
        selected_life = st.multiselect("재료 선택", filtered_items, default=filtered_items[:5])
        chart_data = preprocess_for_chart(df_lifeskill, selected_life)
        if not chart_data.empty: draw_stock_chart(chart_data)

with tab3:
    st.subheader("배틀 아이템 시세")
    if df_battle is not None:
        all_battle = df_battle['item_name'].unique()
        selected_battle = st.multiselect("아이템 선택", all_battle, default=all_battle[:5])
        chart_data = preprocess_for_chart(df_battle, selected_battle)
        if not chart_data.empty: draw_stock_chart(chart_data)

with tab4:
    st.subheader("유물 각인서 시세")
    if df_engravings is not None:
        all_eng = df_engravings['item_name'].unique()
        selected_eng = st.multiselect("각인서 선택", all_eng, default=all_eng[:1])
        chart_data = preprocess_for_chart(df_engravings, selected_eng)
        if not chart_data.empty: draw_stock_chart(chart_data)

with tab5:
    st.subheader("T4 보석 최저가")
    if df_gems is not None:
        all_gems = df_gems['item_name'].unique()
        selected_gems = st.multiselect("보석 선택", all_gems, default=all_gems)
        chart_data = preprocess_for_chart(df_gems, selected_gems)
        if not chart_data.empty: draw_stock_chart(chart_data)