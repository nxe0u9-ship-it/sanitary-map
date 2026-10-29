from pathlib import Path
import base64
import math

from PIL import Image, ImageOps, ImageDraw, ImageChops
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent


# 수정된 자료의 미생물별 설명
BIOLOGY = {
    "Aspergillus niger": (
        "검은색 분생포자가 빽빽해지면 표면이 검은 가루처럼 보이는 사상균. "
        "토양·먼지·부패한 식물체의 유기물을 분해하며, "
        "면역저하자에서는 드물게 중증 감염과 연관된다."
    ),
    "Cladosporium cladosporioides": (
        "올리브색·암갈색의 포자와 벨벳 같은 집락을 형성하는 사상균. "
        "식물 표면·낙엽·공기·실내 먼지에 널리 분포하고, "
        "공기 중 포자가 일부 사람에게 알레르기를 유발할 수 있다."
    ),
    "Mucor circinelloides": (
        "밝은 회백색의 솜털형 균사가 빠르게 퍼지고 포자낭을 만드는 곰팡이. "
        "흙·부패 유기물 등에 존재하며, "
        "면역저하자에게 매우 드물지만 중증 모균증을 일으킬 수 있다."
    ),
    "Penicillium rubens": (
        "청록색 분생포자와 비교적 옅은 바깥 균사가 나타나는 곰팡이. "
        "실내 먼지·식품 등에서 발견될 수 있고, "
        "일부 균주는 항생제 페니실린 생산과 관련이 있다."
    ),
    "Fusarium oxysporum": (
        "흰 균사와 분홍·보라색 계열 색소가 배양 조건에 따라 나타나는 토양성 곰팡이. "
        "식물 시듦병을 일으키는 균주가 있고, "
        "면역저하자에서 드물지만 침습성 감염이 보고된다."
    ),
    "Rhizopus stolonifer": (
        "처음에는 흰 솜털형 균사가 자라고, "
        "포자낭이 성숙하면 검은 점처럼 보일 수 있다. "
        "빵·과일의 부패에 관여하며, "
        "관련 모균류는 면역저하자에서 중증 감염을 일으킬 수 있다."
    ),
    "Alternaria alternata": (
        "갈색 색소를 가진 다세포 분생포자를 만들어 회갈색·흑갈색 집락으로 보인다. "
        "식물의 병반·낙엽·실외 공기에 흔하며, "
        "포자는 알레르기 반응과 관련될 수 있다."
    ),
    "Bacillus subtilis": (
        "그람양성 막대세균으로 건조에 강한 내생포자를 만들고, "
        "표면 생물막이 깊은 주름을 이루기도 한다. "
        "토양·식물 주변에 흔하며 보통 인체 위해성이 낮지만 "
        "균주와 상황에 따른 차이가 있다."
    ),
    "Bacillus mycoides": (
        "그람양성 막대세균이며 내생포자를 만들 수 있다. "
        "흙에서 흔하고, 집락이 뿌리·나뭇가지처럼 "
        "방사형으로 분지하는 것이 유명하다. 일반적 인체 감염은 드물다."
    ),
    "Micrococcus luteus": (
        "그람양성 구균으로 노란 색소를 만들어 작고 둥근 황색 집락을 형성한다. "
        "사람 피부·먼지·토양 등에서 발견되며 보통 무해하지만 "
        "면역저하자에서 드문 기회감염이 보고된다."
    ),
    "Aureobasidium pullulans": (
        "효모처럼 자라기도 하는 진균으로 초기에는 크림색·연분홍색의 점액성 집락, "
        "후기에는 흑갈색 집락을 만든다. "
        "식물 표면과 습한 환경에 존재하고 다당류 풀룰란 생산으로 알려졌다."
    ),
}


