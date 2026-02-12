import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="로스트아크 시세 변동",
    layout="wide"
)

st.title("Lost Ark Market Trends")
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-bottom: 2px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)
st.info("GitHub Actions를 통해 매시간 수집된 데이터를 시각화합니다.")


# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리 함수
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


def preprocess_for_chart(df, selected_items):
    if df is None or df.empty or not selected_items:
        return pd.DataFrame()

    # 1. 아이템 필터링
    df_filtered = df[df['item_name'].isin(selected_items)].copy()

    # 2. 불필요한 컬럼 제거
    if 'sub_category' in df_filtered.columns:
        df_filtered = df_filtered.drop(columns=['sub_category'])

    df_filtered = df_filtered.set_index('item_name')

    # 3. 행/열 뒤집기 (Transpose)
    df_transposed = df_filtered.T

    # 4. 인덱스(날짜 문자열)를 Datetime 객체로 변환
    df_transposed.index = pd.to_datetime(df_transposed.index, errors='coerce')

    return df_transposed


# -----------------------------------------------------------------------------
# 3. 데이터 로드
# -----------------------------------------------------------------------------
df_materials = load_data("market_materials.csv")
df_lifeskill = load_data("market_lifeskill.csv")
df_battle = load_data("market_battleitems.csv")
df_engravings = load_data("market_engravings.csv")
df_gems = load_data("market_gems.csv")

# -----------------------------------------------------------------------------
# 4. 탭 구성 (아이콘 제거)
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "강화 재료", "생활 재료", "배틀 아이템", "각인서", "보석"
])

# --- Tab 1: 강화 재료 ---
with tab1:
    st.subheader("강화 재료 시세")
    if df_materials is not None:
        all_items = df_materials['item_name'].unique()
        default_items = ["운명의 파괴석", "운명의 수호석", "운명의 돌파석"] if "운명의 파괴석" in all_items else all_items[:3]

        selected = st.multiselect("확인할 재료를 선택하세요", all_items, default=default_items, key="mat_select")

        chart_data = preprocess_for_chart(df_materials, selected)
        if not chart_data.empty:
            st.line_chart(chart_data)
            with st.expander("상세 데이터 표 보기"):
                st.dataframe(chart_data.sort_index(ascending=False))
    else:
        st.warning("아직 데이터가 수집되지 않았습니다.")

# --- Tab 2: 생활 재료 ---
with tab2:
    st.subheader("생활 재료 시세")
    if df_lifeskill is not None:
        if 'sub_category' in df_lifeskill.columns:
            categories = df_lifeskill['sub_category'].unique()
            selected_cat = st.selectbox("생활 카테고리 선택", categories, index=0)
            filtered_items = df_lifeskill[df_lifeskill['sub_category'] == selected_cat]['item_name'].unique()
        else:
            filtered_items = df_lifeskill['item_name'].unique()

        selected_life = st.multiselect("재료 선택", filtered_items, default=filtered_items[:5], key="life_select")

        chart_data = preprocess_for_chart(df_lifeskill, selected_life)
        if not chart_data.empty:
            st.line_chart(chart_data)
    else:
        st.warning("데이터 준비 중입니다.")

# --- Tab 3: 배틀 아이템 ---
with tab3:
    st.subheader("배틀 아이템 시세")
    if df_battle is not None:
        all_battle = df_battle['item_name'].unique()
        defaults = [i for i in ["정령의 회복약", "암흑 수류탄", "파괴 폭탄"] if i in all_battle]

        selected_battle = st.multiselect("아이템 선택", all_battle, default=defaults, key="battle_select")

        chart_data = preprocess_for_chart(df_battle, selected_battle)
        if not chart_data.empty:
            st.line_chart(chart_data)
    else:
        st.warning("데이터 준비 중입니다.")

# --- Tab 4: 각인서 ---
with tab4:
    st.subheader("유물 각인서 시세")
    if df_engravings is not None:
        all_eng = df_engravings['item_name'].unique()
        selected_eng = st.multiselect("각인서 선택", all_eng, default=all_eng[:1], key="eng_select")

        chart_data = preprocess_for_chart(df_engravings, selected_eng)
        if not chart_data.empty:
            st.line_chart(chart_data)
    else:
        st.warning("데이터 준비 중입니다.")

# --- Tab 5: 보석 ---
with tab5:
    st.subheader("T4 보석 (8~10레벨 겁화/작열) 최저가")
    if df_gems is not None:
        all_gems = df_gems['item_name'].unique()
        selected_gems = st.multiselect("보석 선택", all_gems, default=all_gems, key="gem_select")

        chart_data = preprocess_for_chart(df_gems, selected_gems)
        if not chart_data.empty:
            st.line_chart(chart_data)
            st.caption("※ 경매장 즉시 구매가 최저가 기준입니다.")
    else:
        st.warning("데이터 준비 중입니다.")