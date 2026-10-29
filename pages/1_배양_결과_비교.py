from pathlib import Path
import base64
import math

from PIL import Image, ImageOps, ImageDraw, ImageChops
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="배양 결과 비교 | 우리 학교 위생맵",
    page_icon="🧫",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parents[1]


# 장소 이름에 형광펜을 표시할 영역
HIGHLIGHTS = {
    "운동장": (240, 71, 350, 101),
    "본관 왼쪽 위 계단": (53, 111, 104, 141),
    "본관 오른쪽 위 계단": (481, 111, 535, 141),
    "보건실": (182, 181, 244, 213),
    "보건실 앞 복도": (237, 130, 322, 155),
    "교무 1실": (322, 171, 369, 228),
    "당직실": (381, 181, 440, 213),
    "남자화장실": (489, 158, 560, 184),
    "여자화장실": (489, 438, 560, 465),
    "분리수거장": (21, 301, 77, 348),
    "중앙정원": (207, 307, 354, 341),
    "엘리베이터": (29, 411, 68, 434),
    "학습 도움실": (193, 446, 269, 509),
    "탐구 1실": (317, 438, 374, 520),
    "서고": (386, 461, 437, 496),
    "본관 왼쪽 아래 계단": (54, 507, 104, 538),
    "현관": (527, 208, 559, 272),
    "행정실": (489, 308, 561, 340),
    "신관 소그룹 1실": (612, 408, 670, 471),
}


# 공간, 화면에 표시할 짧은 이름, 사진 번호, 구역 번호
SAMPLES = [
    ("엘리베이터", "엘리베이터", 1, 1),
    ("탐구 1실", "창고", 1, 2),
    ("본관 왼쪽 아래 계단", "계단", 1, 3),
    ("신관 소그룹 1실", "소그룹 1실", 1, 4),

    ("남자화장실", "손잡이", 2, 1),
    ("현관", "거울", 2, 2),
    ("현관", "우산꽂이", 2, 3),
    ("학습 도움실", "학습도움실", 2, 4),

    ("교무 1실", "본부교무실", 3, 1),
    ("운동장", "담 철창살", 3, 2),
    ("중앙정원", "벤치", 3, 3),
    ("운동장", "체육부품실 손잡이", 3, 4),

    ("보건실 앞 복도", "신발장", 4, 1),
    ("분리수거장", "분리수거장", 4, 2),
    ("중앙정원", "식물", 4, 4),

    ("당직실", "책상", 5, 1),
    ("서고", "서고", 5, 2),
    ("탐구 1실", "싱크대", 5, 3),
    ("본관 오른쪽 위 계단", "히터", 5, 4),

    ("여자화장실", "수도꼭지", 6, 1),
    ("여자화장실", "변기", 6, 2),
    ("여자화장실", "세면대", 6, 3),
    ("여자화장실", "문 손잡이", 6, 4),

    ("현관", "내빈용 실내화", 7, 1),
    ("보건실", "보건실", 7, 2),
    ("행정실", "행정실", 7, 3),
    ("본관 왼쪽 위 계단", "청소도구함", 7, 4),
]


PHOTO_BOUNDS = {
    1: (
        (270, 300, 1370, 1390),
        (780, 850),
        ((720, 330), (1320, 900), (980, 1380), (310, 810)),
    ),
    2: (
        (170, 285, 1330, 1420),
        (768, 870),
        ((780, 300), (1320, 885), (730, 1410), (180, 970)),
    ),
    3: (
        (300, 280, 1400, 1400),
        (850, 750),
        ((700, 280), (1390, 740), (980, 1390), (300, 760)),
    ),
    4: (
        (280, 175, 1385, 1320),
        (900, 770),
        ((900, 180), (1380, 785), (830, 1320), (290, 760)),
    ),
    5: (
        (160, 170, 1430, 1375),
        (880, 800),
        ((870, 175), (1430, 825), (820, 1370), (170, 750)),
    ),
    6: (
        (260, 290, 1400, 1400),
        (790, 810),
        ((800, 300), (1390, 740), (800, 1390), (270, 835)),
    ),
    7: (
        (210, 185, 1420, 1430),
        (835, 820),
        ((780, 195), (1410, 780), (840, 1420), (220, 890)),
    ),
}


RESULTS = {}
GROUPS = {name: [] for name in HIGHLIGHTS}

for place, short, plate, section in SAMPLES:
    result_id = f"{plate}_{section}"

    RESULTS[result_id] = {
        "place": place,
        "short": short,
        "plate": plate,
        "section": section,
    }

    GROUPS[place].append(result_id)


if "compare_ids" not in st.session_state:
    st.session_state.compare_ids = []

if st.session_state.get("compare_place") not in GROUPS:
    st.session_state.compare_place = None


def find_photo(plate):
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


