from pathlib import Path
import base64

from PIL import Image, ImageOps
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="우리 학교 위생맵",
    page_icon="🧫",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
MAP_PATH = BASE_DIR / "school_map.png"


# 기록이 있는 공간만 지도에 표시합니다.
# 글씨를 덜 가리도록 공간의 가장자리 쪽으로 조정한 대표 좌표입니다.
PLACES = {
    "운동장": (36, 21),
    "본관 왼쪽 위 계단": (5, 23),
    "본관 오른쪽 위 계단": (67, 20),
    "보건실": (23, 33),
    "보건실 앞 복도": (26, 44),
    "교무 1실": (39, 33),
    "당직실": (48, 33),
    "남자화장실": (67, 30),
    "여자화장실": (67, 80),
    "분리수거장": (3, 58),
    "중앙정원": (34, 65),
    "엘리베이터": (3, 76),
    "학습 도움실": (25, 90),
    "탐구 1실": (40, 90),
    "서고": (48, 90),
    "본관 왼쪽 아래 계단": (5, 94),
    "현관": (68, 44),
    "행정실": (67, 58),
    "신관 소그룹 1실": (76, 82),
}


# 지도 공간 / 채취 대상 / 플레이트 번호 / 구역 번호
# 구역 번호는 글씨 없는 앞면 기준입니다.
# 1: 왼쪽 위, 2: 오른쪽 위, 3: 왼쪽 아래, 4: 오른쪽 아래
#
# 4번 플레이트 3번 구역의 '교무실' 기록은 제외했습니다.
SAMPLES = [
    ("엘리베이터", "엘리베이터", 1, 1),
    ("탐구 1실", "탐구1실 창고", 1, 2),
    ("본관 왼쪽 아래 계단", "계단", 1, 3),
    ("신관 소그룹 1실", "신관", 1, 4),

    ("남자화장실", "남자화장실 손잡이", 2, 1),
    ("현관", "1층 거울", 2, 2),
    ("현관", "우산꽂이", 2, 3),
    ("학습 도움실", "학습도움실", 2, 4),

    ("교무 1실", "1층 본부교무실", 3, 1),
    ("운동장", "담 철창살", 3, 2),
    ("중앙정원", "중앙정원 벤치", 3, 3),
    ("운동장", "운동장 체육부품실 손잡이", 3, 4),

    ("보건실 앞 복도", "보건실쪽 신발장", 4, 1),
    ("분리수거장", "분리수거장", 4, 2),
    ("중앙정원", "중앙정원 식물", 4, 4),

    ("당직실", "당직실 책상", 5, 1),
    ("서고", "서고", 5, 2),
    ("탐구 1실", "탐구1실 싱크대", 5, 3),
    ("본관 오른쪽 위 계단", "남자화장실 옆 히터", 5, 4),

    ("여자화장실", "화장실 수도꼭지", 6, 1),
    ("여자화장실", "변기", 6, 2),
    ("여자화장실", "화장실 세면대", 6, 3),
    ("여자화장실", "화장실 문 손잡이", 6, 4),

    ("현관", "내빈용 실내화", 7, 1),
    ("보건실", "보건실", 7, 2),
    ("행정실", "행정실", 7, 3),
    ("본관 왼쪽 위 계단", "청소도구함", 7, 4),
]


RECORDS = {place: [] for place in PLACES}

for place, target, plate, section in SAMPLES:
    RECORDS[place].append(
        {
            "target": target,
            "plate": plate,
            "section": section,
        }
    )


POSITIONS = {
    1: "왼쪽 위",
    2: "오른쪽 위",
    3: "왼쪽 아래",
    4: "오른쪽 아래",
}

# 앞면 구역 번호 → 뒷면 사진에서의 위치 번호
BACK_SECTIONS = {
    1: 2,
    2: 1,
    3: 4,
    4: 3,
}


# 사진을 네 구역으로 나누는 중심 위치
# 2~7번은 우선 사진의 정중앙을 기준으로 합니다.
PHOTO_CENTERS = {
    1: {
        "front": (0.50, 0.50),
        "back": (0.47, 0.49),
    },
    **{
        plate: {
            "front": (0.50, 0.50),
            "back": (0.50, 0.50),
        }
        for plate in range(2, 8)
    },
}


