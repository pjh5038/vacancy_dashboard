import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import folium
from streamlit_folium import st_folium

# -----------------------------
# 1. KOSIS API 호출
# -----------------------------
API_KEY = "ZmZiZmUxOTkzNzRlNDM3YmZiZGIwNDk1OTg3ZjJhNjc="
url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
params = {
    "method": "getList",
    "apiKey": API_KEY,
    "itmId": "T10 T20 T30",  # 총주택, 빈집수, 빈집비율
    "objL1": "11 21 22 23 24 25 26 29 31 32 33 34 35 36 37 38 39",
    "format": "json",
    "jsonVD": "Y",
    "prdSe": "Y",
    "newEstPrdCnt": 1,
    "orgId": "101",
    "tblId": "DT_1YL202005"
}
response = requests.get(url, params=params)
data = response.json()

# -----------------------------
# 2. 데이터 전처리
# -----------------------------
df = pd.DataFrame(data)
df = df[["C1_NM", "ITM_ID", "ITM_NM", "DT", "PRD_DE"]]
df = df.pivot_table(index=["C1_NM", "PRD_DE"], columns="ITM_ID", values="DT", aggfunc="first").reset_index()
df.columns.name = None

df = df.rename(columns={
    "C1_NM": "행정구역",
    "PRD_DE": "연도",
    "T10": "전체 주택 수",
    "T20": "빈집 수",
    "T30": "빈집 비율(%)"
})

for col in ["전체 주택 수", "빈집 수", "빈집 비율(%)"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 최신 연도 데이터만 사용
latest_year = df["연도"].max()
df = df[df["연도"] == latest_year].reset_index(drop=True)

# -----------------------------
# 3. Streamlit UI
# -----------------------------
st.set_page_config(page_title="빈집 비율 대시보드", layout="wide")
st.title("🏚️ 전국 시도별 빈집 비율 대시보드")

selected_region = st.selectbox("📍 행정구역을 선택하세요", df["행정구역"].tolist())
selected_row_df = df[df["행정구역"] == selected_region].iloc[[0]]
selected_row = selected_row_df.iloc[0]

# -----------------------------
# 4. 순위 계산 및 출력
# -----------------------------
df["빈집 비율 순위"] = df["빈집 비율(%)"].rank(ascending=False).astype(int)
df["빈집 수 순위"] = df["빈집 수"].rank(ascending=False).astype(int)
df["전체 주택 수 순위"] = df["전체 주택 수"].rank(ascending=False).astype(int)

rank_row = df[df["행정구역"] == selected_region].iloc[0]

st.markdown(f"""
### 📊 {selected_region} 순위 정보
- 📉 **빈집 비율 순위**: {rank_row['빈집 비율 순위']}위
- 🏠 **빈집 수 순위**: {rank_row['빈집 수 순위']}위
- 🏘️ **전체 주택 수 순위**: {rank_row['전체 주택 수 순위']}위
""")

# -----------------------------
# 5. 시각화 (차트 + 지도)
# -----------------------------
col1, col2 = st.columns([1.4, 1])

with col1:
    fig = px.bar(
        df.sort_values(by="빈집 비율(%)", ascending=False),
        x="행정구역",
        y="빈집 비율(%)",
        color="행정구역",
        text="빈집 비율(%)",
        title=f"{latest_year}년 빈집 비율"
    )
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    coords = {
        "서울특별시": [37.5665, 126.9780], "부산광역시": [35.1796, 129.0756],
        "대구광역시": [35.8714, 128.6014], "인천광역시": [37.4563, 126.7052],
        "광주광역시": [35.1595, 126.8526], "대전광역시": [36.3504, 127.3845],
        "울산광역시": [35.5384, 129.3114], "세종특별자치시": [36.4800, 127.2890],
        "경기도": [37.4138, 127.5183], "강원도": [37.8228, 128.1555],
        "충청북도": [36.6357, 127.4917], "충청남도": [36.5184, 126.8000],
        "전라북도": [35.7167, 127.1442], "전라남도": [34.8161, 126.4629],
        "경상북도": [36.4919, 128.8889], "경상남도": [35.4606, 128.2132],
        "제주특별자치도": [33.4996, 126.5312]
    }

    if selected_region in coords:
        m = folium.Map(location=coords[selected_region], zoom_start=7)
        folium.Marker(
            location=coords[selected_region],
            tooltip=selected_region,
            popup=f"{selected_region} 위치",
            icon=folium.Icon(color="red", icon="home")
        ).add_to(m)
        st_folium(m, width=500, height=400)
    else:
        st.warning("해당 지역의 좌표 정보가 없어 지도를 표시할 수 없습니다.")
