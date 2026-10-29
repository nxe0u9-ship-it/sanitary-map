from pathlib import Path
import base64
import math

from PIL import Image, ImageOps, ImageDraw, ImageChops
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent


# 각 행: 구분, 관찰 특징, 학명, 미생물의 일반 특징
IDENTIFICATIONS = {
    "1_1": [
        ("A", "검은색의 굵고 둥근 집락", "Aspergillus niger", "검은 포자층을 만들 수 있는 곰팡이"),
        ("B", "자주빛이 섞인 흑갈색 원형 집락", "Cladosporium cladosporioides", "올리브색·암갈색의 벨벳형 집락을 만들 수 있음"),
        ("C", "주변의 옅은 회백색 솜털", "Mucor circinelloides", "빠르게 퍼지는 흰색·회색 균사 형태"),
    ],
    "1_2": [
        ("A", "어두운 회흑색의 불규칙한 덩어리", "Cladosporium cladosporioides", "짙은 올리브색·갈색의 분말형 표면"),
        ("B", "부분적으로 솟은 흰 솜털", "Mucor circinelloides", "공중으로 자라는 솜털 모양 균사"),
        ("C", "작고 짙은 원형 부분", "Aspergillus niger", "성숙할수록 검게 보이는 포자층"),
    ],
    "1_3": [
        ("A", "청록색·회녹색의 작은 둥근 집락", "Penicillium rubens", "청록색 계열의 포자 형성"),
        ("B", "검은 올리브색의 둥근 집락", "Cladosporium cladosporioides", "짙고 벨벳 같은 집락"),
        ("C", "흰색·연분홍빛의 작은 솜털", "Fusarium oxysporum", "일부 조건에서 분홍빛을 띠는 균사"),
    ],
    "1_4": [
        ("A", "넓고 흰색인 구름·솜털 모양", "Mucor circinelloides", "솜털형 균사가 넓게 퍼질 수 있음"),
        ("B", "작고 어두운 회흑색 원형", "Aspergillus niger", "검은 포자층과 원형 성장 모습"),
        ("C", "외곽의 회색·올리브색 고리", "Cladosporium cladosporioides", "올리브색·갈색의 어두운 표면"),
    ],
    "2_1": [
        ("A", "넓게 덮인 회백색 솜털", "Mucor circinelloides", "회백색으로 퍼지는 빠른 균사 성장"),
        ("B", "솜털 속 검은 점과 짙은 둥근 부분", "Rhizopus stolonifer", "검게 보이는 포자낭을 만들 수 있음"),
    ],
    "2_2": [
        ("A", "회갈색의 넓고 흐릿한 솜털", "Alternaria alternata", "갈색·회색·검정 계열의 포자층"),
        ("B", "독립된 검은 둥근 집락", "Aspergillus niger", "검은 포자를 빽빽하게 형성할 수 있음"),
        ("C", "작은 회흑색 점들이 모인 부분", "Cladosporium cladosporioides", "짙은 색의 촘촘한 균총"),
    ],
    "2_3": [
        ("A", "빽빽한 어두운 올리브색 원형들", "Cladosporium cladosporioides", "올리브색·흑갈색의 벨벳형 표면"),
        ("B", "가느다란 흰색 솜털 덩어리", "Mucor circinelloides", "희고 부드러운 균사 성장"),
        ("C", "회갈색의 옅은 번짐", "Alternaria alternata", "어두운 갈색의 확산성 집락"),
    ],
    "2_4": [
        ("A", "넓게 퍼진 회색 솜털층", "Rhizopus stolonifer", "균사가 넓게 퍼진 뒤 어두워질 수 있음"),
        ("B", "검고 둥근 조밀한 부분", "Aspergillus niger", "검은색 포자가 밀집한 외형"),
        ("C", "군데군데 작은 흰 솜털", "Mucor circinelloides", "밝은색의 푹신한 균사 형태"),
    ],
    "3_1": [
        ("A", "매우 크게 뭉친 짙은 검은색 집락", "Aspergillus niger", "검게 성숙하는 포자층"),
        ("B", "경계에 섞인 회백색 솜털", "Mucor circinelloides", "흰색·회색의 성긴 솜털형 균사"),
    ],
    "3_2": [
        ("A", "진한 올리브·회녹색 원형", "Cladosporium cladosporioides", "올리브색의 둥글고 벨벳 같은 외형"),
        ("B", "흑색 중심이 있는 작은 원형", "Aspergillus niger", "짙은 색의 포자층"),
        ("C", "그 사이 흰색 솜털 부분", "Mucor circinelloides", "희게 퍼지는 솜털 모양 균사"),
    ],
    "3_3": [
        ("A", "큰 흰색 솜털형 덩어리", "Mucor circinelloides", "넓게 퍼지는 백색 균사"),
        ("B", "약한 분홍빛·연보랏빛의 작은 부분", "Fusarium oxysporum", "일부 배지에서 분홍색 색소를 나타냄"),
        ("C", "회흑색의 작은 둥근 집락", "Cladosporium cladosporioides", "어두운 벨벳형 곰팡이 집락"),
    ],
    "3_4": [
        ("A", "넓은 회백색 솜털형 층", "Rhizopus stolonifer", "흰 균사와 어두운 포자낭을 형성"),
        ("B", "따로 보이는 검은 원형", "Aspergillus niger", "검은 분말형 포자층"),
        ("C", "붉은빛·연갈색 고리 모양", "Fusarium oxysporum", "조건에 따라 연분홍색 색소를 형성"),
    ],
    "4_1": [
        ("A", "흰 거미줄처럼 가늘게 뻗는 층", "Mucor circinelloides", "가느다란 균사가 솜털처럼 확장"),
        ("B", "작고 짙은 올리브색 원형", "Cladosporium cladosporioides", "짙은 벨벳형 집락"),
    ],
    "4_2": [
        ("A", "유난히 큰 검은색 원형", "Aspergillus niger", "검고 빽빽한 포자층"),
        ("B", "주변의 회백색 솜털 번짐", "Mucor circinelloides", "백색·회색으로 뻗는 균사"),
        ("C", "소규모 흰색 돌기 모양", "Bacillus subtilis", "흰색·크림색의 둥글거나 주름진 집락 가능"),
    ],
    # 기존 요청대로 지도와 비교 대상에서는 제외한 교무실 기록
    "4_3": [
        ("A", "넓은 갈색의 미세한 가루 같은 층", "Alternaria alternata", "갈색~흑갈색의 포자 형성"),
        ("B", "동심원 고리·주름 무늬", "Aspergillus niger", "성장 조건에 따라 표면 무늬가 생길 수 있음"),
        ("C", "회검은 원형의 작은 덩어리", "Cladosporium cladosporioides", "회갈색·올리브색의 조밀한 외형"),
    ],
    "4_4": [
        ("A", "흰 레이스처럼 넓게 뻗은 솜털", "Rhizopus stolonifer", "가늘고 빠르게 성장하는 솜털형 균사"),
        ("B", "어두운 회흑색 원형·얼룩", "Cladosporium cladosporioides", "짙은 올리브색의 집락"),
    ],
    "5_1": [
        ("A", "가장자리에서 나뭇가지처럼 뻗는 흰 성장 무늬", "Bacillus mycoides", "뿌리·나뭇가지 같은 세균 집락"),
        ("B", "넓은 회갈색의 흐릿한 층", "Alternaria alternata", "어두운 갈색 계열의 퍼지는 집락"),
        ("C", "독립된 흑회색 작은 원형", "Cladosporium cladosporioides", "어두운색의 조밀한 집락"),
    ],
    "5_2": [
        ("A", "크고 두꺼운 흰색의 꽃잎 모양 주름", "Bacillus subtilis", "건조하고 깊게 주름진 집락이 가능"),
        ("B", "작고 선명한 노란색 원형 점", "Micrococcus luteus", "노란색·크림색의 둥근 집락 가능"),
        ("C", "별도로 보이는 짙은 회색 원형", "Cladosporium cladosporioides", "회갈색·올리브색의 벨벳형 표면"),
    ],
    "5_3": [
        ("A", "회녹색·청록색 원형", "Penicillium rubens", "푸른빛·녹색 포자를 만들 수 있음"),
        ("B", "흰색 솜털 뭉치", "Mucor circinelloides", "흰색의 성긴 균사층"),
        ("C", "회갈색의 점·가루 모양 층", "Alternaria alternata", "갈색의 포자층을 형성"),
    ],
    "5_4": [
        ("A", "갈색으로 넓게 퍼진 가루형 집락", "Alternaria alternata", "회갈색~흑갈색 계열의 포자층"),
        ("B", "외곽의 가는 흰색 솜털", "Mucor circinelloides", "밝고 성긴 솜털 모양 균사"),
        ("C", "작은 짙은색 원형 점들", "Cladosporium cladosporioides", "조밀한 회흑색·올리브색 집락"),
    ],
    "6_1": [
        ("A", "크고 밝은 흰색의 나뭇가지형 가지", "Bacillus mycoides", "균락이 나뭇가지처럼 분지하며 퍼짐"),
        ("B", "가장자리의 작은 짙은 회색 점", "Cladosporium cladosporioides", "어두운 벨벳형 표면"),
    ],
    "6_2": [
        ("A", "어두운 회녹색의 벨벳형 원형", "Cladosporium cladosporioides", "회녹색·올리브색의 조밀한 균총"),
        ("B", "옅고 넓게 퍼진 회백색 층", "Mucor circinelloides", "흰색·회색의 솜털 모양 균사"),
        ("C", "일부 진한 흑색 작은 원형", "Aspergillus niger", "검은 포자층을 형성"),
    ],
    "6_3": [
        ("A", "두껍고 하얀 주름·방사형 성장", "Bacillus subtilis", "마른 표면에 주름을 이루는 세균 집락"),
        ("B", "희미한 넓은 회색 균사", "Mucor circinelloides", "넓게 퍼지는 성긴 균사층"),
        ("C", "분리된 작고 검은 둥근 부분", "Aspergillus niger", "조밀한 흑색 포자층"),
    ],
    "6_4": [
        ("A", "흰색·크림색의 솜털형 번짐", "Rhizopus stolonifer", "희고 솜털 같은 균사와 포자낭"),
        ("B", "뚜렷한 검은 둥근 집락 여러 개", "Aspergillus niger", "검게 보이는 포자층"),
        ("C", "주변 회색의 옅은 원형", "Cladosporium cladosporioides", "올리브색·회흑색의 벨벳형 집락"),
    ],
    "7_1": [
        ("A", "회녹색의 둥근 집락 여러 개", "Cladosporium cladosporioides", "올리브색·회녹색의 벨벳형 집락"),
        ("B", "어두운 테두리와 중심이 있는 원형", "Aspergillus niger", "검게 성숙하는 포자층"),
        ("C", "일부 연한 회백색 가장자리", "Penicillium rubens", "녹색 포자와 연한 바깥 균사"),
    ],
    "7_2": [
        ("A", "매우 큰 하얀 솜털 덩어리", "Mucor circinelloides", "희고 성긴 솜털형 균사"),
        ("B", "아래쪽의 깊은 회흑색 둥근 집락", "Aspergillus niger", "짙은 포자층"),
        ("C", "연갈색의 작고 둥근 부분", "Alternaria alternata", "갈색·회색 계열의 집락"),
    ],
    "7_3": [
        ("A", "짙은 회녹색·올리브색 원형들", "Cladosporium cladosporioides", "올리브색의 조밀한 벨벳형 표면"),
        ("B", "흰 중심·옅은 솜털이 섞인 원형", "Penicillium rubens", "녹색 포자층 주변의 흰색 균사"),
        ("C", "부분적으로 짙은 갈색·검은색", "Aspergillus niger", "검은 포자를 빽빽하게 형성할 수 있음"),
    ],
    "7_4": [
        ("A", "윤기 있는 황갈색·크림색 주름 부분", "Aureobasidium pullulans", "크림색에서 짙게 변하는 점액성 집락 가능"),
        ("B", "널리 퍼진 짙은 회흑색 가루형 층", "Alternaria alternata", "갈색~검은색의 포자층"),
        ("C", "분리된 작고 어두운 둥근 집락", "Cladosporium cladosporioides", "짙은 올리브·회흑색의 조밀한 형태"),
    ],
}


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