def crop_sector(image, plate, section):
    width, height = image.size
    bounds, center, directions = PHOTO_BOUNDS[plate]

    sx = width / 1600
    sy = height / 1600
    cx = center[0] * sx
    cy = center[1] * sy

    dish_mask = Image.new("L", image.size, 0)

    ImageDraw.Draw(dish_mask).ellipse(
        (
            bounds[0] * sx,
            bounds[1] * sy,
            bounds[2] * sx,
            bounds[3] * sy,
        ),
        fill=255,
    )

    ray_pairs = {
        1: (3, 0),
        2: (0, 1),
        3: (2, 3),
        4: (1, 2),
    }

    first, last = ray_pairs[section]

    def direction_angle(index):
        x, y = directions[index]
        return math.atan2(
            y * sy - cy,
            x * sx - cx,
        )

    start = direction_angle(first)
    end = direction_angle(last)

    while end <= start:
        end += 2 * math.pi

    reach = math.hypot(width, height) * 4
    points = [(cx, cy)]

    for step in range(91):
        angle = start + (end - start) * step / 90
        points.append((
            cx + reach * math.cos(angle),
            cy + reach * math.sin(angle),
        ))

    sector_mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(sector_mask).polygon(points, fill=255)

    mask = ImageChops.multiply(dish_mask, sector_mask)
    mask = ImageChops.multiply(mask, image.getchannel("A"))

    box = mask.getbbox()

    if box is None:
        raise ValueError("사진 자르기 영역을 확인해주세요.")

    result = image.copy()
    result.putalpha(mask)

    return result.crop(box)


def make_display_photo(image):
    fitted = ImageOps.contain(image, (560, 560))
    canvas = Image.new("RGBA", (600, 600), (0, 0, 0, 0))

    canvas.alpha_composite(
        fitted,
        (
            (600 - fitted.width) // 2,
            (600 - fitted.height) // 2,
        ),
    )

    return canvas


def checkbox_key(result_id):
    return f"compare_check_{result_id}"


def toggle_result(result_id):
    selected = list(st.session_state.compare_ids)
    checked = st.session_state.get(
        checkbox_key(result_id),
        False,
    )

    if checked and result_id not in selected:
        selected.append(result_id)

    elif not checked and result_id in selected:
        selected.remove(result_id)

    st.session_state.compare_ids = selected


def remove_result(result_id):
    st.session_state.compare_ids = [
        item
        for item in st.session_state.compare_ids
        if item != result_id
    ]

    st.session_state[checkbox_key(result_id)] = False


def clear_results():
    st.session_state.compare_ids = []

    for result_id in RESULTS:
        st.session_state[checkbox_key(result_id)] = False


def select_place_results(place):
    selected = list(st.session_state.compare_ids)

    for result_id in GROUPS[place]:
        if result_id not in selected:
            selected.append(result_id)

        st.session_state[checkbox_key(result_id)] = True

    st.session_state.compare_ids = selected


def handle_compare_map():
    state = st.session_state.get("comparison_map", {})
    points = state.get("selection", {}).get("points", [])

    if points:
        name = points[-1].get("customdata")

        if name in GROUPS:
            st.session_state.compare_place = name


def display_name(record):
    place = record["place"]
    short = record["short"]

    if place.replace(" ", "") == short.replace(" ", ""):
        return place

    return f"{place} · {short}"


st.title("🧫 배양 결과 비교")

st.write(
    "지도에서 장소를 누른 뒤 비교할 대상을 체크하세요. "
    "다른 장소로 이동해도 선택은 유지됩니다."
)


map_column, selection_column = st.columns(
    [1.6, 1],
    gap="large",
)