# 구분, 관찰 특징, 학명
OBSERVATIONS = {
    "1_1": [
        ("A", "검은색의 굵고 둥근 집락", "Aspergillus niger"),
        ("B", "자주빛이 섞인 흑갈색 원형 집락", "Cladosporium cladosporioides"),
        ("C", "주변의 옅은 회백색 솜털", "Mucor circinelloides"),
    ],
    "1_2": [
        ("A", "어두운 회흑색의 불규칙한 덩어리", "Cladosporium cladosporioides"),
        ("B", "부분적으로 솟은 흰 솜털", "Mucor circinelloides"),
        ("C", "작고 짙은 원형 부분", "Aspergillus niger"),
    ],
    "1_3": [
        ("A", "청록색·회녹색의 작은 둥근 집락", "Penicillium rubens"),
        ("B", "검은 올리브색의 둥근 집락", "Cladosporium cladosporioides"),
        ("C", "흰색·연분홍빛의 작은 솜털", "Fusarium oxysporum"),
    ],
    "1_4": [
        ("A", "넓고 흰색인 구름·솜털 모양", "Mucor circinelloides"),
        ("B", "작고 어두운 회흑색 원형", "Aspergillus niger"),
        ("C", "외곽의 회색·올리브색 고리", "Cladosporium cladosporioides"),
    ],
    "2_1": [
        ("A", "넓게 덮인 회백색 솜털", "Mucor circinelloides"),
        ("B", "솜털 속 검은 점과 짙은 둥근 부분", "Rhizopus stolonifer"),
    ],
    "2_2": [
        ("A", "회갈색의 넓고 흐릿한 솜털", "Alternaria alternata"),
        ("B", "독립된 검은 둥근 집락", "Aspergillus niger"),
        ("C", "작은 회흑색 점들이 모인 부분", "Cladosporium cladosporioides"),
    ],
    "2_3": [
        ("A", "빽빽한 어두운 올리브색 원형들", "Cladosporium cladosporioides"),
        ("B", "가느다란 흰색 솜털 덩어리", "Mucor circinelloides"),
        ("C", "회갈색의 옅은 번짐", "Alternaria alternata"),
    ],
    "2_4": [
        ("A", "넓게 퍼진 회색 솜털층", "Rhizopus stolonifer"),
        ("B", "검고 둥근 조밀한 부분", "Aspergillus niger"),
        ("C", "군데군데 작은 흰 솜털", "Mucor circinelloides"),
    ],
    "3_1": [
        ("A", "매우 크게 뭉친 짙은 검은색 집락", "Aspergillus niger"),
        ("B", "경계에 섞인 회백색 솜털", "Mucor circinelloides"),
    ],
    "3_2": [
        ("A", "진한 올리브·회녹색 원형", "Cladosporium cladosporioides"),
        ("B", "흑색 중심이 있는 작은 원형", "Aspergillus niger"),
        ("C", "그 사이 흰색 솜털 부분", "Mucor circinelloides"),
    ],
    "3_3": [
        ("A", "큰 흰색 솜털형 덩어리", "Mucor circinelloides"),
        ("B", "약한 분홍빛·연보랏빛의 작은 부분", "Fusarium oxysporum"),
        ("C", "회흑색의 작은 둥근 집락", "Cladosporium cladosporioides"),
    ],
    "3_4": [
        ("A", "넓은 회백색 솜털형 층", "Rhizopus stolonifer"),
        ("B", "따로 보이는 검은 원형", "Aspergillus niger"),
        ("C", "붉은빛·연갈색 고리 모양", "Fusarium oxysporum"),
    ],
    "4_1": [
        ("A", "흰 거미줄처럼 가늘게 뻗는 층", "Mucor circinelloides"),
        ("B", "작고 짙은 올리브색 원형", "Cladosporium cladosporioides"),
    ],
    "4_2": [
        ("A", "유난히 큰 검은색 원형", "Aspergillus niger"),
        ("B", "주변의 회백색 솜털 번짐", "Mucor circinelloides"),
        ("C", "소규모 흰색 돌기 모양", "Bacillus subtilis"),
    ],
    "4_4": [
        ("A", "흰 레이스처럼 넓게 뻗은 솜털", "Rhizopus stolonifer"),
        ("B", "어두운 회흑색 원형·얼룩", "Cladosporium cladosporioides"),
    ],
    "5_1": [
        ("A", "가장자리에서 나뭇가지처럼 뻗는 흰 성장 무늬", "Bacillus mycoides"),
        ("B", "넓은 회갈색의 흐릿한 층", "Alternaria alternata"),
        ("C", "독립된 흑회색 작은 원형", "Cladosporium cladosporioides"),
    ],
    "5_2": [
        ("A", "크고 두꺼운 흰색의 꽃잎 모양 주름", "Bacillus subtilis"),
        ("B", "작고 선명한 노란색 원형 점", "Micrococcus luteus"),
        ("C", "별도로 보이는 짙은 회색 원형", "Cladosporium cladosporioides"),
    ],
    "5_3": [
        ("A", "회녹색·청록색 원형", "Penicillium rubens"),
        ("B", "흰색 솜털 뭉치", "Mucor circinelloides"),
        ("C", "회갈색의 점·가루 모양 층", "Alternaria alternata"),
    ],
    "5_4": [
        ("A", "갈색으로 넓게 퍼진 가루형 집락", "Alternaria alternata"),
        ("B", "외곽의 가는 흰색 솜털", "Mucor circinelloides"),
        ("C", "작은 짙은색 원형 점들", "Cladosporium cladosporioides"),
    ],
    "6_1": [
        ("A", "크고 밝은 흰색의 나뭇가지형 가지", "Bacillus mycoides"),
        ("B", "가장자리의 작은 짙은 회색 점", "Cladosporium cladosporioides"),
    ],
    "6_2": [
        ("A", "어두운 회녹색의 벨벳형 원형", "Cladosporium cladosporioides"),
        ("B", "옅고 넓게 퍼진 회백색 층", "Mucor circinelloides"),
        ("C", "일부 진한 흑색 작은 원형", "Aspergillus niger"),
    ],
    "6_3": [
        ("A", "두껍고 하얀 주름·방사형 성장", "Bacillus subtilis"),
        ("B", "희미한 넓은 회색 균사", "Mucor circinelloides"),
        ("C", "분리된 작고 검은 둥근 부분", "Aspergillus niger"),
    ],
    "6_4": [
        ("A", "흰색·크림색의 솜털형 번짐", "Rhizopus stolonifer"),
        ("B", "뚜렷한 검은 둥근 집락 여러 개", "Aspergillus niger"),
        ("C", "주변 회색의 옅은 원형", "Cladosporium cladosporioides"),
    ],
    "7_1": [
        ("A", "회녹색의 둥근 집락 여러 개", "Cladosporium cladosporioides"),
        ("B", "어두운 테두리와 중심이 있는 원형", "Aspergillus niger"),
        ("C", "일부 연한 회백색 가장자리", "Penicillium rubens"),
    ],
    "7_2": [
        ("A", "매우 큰 하얀 솜털 덩어리", "Mucor circinelloides"),
        ("B", "아래쪽의 깊은 회흑색 둥근 집락", "Aspergillus niger"),
        ("C", "연갈색의 작고 둥근 부분", "Alternaria alternata"),
    ],
    "7_3": [
        ("A", "짙은 회녹색·올리브색 원형들", "Cladosporium cladosporioides"),
        ("B", "흰 중심·옅은 솜털이 섞인 원형", "Penicillium rubens"),
        ("C", "부분적으로 짙은 갈색·검은색", "Aspergillus niger"),
    ],
    "7_4": [
        ("A", "윤기 있는 황갈색·크림색 주름 부분", "Aureobasidium pullulans"),
        ("B", "널리 퍼진 짙은 회흑색 가루형 층", "Alternaria alternata"),
        ("C", "분리된 작고 어두운 둥근 집락", "Cladosporium cladosporioides"),
    ],
}