def find_photo(plate, side):
    """파일 이름과 확장자를 확인해 사진을 찾습니다."""
    stem = f"plate{plate}_{side}"
    extensions = (".jpg", ".jpeg", ".png", ".webp")

    for extension in extensions:
        path = BASE_DIR / f"{stem}{extension}"

        if path.is_file():
            return path

    # 대문자 확장자도 지원합니다.
    for path in BASE_DIR.iterdir():
        if (
            path.is_file()
            and path.stem.lower() == stem
            and path.suffix.lower() in extensions
        ):
            return path

    return None


def crop_section(image, section, center_x, center_y):
    """선택한 구역에 해당하는 사진만 잘라냅니다."""
    width, height = image.size

    split_x = int(width * center_x)
    split_y = int(height * center_y)

    boxes = {
        1: (0, 0, split_x, split_y),
        2: (split_x, 0, width, split_y),
        3: (0, split_y, split_x, height),
        4: (split_x, split_y, width, height),
    }

    return image.crop(boxes[section])


def show_photo(record, side):
    plate = record["plate"]
    section = record["section"]

    path = find_photo(plate, side)

    if path is None:
        st.warning(
            f"plate{plate}_{side} 사진 파일이 없습니다."
        )
        return

    photo_section = (
        BACK_SECTIONS[section]
        if side == "back"
        else section
    )

    try:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(
                source
            ).convert("RGB")

        center_x, center_y = PHOTO_CENTERS[plate][side]

        cropped = crop_section(
            image,
            photo_section,
            center_x,
            center_y,
        )

        side_name = "앞면" if side == "front" else "뒷면"

        st.image(
            cropped,
            use_container_width=True,
            caption=(
                f"{record['target']} · "
                f"{plate}번 플레이트 · "
                f"{section}번 구역 · "
                f"{side_name} {POSITIONS[photo_section]}"
            ),
        )

    except (OSError, ValueError):
        st.error(
            f"{path.name} 사진을 읽지 못했습니다. "
            "이미지 파일을 확인해주세요."
        )


# 기존 코드에서 사용하던 선택 상태와 구분합니다.
if (
    st.session_state.get("active_map_place")
    not in RECORDS
):
    st.session_state.active_map_place = None


def handle_map_selection():
    """지도 클릭만으로 해당 공간의 모든 기록을 표시합니다."""
    state = st.session_state.get(
        "school_map_click",
        {},
    )

    points = state.get(
        "selection",
        {},
    ).get("points", [])

    if not points:
        return

    name = points[-1].get("customdata")

    if name in RECORDS:
        st.session_state.active_map_place = name


st.title("🧫 우리 학교 위생맵")

st.write(
    "지도 위 작은 원을 누르면 그 공간에서 채취한 "
    "모든 대상의 배양 사진과 관찰 기록을 확인할 수 있습니다."
)

st.caption(
    f"7개 플레이트 · {len(SAMPLES)}개 채취 기록 · "
    "미생물 동정 결과는 확인 후 추가"
)


map_column, result_column = st.columns(
    [1.6, 1],
    gap="large",
)


