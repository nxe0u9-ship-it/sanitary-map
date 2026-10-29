from pathlib import Path
import base64
import math

from PIL import Image, ImageOps, ImageDraw, ImageChops
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="우리 학교 위생맵",
    page_icon="🧫",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
MAP_PATH = BASE_DIR / "school_map.png"


# 관찰 기록이 있는 공간만 표시합니다.
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


# 지도 공간, 채취 대상, 플레이트 번호, 앞면 구역 번호
# 구역 번호: 왼쪽 위 1, 오른쪽 위 2,
#            왼쪽 아래 3, 오른쪽 아래 4
# 4번 플레이트 3번 구역의 교무실 기록은 제외했습니다.
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


RECORDS = {name: [] for name in PLACES}

for place, target, plate, section in SAMPLES:
    RECORDS[place].append({
        "target": target,
        "plate": plate,
        "section": section,
    })


# 원본 사진을 확인하기 전의 기본값입니다.
# 중심 위치: 사진 너비·높이에 대한 백분율
# 반지름: 사진의 짧은 변에 대한 백분율
# 구역선 교점: 배지 중심에서 벗어난 정도
DEFAULT_CROP = {
    "cx": 50.0,
    "cy": 50.0,
    "rx": 46.0,
    "ry": 46.0,
    "split_x": 0.0,
    "split_y": 0.0,
    "angle": 0.0,
}

if "plate_crop_settings" not in st.session_state:
    st.session_state.plate_crop_settings = {
        plate: DEFAULT_CROP.copy()
        for plate in range(1, 8)
    }

if st.session_state.get("active_map_place") not in RECORDS:
    st.session_state.active_map_place = None


def find_photo(plate):
    """앞면 사진만 찾습니다."""
    stem = f"plate{plate}_front"
    extensions = {".jpg", ".jpeg", ".png", ".webp"}

    for path in BASE_DIR.iterdir():
        if (
            path.is_file()
            and path.stem.lower() == stem
            and path.suffix.lower() in extensions
        ):
            return path

    return None


@st.cache_data(show_spinner=False)
def load_photo(path_string, modified_time):
    with Image.open(path_string) as source:
        image = ImageOps.exif_transpose(source).convert("RGBA")

    image.thumbnail((1800, 1800))
    return image


def get_photo(plate):
    path = find_photo(plate)

    if path is None:
        return None

    return load_photo(
        str(path),
        path.stat().st_mtime_ns,
    )


def crop_sector(image, section, settings):
    """둥근 배지 안에서 선택한 구역만 남깁니다."""
    width, height = image.size
    short_side = min(width, height)

    cx = width * settings["cx"] / 100
    cy = height * settings["cy"] / 100

    rx = short_side * settings["rx"] / 100
    ry = short_side * settings["ry"] / 100

    split_x = cx + short_side * settings["split_x"] / 100
    split_y = cy + short_side * settings["split_y"] / 100

    # 배지 바깥을 투명하게 만드는 마스크
    dish_mask = Image.new("L", image.size, 0)
    dish_draw = ImageDraw.Draw(dish_mask)

    dish_draw.ellipse(
        (cx - rx, cy - ry, cx + rx, cy + ry),
        fill=255,
    )

    # 화면 좌표에서는 아래쪽이 양의 y 방향입니다.
    angle_ranges = {
        1: (180, 270),
        2: (270, 360),
        3: (90, 180),
        4: (0, 90),
    }

    start, end = angle_ranges[section]
    rotation = settings["angle"]
    reach = math.hypot(width, height) * 4

    points = [(split_x, split_y)]

    for step in range(61):
        degrees = (
            start
            + (end - start) * step / 60
            + rotation
        )

        radians = math.radians(degrees)

        points.append((
            split_x + reach * math.cos(radians),
            split_y + reach * math.sin(radians),
        ))

    sector_mask = Image.new("L", image.size, 0)

    ImageDraw.Draw(sector_mask).polygon(
        points,
        fill=255,
    )

    # 배지 내부와 선택한 구역이 겹치는 부분만 유지
    mask = ImageChops.multiply(
        dish_mask,
        sector_mask,
    )

    mask = ImageChops.multiply(
        mask,
        image.getchannel("A"),
    )

    bounds = mask.getbbox()

    if bounds is None:
        raise ValueError(
            "사진과 겹치는 영역이 없습니다. "
            "사진 자르기 조정값을 확인해주세요."
        )

    result = image.copy()
    result.putalpha(mask)

    return result.crop(bounds)


def handle_map_selection():
    state = st.session_state.get(
        "school_map_click",
        {},
    )

    points = state.get(
        "selection",
        {},
    ).get("points", [])

    if points:
        name = points[-1].get("customdata")

        if name in RECORDS:
            st.session_state.active_map_place = name


st.title("🧫 우리 학교 위생맵")

st.write(
    "지도 위 작은 원을 누르면 그 공간의 모든 채취 기록과 "
    "앞면 배양 사진을 확인할 수 있습니다."
)

st.caption(
    f"7개 플레이트 · {len(SAMPLES)}개 채취 기록 · "
    "동정 결과는 확인 후 추가"
)


