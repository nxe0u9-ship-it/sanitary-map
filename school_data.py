from pathlib import Path
import base64
import math

from PIL import Image, ImageOps, ImageDraw, ImageChops
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent


# 동정 결과가 나오면 여기에 등록합니다.
# 예를 들어 "1_1"은 1번 플레이트의 1번 구역입니다.
#
# 입력 항목:
# name: 동정 결과명
# scientific_name: 학명
# status: 추정 동정 / 확인 동정 등 확인 수준
# evidence: 동정 근거
# notes: 추가 설명
#
# 아직 실제 결과를 받지 않았으므로 비워둡니다.
IDENTIFICATIONS = {}


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


SHORT_NAMES = [
    "엘리베이터", "창고", "계단", "소그룹 1실",
    "손잡이", "거울", "우산꽂이", "학습도움실",
    "본부교무실", "담 철창살", "벤치", "체육부품실 손잡이",
    "신발장", "분리수거장", "식물",
    "책상", "서고", "싱크대", "히터",
    "수도꼭지", "변기", "세면대", "문 손잡이",
    "내빈용 실내화", "보건실", "행정실", "청소도구함",
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

for sample, short in zip(SAMPLES, SHORT_NAMES):
    place, target, plate, section = sample
    result_id = f"{plate}_{section}"

    RESULTS[result_id] = {
        "place": place,
        "short": short,
        "target": target,
        "plate": plate,
        "section": section,
    }

    GROUPS[place].append(result_id)


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
        return math.atan2(y * sy - cy, x * sx - cx)

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


def display_name(record):
    place = record["place"]
    short = record["short"]

    if place.replace(" ", "") == short.replace(" ", ""):
        return place

    return f"{place} · {short}"


def show_identification(result_id):
    result = IDENTIFICATIONS.get(result_id)

    st.markdown("**동정 결과**")

    if not result:
        st.caption("아직 등록되지 않았습니다.")
        return

    st.write(result.get("name") or "결과명 미입력")

    if result.get("scientific_name"):
        st.write(f"학명: {result['scientific_name']}")

    if result.get("status"):
        st.caption(f"확인 수준: {result['status']}")

    if result.get("evidence"):
        st.caption(f"근거: {result['evidence']}")

    if result.get("notes"):
        st.caption(result["notes"])


def show_result_photo(result_id, framed=False):
    record = RESULTS[result_id]

    try:
        image = get_photo(record["plate"])

        if image is None:
            st.warning("배양 사진 파일을 찾지 못했습니다.")
            return

        cropped = crop_sector(
            image,
            record["plate"],
            record["section"],
        )

        if framed:
            cropped = make_display_photo(cropped)

        st.image(
            cropped,
            use_container_width=True,
        )

    except (OSError, ValueError) as error:
        st.error(f"사진을 표시하지 못했습니다: {error}")


def render_map(state_key, chart_key, chosen_ids=()):
    if st.session_state.get(state_key) not in GROUPS:
        st.session_state[state_key] = None

    path = BASE_DIR / "school_map.png"

    if not path.is_file():
        st.error("학교 지도 사진을 찾지 못했습니다.")
        return

    encoded = base64.b64encode(
        path.read_bytes()
    ).decode("ascii")

    fig = go.Figure()

    fig.add_layout_image(
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
        for item in chosen_ids
        if item in RESULTS
    }

    xs = []
    ys = []
    names = []

    for name, bounds in HIGHLIGHTS.items():
        left, top, right, bottom = bounds

        if name == st.session_state[state_key]:
            color = "rgba(53,199,118,0.35)"
        elif name in chosen_places:
            color = "rgba(255,157,51,0.38)"
        else:
            color = "rgba(255,219,51,0.30)"

        fig.add_shape(
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

    fig.add_trace(
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

    fig.update_layout(
        height=570,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        showlegend=False,
        clickmode="event+select",
        dragmode=False,
        hovermode="closest",
        hoverdistance=8,
        uirevision=chart_key,
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

    # 현재 클릭으로 반환된 선택값을 즉시 처리합니다.
    event = st.plotly_chart(
        fig,
        use_container_width=True,
        key=chart_key,
        on_select="rerun",
        selection_mode="points",
        config={
            "displayModeBar": False,
            "scrollZoom": False,
            "doubleClick": False,
        },
    )

    points = event.get("selection", {}).get("points", [])

    if points:
        name = points[-1].get("customdata")

        if (
            name in GROUPS
            and name != st.session_state[state_key]
        ):
            st.session_state[state_key] = name

            # 추가 클릭 없이 색상과 결과를 함께 갱신합니다.
            st.rerun()


def show_legend(comparison=False):
    items = [
        ("#FFF1A8", "#514000", "관찰 기록이 있는 공간"),
        ("#C8F0D8", "#104D2C", "현재 선택한 공간"),
    ]

    if comparison:
        items.insert(
            1,
            ("#FFD9B0", "#693500", "비교 대상이 담긴 공간"),
        )

    cards = "".join(
        f'<span style="background:{bg};color:{fg};'
        f'padding:11px 14px;border-radius:10px;'
        f'font-size:17px;font-weight:700;">{label}</span>'
        for bg, fg, label in items
    )

    st.markdown(
        '<div style="display:flex;gap:10px;'
        'flex-wrap:wrap;margin:8px 0 16px;">'
        + cards
        + "</div>",
        unsafe_allow_html=True,
    )