# 자료에 제시된 (평균 점수, 상대 단계)
RISK_RESULTS = {
    "1_1": (3.67, 4),
    "1_2": (3.67, 4),
    "1_3": (3.00, 2),
    "1_4": (3.67, 4),
    "2_1": (5.00, 5),
    "2_2": (3.00, 2),
    "2_3": (3.33, 3),
    "2_4": (4.67, 5),
    "3_1": (4.50, 5),
    "3_2": (3.67, 4),
    "3_3": (4.00, 4),
    "3_4": (4.67, 5),
    "4_1": (3.50, 3),
    "4_2": (3.33, 3),
    "4_4": (3.50, 3),
    "5_1": (2.33, 2),
    "5_2": (1.33, 1),
    "5_3": (3.33, 3),
    "5_4": (3.33, 3),
    "6_1": (2.00, 1),
    "6_2": (3.67, 4),
    "6_3": (3.33, 3),
    "6_4": (3.67, 4),
    "7_1": (2.67, 2),
    "7_2": (4.00, 4),
    "7_3": (2.67, 2),
    "7_4": (2.67, 2),
}


IDENTIFICATIONS = {
    key: [
        (label, observation, species, BIOLOGY[species])
        for label, observation, species in rows
    ]
    for key, rows in OBSERVATIONS.items()
}


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
    rows = IDENTIFICATIONS.get(result_id, [])
    risk = RISK_RESULTS.get(result_id)

    if risk:
        score, stage = risk

        colors = {
            1: ("#E8F2FF", "#184A7D"),
            2: ("#E3F4EE", "#205442"),
            3: ("#FFF4CD", "#6B5000"),
            4: ("#FFE5CD", "#7D3F11"),
            5: ("#FCE1E7", "#842C43"),
        }

        background, foreground = colors[stage]

        st.markdown(
            f'<div style="background:{background};'
            f'color:{foreground};padding:13px 15px;'
            'border-radius:12px;margin:10px 0;font-weight:700;">'
            f'<div style="font-size:18px;">'
            f'상대 잠재 중증도 {stage}단계 / 5단계</div>'
            f'<div style="font-size:15px;margin-top:5px;">'
            f'자료상 평균 점수 {score:.2f} / 5</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "교육용 상대등급이며, 실제 감염률·치사율이나 "
            "장소의 안전도를 뜻하지 않습니다."
        )

        with st.expander("등급 계산 기준"):
            st.write(
                "PDF에서 정한 미생물별 가중치를 "
                "집락 형태별로 같은 비중으로 평균한 점수입니다."
            )

            st.write(
                "1단계: 2.00 이하 / "
                "2단계: 2.00 초과~3.00 이하 / "
                "3단계: 3.00 초과~3.60 이하 / "
                "4단계: 3.60 초과~4.25 이하 / "
                "5단계: 4.25 초과"
            )

            st.caption(
                "가중치와 구간은 자료의 학습용 설정이며 "
                "의학적으로 검증된 위험도 공식이 아닙니다."
            )

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
            f"{label} 미생물의 생태·특징"
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

    xs, ys, names = [], [], []

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
        f'<span style="background:{background};'
        f'color:{foreground};padding:11px 14px;'
        f'border-radius:10px;font-size:17px;'
        f'font-weight:700;">{label}</span>'
        for background, foreground, label in items
    )

    st.markdown(
        '<div style="display:flex;gap:10px;'
        'flex-wrap:wrap;margin:8px 0 16px;">'
        + cards
        + "</div>",
        unsafe_allow_html=True,
    )