with map_column:
    st.subheader("📍 장소 선택")

    st.markdown(
        """
        <div style="
            display:flex;
            gap:8px;
            flex-wrap:wrap;
            margin-bottom:12px;
            font-size:16px;
            font-weight:700;
        ">
            <span style="
                background:#FFF1A8;
                color:#514000;
                padding:9px 12px;
                border-radius:9px;
            ">
                노란색 · 선택 가능한 공간
            </span>
            <span style="
                background:#FFD9B0;
                color:#693500;
                padding:9px 12px;
                border-radius:9px;
            ">
                주황색 · 비교 대상이 담긴 공간
            </span>
            <span style="
                background:#C8F0D8;
                color:#104D2C;
                padding:9px 12px;
                border-radius:9px;
            ">
                초록색 · 현재 보고 있는 공간
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    map_path = BASE_DIR / "school_map.png"

    if not map_path.is_file():
        st.error("학교 지도 사진을 찾지 못했습니다.")

    else:
        encoded = base64.b64encode(
            map_path.read_bytes()
        ).decode("ascii")

        figure = go.Figure()

        figure.add_layout_image(
            source=f"data:image/png;base64,{encoded}",
            xref="x",
            yref="y",
            x=0,
            y=0,
            sizex=818,
            sizey=560,
            sizing="stretch",
            xanchor="left",
            yanchor="top",
            layer="below",
        )

        chosen_places = {
            RESULTS[item]["place"]
            for item in st.session_state.compare_ids
        }

        xs = []
        ys = []
        names = []

        for name, bounds in HIGHLIGHTS.items():
            left, top, right, bottom = bounds

            if name == st.session_state.compare_place:
                color = "rgba(53,199,118,0.35)"
            elif name in chosen_places:
                color = "rgba(255,157,51,0.38)"
            else:
                color = "rgba(255,219,51,0.30)"

            figure.add_shape(
                type="rect",
                x0=left,
                y0=top,
                x1=right,
                y1=bottom,
                fillcolor=color,
                line={"width": 0},
                layer="above",
            )

            for x in range(left, right + 1, 4):
                for y in range(top, bottom + 1, 4):
                    xs.append(x)
                    ys.append(y)
                    names.append(name)

        figure.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                customdata=names,
                text=names,
                mode="markers",
                marker={
                    "size": 6,
                    "symbol": "square",
                    "color": "rgba(0,0,0,0.001)",
                },
                selected={
                    "marker": {"opacity": 1},
                },
                unselected={
                    "marker": {"opacity": 1},
                },
                hovertemplate="%{text}<extra></extra>",
            )
        )

        figure.update_layout(
            height=570,
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
            showlegend=False,
            clickmode="event+select",
            dragmode=False,
            hovermode="closest",
            hoverdistance=8,
            uirevision="compare-map",
            xaxis={
                "range": [0, 818],
                "visible": False,
                "fixedrange": True,
            },
            yaxis={
                "range": [560, 0],
                "visible": False,
                "fixedrange": True,
                "scaleanchor": "x",
                "scaleratio": 1,
            },
            paper_bgcolor="white",
            plot_bgcolor="white",
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
            key="comparison_map",
            on_select=handle_compare_map,
            selection_mode="points",
            config={
                "displayModeBar": False,
                "scrollZoom": False,
                "doubleClick": False,
            },
        )


with selection_column:
    st.subheader("☑️ 비교할 대상 고르기")

    place = st.session_state.compare_place

    if place is None:
        st.info("왼쪽 지도에서 장소 이름을 눌러주세요.")

    else:
        st.markdown(f"### {place}")

        for result_id in GROUPS[place]:
            key = checkbox_key(result_id)

            if key not in st.session_state:
                st.session_state[key] = (
                    result_id in st.session_state.compare_ids
                )

            st.checkbox(
                RESULTS[result_id]["short"],
                key=key,
                on_change=toggle_result,
                args=(result_id,),
            )

        if len(GROUPS[place]) > 1:
            st.button(
                "이 장소 모두 선택",
                key="select_place_all",
                on_click=select_place_results,
                args=(place,),
            )

        st.caption(
            "체크한 대상은 아래 비교 영역에 바로 추가됩니다."
        )


st.divider()
st.subheader("🔬 선택한 배양 결과")

selected = list(st.session_state.compare_ids)

if not selected:
    st.info(
        "지도에서 장소를 고른 뒤 원하는 대상을 체크해주세요."
    )

else:
    count_column, reset_column = st.columns([3, 1])

    count_column.write(
        f"**총 {len(selected)}개 선택**"
    )

    reset_column.button(
        "선택 초기화",
        on_click=clear_results,
        use_container_width=True,
    )

    column_count = min(3, len(selected))

    for start in range(0, len(selected), column_count):
        columns = st.columns(
            column_count,
            gap="large",
        )

        row = selected[start:start + column_count]

        for column, result_id in zip(columns, row):
            record = RESULTS[result_id]

            with column:
                st.markdown(
                    f"#### {display_name(record)}"
                )

                try:
                    image = get_photo(record["plate"])

                    if image is None:
                        st.warning(
                            "배양 사진 파일을 찾지 못했습니다."
                        )

                    else:
                        cropped = crop_sector(
                            image,
                            record["plate"],
                            record["section"],
                        )

                        st.image(
                            make_display_photo(cropped),
                            use_container_width=True,
                        )

                except (OSError, ValueError) as error:
                    st.error(
                        f"사진을 표시하지 못했습니다: {error}"
                    )

                st.button(
                    "비교에서 빼기",
                    key=f"remove_{result_id}",
                    on_click=remove_result,
                    args=(result_id,),
                    use_container_width=True,
                )

        st.divider()


st.caption(
    "사진은 보기 편하도록 표시 크기를 맞췄습니다. "
    "실제 집락 크기를 재는 척도로 사용할 수 없습니다. "
    "집락에 가려진 구역선은 보이는 부분의 연장 방향으로 "
    "추정했습니다."
)

st.info(
    "집락의 색·모양·표면·퍼진 정도를 비교해보세요. "
    "사진만으로 미생물의 종이나 병원성을 확정할 수 없으며, "
    "장소별 차이를 해석하려면 채취 방법과 배양 조건도 "
    "확인해야 합니다."
)