with map_column:
    st.subheader("📍 학교 공간 지도")

    st.caption(
        "기록이 등록된 공간에만 원이 표시됩니다. "
        "원 위에 마우스를 올리면 장소 이름이 나옵니다."
    )

    if not MAP_PATH.is_file():
        st.error(
            "main.py와 같은 위치에 "
            "school_map.png를 올려주세요."
        )

    else:
        encoded_image = base64.b64encode(
            MAP_PATH.read_bytes()
        ).decode("ascii")

        with Image.open(MAP_PATH) as map_image:
            map_width, map_height = map_image.size

        # 실제 기록이 있는 공간만 클릭할 수 있게 표시
        map_names = [
            name
            for name in PLACES
            if RECORDS.get(name)
        ]

        figure = go.Figure()

        figure.add_layout_image(
            source=(
                "data:image/png;base64,"
                f"{encoded_image}"
            ),
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

        figure.add_trace(
            go.Scatter(
                x=[
                    PLACES[name][0]
                    for name in map_names
                ],
                y=[
                    PLACES[name][1]
                    for name in map_names
                ],
                customdata=map_names,
                text=[
                    (
                        f"{name}<br>"
                        f"채취 기록 {len(RECORDS[name])}개"
                        "<br>클릭해서 전체 보기"
                    )
                    for name in map_names
                ],
                mode="markers",
                marker={
                    "size": 11,
                    "symbol": "circle-open",
                    "color": "#087F5B",
                    "line": {
                        "width": 2,
                    },
                },
                selected={
                    "marker": {
                        "size": 14,
                        "color": "#D35400",
                        "opacity": 1,
                    },
                },
                unselected={
                    "marker": {
                        "opacity": 1,
                    },
                },
                hovertemplate=(
                    "%{text}<extra></extra>"
                ),
            )
        )

        figure.update_layout(
            height=650,
            margin={
                "l": 0,
                "r": 0,
                "t": 0,
                "b": 0,
            },
            showlegend=False,
            clickmode="event+select",
            dragmode=False,
            uirevision="school-map",
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
                "scaleratio": (
                    map_height / map_width
                ),
            },
            hoverlabel={
                "bgcolor": "white",
                "font_size": 14,
                "font_color": "#15372B",
            },
            paper_bgcolor="white",
            plot_bgcolor="white",
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
            key="school_map_click",
            on_select=handle_map_selection,
            selection_mode="points",
            config={
                "displayModeBar": False,
                "scrollZoom": False,
                "doubleClick": False,
            },
        )

    st.caption(
        "원은 공간을 선택하기 위한 대표 위치입니다."
    )

    st.caption(
        "1번 플레이트의 ‘계단’ 기록은 "
        "본관 왼쪽 아래 계단에 임시로 연결했습니다."
    )


with result_column:
    st.subheader("🔎 선택한 공간의 전체 기록")

    selected_place = (
        st.session_state.active_map_place
    )

    if selected_place is None:
        st.info(
            "왼쪽 지도에서 확인할 공간의 "
            "작은 원을 눌러주세요."
        )

    else:
        records = RECORDS[selected_place]

        st.markdown(
            f"### 📍 {selected_place}"
        )

        st.success(
            f"이 공간의 채취 기록 "
            f"{len(records)}개를 모두 표시합니다."
        )

        # 추가 선택 없이 모든 채취 기록을 차례대로 표시
        for index, record in enumerate(
            records,
            start=1,
        ):
            st.markdown(
                f"#### {index}. {record['target']}"
            )

            st.caption(
                f"{record['plate']}번 플레이트 · "
                f"{record['section']}번 구역"
            )

            front_tab, back_tab = st.tabs(
                [
                    "앞면 사진",
                    "뒷면 사진",
                ]
            )

            with front_tab:
                show_photo(
                    record,
                    "front",
                )

            with back_tab:
                show_photo(
                    record,
                    "back",
                )

            st.write(
                "**동정 상태:** 미동정"
            )

            st.caption(
                "집락 수: 미계수 · "
                "조사 조건: 확인 후 추가"
            )

            st.divider()

        st.caption(
            "원본 사진을 구역별로 잘라 표시했습니다. "
            "구역 경계에 걸친 집락은 채취 장소를 "
            "명확히 구분하기 어려울 수 있습니다."
        )


st.divider()

with st.expander(
    "전체 채취 기록과 사진 번호 확인"
):
    st.table(
        [
            {
                "플레이트": plate,
                "구역": section,
                "지도 공간": place,
                "채취 대상": target,
                "앞면 위치": POSITIONS[section],
                "뒷면 위치": POSITIONS[
                    BACK_SECTIONS[section]
                ],
            }
            for (
                place,
                target,
                plate,
                section,
            ) in SAMPLES
        ]
    )


st.subheader("💡 결과 해석 안내")

st.write(
    "같은 채취 방법과 배양 조건에서 얻은 결과끼리 "
    "비교합니다. 사진의 색과 모양만으로 미생물의 종을 "
    "확정하거나, 집락 수만으로 장소 전체의 안전성을 "
    "판단하지 않습니다."
)