# 공간, 채취 대상, 플레이트 번호, 구역 번호
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


# 앞면 사진을 1600 × 1600으로 환산한 자르기 기준
PHOTO_BOUNDS = {
    1: (
        (270, 300, 1370, 1390), (780, 850),
        ((720, 330), (1320, 900), (980, 1380), (310, 810)),
    ),
    2: (
        (170, 285, 1330, 1420), (768, 870),
        ((780, 300), (1320, 885), (730, 1410), (180, 970)),
    ),
    3: (
        (300, 280, 1400, 1400), (850, 750),
        ((700, 280), (1390, 740), (980, 1390), (300, 760)),
    ),
    4: (
        (280, 175, 1385, 1320), (900, 770),
        ((900, 180), (1380, 785), (830, 1320), (290, 760)),
    ),
    5: (
        (160, 170, 1430, 1375), (880, 800),
        ((870, 175), (1430, 825), (820, 1370), (170, 750)),
    ),
    6: (
        (260, 290, 1400, 1400), (790, 810),
        ((800, 300), (1390, 740), (800, 1390), (270, 835)),
    ),
    7: (
        (210, 185, 1420, 1430), (835, 820),
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

    mask = ImageChops.multiply(
        dish_mask,
        sector_mask,
    )

    mask = ImageChops.multiply(
        mask,
        image.getchannel("A"),
    )

    box = mask.getbbox()

    if box is None:
        raise ValueError("사진 자르기 영역을 확인해주세요.")

    result = image.copy()
    result.putalpha(mask)

    return result.crop(box)


def make_display_photo(image):
    fitted = ImageOps.contain(image, (560, 560))

    canvas = Image.new(
        "RGBA",
        (600, 600),
        (0, 0, 0, 0),
    )

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
    rows = IDENTIFICATIONS.get(result_id, [])

    st.markdown("**동정 결과**")

    if not rows:
        st.caption("아직 등록되지 않았습니다.")
        return

    for label, observation, scientific_name, general_trait in rows:
        st.markdown(
            f"**{label}** · *{scientific_name}*"
        )

        st.write(
            f"관찰 특징: {observation}"
        )

        with st.expander(
            f"{label} 미생물의 일반 특징"
        ):
            st.write(general_trait)


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
        st.error(
            f"사진을 표시하지 못했습니다: {error}"
        )


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
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0,
        },
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

    points = event.get(
        "selection",
        {},
    ).get("points", [])

    if points:
        name = points[-1].get("customdata")

        if (
            name in GROUPS
            and name != st.session_state[state_key]
        ):
            st.session_state[state_key] = name
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
