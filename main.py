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


# 장소 이름에 형광펜을 표시할 영역
# 평면도 원본 818 × 560 기준
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


# 지도 공간, 채취 대상, 플레이트 번호, 앞면 구역 번호
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


RECORDS = {name: [] for name in HIGHLIGHTS}

for place, target, plate, section in SAMPLES:
    RECORDS[place].append({
        "target": target,
        "plate": plate,
        "section": section,
    })


# 사진별 배지 경계와 구역선 방향
# 1600 × 1600으로 환산한 기준
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


if st.session_state.get("active_map_place") not in RECORDS:
    st.session_state.active_map_place = None


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


def handle_map_selection():
    state = st.session_state.get("school_map_click", {})
    points = state.get("selection", {}).get("points", [])

    if points:
        name = points[-1].get("customdata")

        if name in RECORDS:
            st.session_state.active_map_place = name


st.title("🧫 우리 학교 위생맵")

st.write(
    "지도에서 형광펜으로 표시된 장소 이름을 누르면 "
    "해당 공간의 모든 배양 관찰 기록을 확인할 수 있습니다."
)


map_column, result_column = st.columns(
    [1.6, 1],
    gap="large",
)


with map_column:
    st.subheader("📍 학교 공간 지도")

    # 색상 안내를 큰 글씨와 색상 배경으로 표시합니다.
    st.markdown(
        """
        <div style="
            display:flex;
            gap:12px;
            flex-wrap:wrap;
            margin:8px 0 18px;
        ">
            <div style="
                background:#FFF1A8;
                color:#514000;
                border:2px solid #E8BD23;
                border-radius:12px;
                padding:12px 16px;
                font-size:18px;
                font-weight:700;
            ">
                🟨 관찰 기록이 있는 공간
            </div>
            <div style="
                background:#C8F0D8;
                color:#104D2C;
                border:2px solid #43A66B;
                border-radius:12px;
                padding:12px 16px;
                font-size:18px;
                font-weight:700;
            ">
                🟩 선택한 공간
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not MAP_PATH.is_file():
        st.error(
            "main.py와 같은 위치에 school_map.png를 올려주세요."
        )

    else:
        encoded = base64.b64encode(
            MAP_PATH.read_bytes()
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

        click_x = []
        click_y = []
        click_names = []
        click_text = []

        active_place = st.session_state.active_map_place

        for name, bounds in HIGHLIGHTS.items():
            if not RECORDS.get(name):
                continue

            left, top, right, bottom = bounds

            if name == active_place:
                color = "rgba(53, 199, 118, 0.30)"
            else:
                color = "rgba(255, 219, 51, 0.30)"

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

            # 형광펜 영역 전체에 투명한 클릭 지점을 배치
            for x in range(left, right + 1, 4):
                for y in range(top, bottom + 1, 4):
                    click_x.append(x)
                    click_y.append(y)
                    click_names.append(name)
                    click_text.append(
                        f"{name}<br>"
                        f"채취 기록 {len(RECORDS[name])}개"
                    )

        figure.add_trace(
            go.Scatter(
                x=click_x,
                y=click_y,
                customdata=click_names,
                text=click_text,
                mode="markers",
                marker={
                    "size": 6,
                    "symbol": "square",
                    "color": "rgba(0, 0, 0, 0.001)",
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
            height=620,
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
            showlegend=False,
            clickmode="event+select",
            dragmode=False,
            uirevision="highlight-map",
            hovermode="closest",
            hoverdistance=8,
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
            hoverlabel={
                "bgcolor": "white",
                "font_color": "#15372B",
            },
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
        "‘계단’ 기록은 본관 왼쪽 아래 계단에 "
        "임시 연결했습니다."
    )


with result_column:
    st.subheader("🔎 선택한 공간의 전체 기록")

    selected_place = st.session_state.active_map_place

    if selected_place is None:
        st.info(
            "왼쪽 지도에서 형광펜으로 표시된 "
            "장소 이름을 눌러주세요."
        )

    else:
        records = RECORDS[selected_place]

        st.markdown(f"### 📍 {selected_place}")
        st.write(f"**채취 기록 {len(records)}개**")

        for index, record in enumerate(records, start=1):
            st.markdown(
                f"#### {index}. {record['target']}"
            )

            st.caption(
                f"{record['plate']}번 플레이트 · "
                f"{record['section']}번 구역"
            )

            try:
                image = get_photo(record["plate"])

                if image is None:
                    st.warning(
                        f"plate{record['plate']}_front "
                        "사진이 없습니다."
                    )

                else:
                    cropped = crop_sector(
                        image,
                        record["plate"],
                        record["section"],
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

            st.write("**동정 상태:** 미동정")
            st.caption(
                "집락 수: 미계수 · 조사 조건: 확인 후 추가"
            )
            st.divider()


st.divider()

with st.expander("전체 채취 기록 확인"):
    st.table([
        {
            "플레이트": plate,
            "구역": section,
            "지도 공간": place,
            "채취 대상": target,
        }
        for place, target, plate, section in SAMPLES
    ])

st.caption(
    "사진의 보이는 구역선에 맞춰 잘랐으며, "
    "집락에 가려진 경계는 연장 방향을 추정했습니다."
)

st.subheader("💡 결과 해석 안내")

st.write(
    "같은 채취 방법과 배양 조건에서 얻은 결과끼리 비교합니다. "
    "사진의 색과 모양만으로 미생물의 종을 확정하거나, "
    "집락 수만으로 장소 전체의 안전성을 판단하지 않습니다."
)
