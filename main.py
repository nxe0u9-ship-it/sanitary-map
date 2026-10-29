from pathlib import Path
import base64

import streamlit as st
import plotly.graph_objects as go


# ──────────────────────────────
# 1. 기본 설정
# ──────────────────────────────
st.set_page_config(
    page_title="우리 학교 위생맵",
    page_icon="🧫",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
MAP_PATH = BASE_DIR / "school_map.png"


# ──────────────────────────────
# 2. 평면도에 표시할 장소와 좌표
# ──────────────────────────────
# 왼쪽 위가 (0, 0), 오른쪽 아래가 (100, 100)
# 좌표는 평면도 위 선택 지점의 위치를 뜻함.
PLACES = {
    "운동장": (36, 15),
    "인쇄실": (18, 36),
    "보건실": (26, 36),
    "방송실": (34, 36),
    "교무 1실": (42, 36),
    "당직실": (50, 36),
    "중앙정원": (34, 57),
    "본관 왼쪽 화장실": (8, 35),
    "본관 위쪽 화장실": (64, 30),
    "본관 아래쪽 화장실": (64, 80),
    "분리수거장": (6, 58),
    "엘리베이터": (6, 76),
    "청소 휴게실": (6, 84),
    "생명과학 실험실": (18, 86),
    "학습 도움실": (28, 86),
    "준비실": (36, 86),
    "탐구 교육 1실": (42, 86),
    "서고": (50, 86),
    "현관": (65, 43),
    "행정실": (64, 58),
    "시청각실": (64, 68),
    "신관 여직원 휴게실": (78, 36),
    "신관 창고": (86, 36),
    "신관 소그룹 1실": (78, 78),
    "신관 AI Lab실": (86, 78),
    "신관 AI 메이커실": (94, 78),
}


# ──────────────────────────────
# 3. 실제 조사 결과
# ──────────────────────────────
# 아직 결과가 준비되지 않았으므로 비워 둠.
# 나중에 이 부분에 실제 결과를 추가하면 됨.
RESULTS = {}

# 나중에 결과를 추가할 때 사용할 형식:
#
# RESULTS["보건실"] = {
#     "sample": "실제 채취 대상",
#     "date": "실제 채취 날짜",
#     "conditions": "채취 방법과 배양 조건",
#     "count": None,
#     "identification": "미동정",
#     "confidence": "미동정",
#     "evidence": "관찰 특징과 동정 근거",
#     "photo": "images/health_room.jpg",
#     "care": "실제 관찰 결과를 바탕으로 작성한 관리 제안",
# }
#
# count: 확인한 집락 수를 숫자로 입력. 미측정은 None.
# confidence: "미동정", "추정", "확인" 중 입력.
# photo: GitHub 저장소에 올린 사진 파일의 경로.


# ──────────────────────────────
# 4. 선택 상태 설정
# ──────────────────────────────
place_names = list(PLACES.keys())

if "selected_place" not in st.session_state:
    st.session_state.selected_place = place_names[0]


def handle_map_selection():
    """지도에서 선택한 장소를 장소 목록에 반영."""
    map_state = st.session_state.get("school_map", {})
    selection = map_state.get("selection", {})
    points = selection.get("points", [])

    if points:
        selected_name = points[-1].get("customdata")

        if selected_name in PLACES:
            st.session_state.selected_place = selected_name


# ──────────────────────────────
# 5. 화면 상단
# ──────────────────────────────
st.title("🧫 우리 학교 위생맵")

st.write(
    "학교 여러 장소에서 얻은 미생물 배양 관찰 결과를 "
    "평면도에서 확인할 수 있는 지도입니다."
)

st.info(
    "현재 지도 준비 단계입니다. "
    "배양 사진과 동정 결과는 확인이 끝난 후 추가할 예정입니다."
)


# ──────────────────────────────
# 6. 지도와 결과 화면
# ──────────────────────────────
map_column, result_column = st.columns(
    [1.7, 1],
    gap="large",
)

with map_column:
    st.subheader("📍 학교 공간 지도")

    st.caption(
        "지도 위 동그란 점을 클릭하세요. "
        "점의 위치는 공간 선택을 위한 것이며, "
        "실제 채취 지점이나 검출량을 뜻하지 않습니다."
    )

    if not MAP_PATH.is_file():
        st.error(
            "평면도 사진을 찾을 수 없습니다. "
            "main.py와 같은 위치에 school_map.png를 올려주세요."
        )

    else:
        encoded_image = base64.b64encode(
            MAP_PATH.read_bytes()
        ).decode("ascii")

        figure = go.Figure()

        # 평면도를 배경 이미지로 추가
        figure.add_layout_image(
            source=f"data:image/png;base64,{encoded_image}",
            xref="x",
            yref="y",
            x=0,
            y=0,
            sizex=100,
            sizey=100,
            sizing="stretch",
            xanchor="left",
            yanchor="top",
            layer="below",
        )

        # 결과 등록 여부에 따른 색상
        marker_colors = [
            "#27825D" if name in RESULTS else "#697D8D"
            for name in place_names
        ]

        # 선택할 수 있는 점 추가
        figure.add_trace(
            go.Scatter(
                x=[
                    PLACES[name][0]
                    for name in place_names
                ],
                y=[
                    PLACES[name][1]
                    for name in place_names
                ],
                customdata=place_names,
                mode="markers",
                marker={
                    "size": 14,
                    "color": marker_colors,
                    "line": {
                        "color": "white",
                        "width": 2,
                    },
                    "opacity": 0.9,
                },
                selected={
                    "marker": {
                        "size": 19,
                        "opacity": 1,
                    }
                },
                unselected={
                    "marker": {
                        "opacity": 0.75,
                    }
                },
                hovertemplate=(
                    "%{customdata}"
                    "<extra></extra>"
                ),
            )
        )

        # 평면도 비율 및 클릭 설정
        figure.update_layout(
            height=590,
            margin={
                "l": 0,
                "r": 0,
                "t": 0,
                "b": 0,
            },
            showlegend=False,
            clickmode="event+select",
            dragmode=False,
            xaxis={
                "range": [0, 100],
                "visible": False,
                "fixedrange": True,
            },
            yaxis={
                "range": [100, 0],
                "visible": False,
                "fixedrange": True,
                "scaleanchor": "x",
                "scaleratio": 560 / 818,
            },
            paper_bgcolor="white",
            plot_bgcolor="white",
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
            key="school_map",
            on_select=handle_map_selection,
            selection_mode="points",
            config={
                "displayModeBar": False,
                "scrollZoom": False,
            },
        )

        st.caption(
            "⚪ 회색 점: 결과 등록 예정　"
            "🟢 초록색 점: 관찰 기록 등록"
        )


with result_column:
    st.subheader("🔎 장소별 관찰 기록")

    selected_place = st.selectbox(
        "확인할 장소",
        options=place_names,
        key="selected_place",
    )

    st.markdown(f"### {selected_place}")

    result = RESULTS.get(selected_place)

    if result is None:
        st.info("결과 등록 예정")

        st.write(
            "배양 사진과 동정 결과가 준비되면 "
            "이곳에 관찰 기록을 추가할 예정입니다."
        )

        st.caption(
            "결과 미등록은 미생물이 검출되지 않았다는 "
            "뜻이 아닙니다."
        )

    else:
        st.write(
            "**채취 대상:**",
            result.get("sample") or "미입력",
        )

        st.write(
            "**채취 날짜:**",
            result.get("date") or "미입력",
        )

        st.write(
            "**조사 조건:**",
            result.get("conditions") or "미입력",
        )

        colony_count = result.get("count")

        st.metric(
            label="관찰한 집락 수",
            value=(
                "미측정"
                if colony_count is None
                else f"{colony_count}개"
            ),
        )

        st.write(
            "**동정 결과:**",
            result.get("identification") or "미동정",
        )

        st.write(
            "**확인 수준:**",
            result.get("confidence") or "미동정",
        )

        st.write(
            "**관찰 근거:**",
            result.get("evidence") or "미입력",
        )

        photo = result.get("photo")

        if photo:
            photo_path = BASE_DIR / photo

            if photo_path.is_file():
                st.image(
                    str(photo_path),
                    caption=(
                        f"{selected_place} 배양 관찰 사진"
                    ),
                    use_container_width=True,
                )
            else:
                st.warning(
                    "등록된 경로에 사진 파일이 없습니다. "
                    "사진 이름과 경로를 확인해주세요."
                )

        st.write(
            "**위생 관리 제안:**",
            result.get("care") or "결과 확인 후 추가 예정",
        )


# ──────────────────────────────
# 7. 제작 목적과 해석 안내
# ──────────────────────────────
st.divider()

purpose_column, guide_column = st.columns(2)

with purpose_column:
    st.subheader("📋 제작 목적")

    st.write(
        "학교 여러 장소에서 얻은 미생물 배양 관찰 결과를 "
        "지도에 연결하여 학교 환경에 대한 관심을 높이고, "
        "생활 속 위생 관리를 실천하도록 돕습니다."
    )

with guide_column:
    st.subheader("💡 결과 해석 안내")

    st.write(
        "같은 채취 방법과 배양 조건에서 얻은 결과끼리 "
        "비교합니다. 집락 수만으로 병원성이나 장소 전체의 "
        "안전성을 판단하지 않으며, 동정 결과의 추정 여부와 "
        "관찰 근거를 함께 표시합니다."
    )