with st.expander(
    "사진 자르기 조정 · 배지 경계와 구역선 맞추기",
    expanded=False,
):
    st.caption(
        "배지가 잘리거나 바닥이 보일 때 조정해주세요. "
        "조정값은 현재 접속 세션 동안 유지됩니다."
    )

    edit_plate = st.selectbox(
        "조정할 플레이트",
        options=list(range(1, 8)),
        format_func=lambda number: f"{number}번 플레이트",
    )

    settings = (
        st.session_state.plate_crop_settings[edit_plate]
    )

    controls = [
        ("cx", "배지 중심 좌우", 0.0, 100.0),
        ("cy", "배지 중심 위아래", 0.0, 100.0),
        ("rx", "배지 가로 반지름", 5.0, 100.0),
        ("ry", "배지 세로 반지름", 5.0, 100.0),
        (
            "split_x",
            "구역선 교점 좌우 이동",
            -40.0,
            40.0,
        ),
        (
            "split_y",
            "구역선 교점 위아래 이동",
            -40.0,
            40.0,
        ),
        ("angle", "구역선 회전 각도", -45.0, 45.0),
    ]

    control_column, preview_column = st.columns(2)

    with control_column:
        for field, label, minimum, maximum in controls:
            settings[field] = st.slider(
                label,
                min_value=minimum,
                max_value=maximum,
                value=float(settings[field]),
                step=0.5,
                key=f"crop_{edit_plate}_{field}",
            )

    with preview_column:
        try:
            original = get_photo(edit_plate)

            if original is None:
                st.warning(
                    f"plate{edit_plate}_front "
                    "사진이 없습니다."
                )

            else:
                preview = original.convert("RGB")
                width, height = preview.size
                short_side = min(width, height)

                cx = width * settings["cx"] / 100
                cy = height * settings["cy"] / 100

                rx = short_side * settings["rx"] / 100
                ry = short_side * settings["ry"] / 100

                split_x = (
                    cx
                    + short_side
                    * settings["split_x"]
                    / 100
                )

                split_y = (
                    cy
                    + short_side
                    * settings["split_y"]
                    / 100
                )

                draw = ImageDraw.Draw(preview)

                line_width = max(
                    2,
                    round(short_side / 250),
                )

                draw.ellipse(
                    (
                        cx - rx,
                        cy - ry,
                        cx + rx,
                        cy + ry,
                    ),
                    outline="#00DD77",
                    width=line_width,
                )

                reach = math.hypot(width, height) * 2

                for degrees in (0, 90, 180, 270):
                    radians = math.radians(
                        degrees + settings["angle"]
                    )

                    draw.line(
                        [
                            (split_x, split_y),
                            (
                                split_x
                                + reach * math.cos(radians),
                                split_y
                                + reach * math.sin(radians),
                            ),
                        ],
                        fill="#FF6600",
                        width=line_width,
                    )

                st.image(
                    preview,
                    caption=(
                        "초록색: 배지 경계 / "
                        "주황색: 구역선"
                    ),
                    use_container_width=True,
                )

                st.caption(
                    "초록색은 배지 안쪽 테두리에, "
                    "주황색은 사진에 비치는 구역선에 "
                    "맞춰주세요."
                )

        except (OSError, ValueError):
            st.error(
                "미리보기 사진을 읽지 못했습니다."
            )


map_column, result_column = st.columns(
    [1.6, 1],
    gap="large",
)


with map_column:
    st.subheader("📍 학교 공간 지도")

    st.caption(
        "작은 원을 클릭하세요. "
        "마우스를 올리면 장소가 표시됩니다."
    )

    if not MAP_PATH.is_file():
        st.error(
            "main.py와 같은 위치에 "
            "school_map.png를 올려주세요."
        )

    else:
        encoded = base64.b64encode(
            MAP_PATH.read_bytes()
        ).decode("ascii")

        with Image.open(MAP_PATH) as source:
            map_width, map_height = source.size

        names = [
            name
            for name in PLACES
            if RECORDS.get(name)
        ]

        figure = go.Figure()

        figure.add_layout_image(
            source=f"data:image/png;base64,{encoded}",
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
                    for name in names
                ],
                y=[
                    PLACES[name][1]
                    for name in names
                ],
                customdata=names,
                text=[
                    (
                        f"{name}<br>"
                        f"채취 기록 "
                        f"{len(RECORDS[name])}개"
                    )
                    for name in names
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
        "원은 공간 선택용 대표 위치입니다. "
        "‘계단’ 기록은 본관 왼쪽 아래 계단에 "
        "임시 연결했습니다."
    )


with result_column:
    st.subheader("🔎 선택한 공간의 전체 기록")

    selected_place = (
        st.session_state.active_map_place
    )

    if selected_place is None:
        st.info(
            "왼쪽 지도에서 확인할 공간의 "
            "원을 눌러주세요."
        )

    else:
        records = RECORDS[selected_place]

        st.markdown(
            f"### 📍 {selected_place}"
        )

        st.write(
            f"**채취 기록 {len(records)}개**"
        )

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

            try:
                image = get_photo(
                    record["plate"]
                )

                if image is None:
                    st.warning(
                        f"plate{record['plate']}_front "
                        "사진이 없습니다."
                    )

                else:
                    settings = (
                        st.session_state
                        .plate_crop_settings[
                            record["plate"]
                        ]
                    )

                    cropped = crop_sector(
                        image,
                        record["section"],
                        settings,
                    )

                    st.image(
                        cropped,
                        caption=record["target"],
                        use_container_width=True,
                    )

            except (OSError, ValueError) as error:
                st.error(
                    f"사진을 표시하지 못했습니다: {error}"
                )

            st.write(
                "**동정 상태:** 미동정"
            )

            st.caption(
                "집락 수: 미계수 · "
                "조사 조건: 확인 후 추가"
            )

            st.divider()


st.divider()

with st.expander("전체 채취 기록 확인"):
    st.table(
        [
            {
                "플레이트": plate,
                "구역": section,
                "지도 공간": place,
                "채취 대상": target,
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
