from pathlib import Path
from io import BytesIO
import base64
import math

from PIL import Image, ImageOps, ImageDraw, ImageChops
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent


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


# 내부 데이터 구조를 유지하기 위한 자료입니다.
# 화면에는 학명과 생태 특징만 표시합니다.
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


RISK_COLORS = {
    1: ("#E8F2FF", "#184A7D"),
    2: ("#E3F4EE", "#205442"),
    3: ("#FFF4CD", "#6B5000"),
    4: ("#FFE5CD", "#7D3F11"),
    5: ("#FCE1E7", "#842C43"),
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


def make_display_photo(image):
    fitted = ImageOps.contain(
        image,
        (560, 560),
    )

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
    rows = IDENTIFICATIONS.get(
        result_id,
        [],
    )

    risk = RISK_RESULTS.get(result_id)

    if risk:
        score, stage = risk
        background, foreground = RISK_COLORS[stage]

        st.markdown(
            f'<div style="background:{background};'
            f'color:{foreground};'
            'padding:13px 15px;'
            'border-radius:12px;'
            'margin:10px 0;'
            'font-weight:700;">'
            '<div style="font-size:18px;">'
            f'위험도 {stage}단계 / 5단계'
            '</div>'
            '<div style="font-size:15px;margin-top:5px;">'
            f'자료 기준 점수 {score:.2f} / 5'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("**동정 결과**")

    if not rows:
        st.caption(
            "아직 등록되지 않았습니다."
        )
        return

    for _label, _observation, scientific_name, general_trait in rows:
        st.markdown(
            f"- **{scientific_name}**"
        )

        st.write(general_trait)


def show_result_photo(result_id, framed=False):
    path = (
        BASE_DIR
        / "sample_photos"
        / f"{result_id}.png"
    )

    if not path.is_file():
        st.warning(
            "배양 사진 파일을 찾지 못했습니다: "
            f"sample_photos/{result_id}.png"
        )
        return

    try:
        with Image.open(path) as source:
            image = source.convert("RGBA")

        if framed:
            image = make_display_photo(image)

        st.image(
            image,
            use_container_width=True,
        )

    except (OSError, ValueError) as error:
        st.error(
            f"사진을 표시하지 못했습니다: {error}"
        )


def place_risk(place):
    stages = [
        RISK_RESULTS[result_id][1]
        for result_id in GROUPS[place]
        if result_id in RISK_RESULTS
    ]

    if not stages:
        return None, None

    average = sum(stages) / len(stages)

    color_stage = min(
        5,
        max(
            1,
            math.floor(average + 0.5),
        ),
    )

    return average, color_stage


def hex_rgba(color, alpha):
    return (
        f"rgba({int(color[1:3], 16)},"
        f"{int(color[3:5], 16)},"
        f"{int(color[5:7], 16)},"
        f"{alpha})"
    )


def render_map(state_key, chart_key, chosen_ids=()):
    if st.session_state.get(state_key) not in GROUPS:
        st.session_state[state_key] = None

    path = BASE_DIR / "school_map.png"

    if not path.is_file():
        st.error(
            "학교 지도 사진을 찾지 못했습니다."
        )
        return

    with Image.open(path) as source:
        map_image = source.convert("RGB").resize(
            (818, 560)
        )

    tint = Image.new(
        "RGB",
        map_image.size,
        "white",
    )

    tint_draw = ImageDraw.Draw(tint)

    for name, bounds in HIGHLIGHTS.items():
        _, stage = place_risk(name)

        if name == st.session_state[state_key]:
            color = "#E9D5FF"
        else:
            color = (
                RISK_COLORS[stage][0]
                if stage
                else "#E5E7EB"
            )

        tint_draw.rectangle(
            bounds,
            fill=color,
        )

    # 지도 글씨를 유지하면서 배경에 색상을 적용합니다.
    colored_map = ImageChops.multiply(
        map_image,
        tint,
    )

    buffer = BytesIO()

    colored_map.save(
        buffer,
        format="PNG",
    )

    encoded = base64.b64encode(
        buffer.getvalue()
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

    xs = []
    ys = []
    names = []
    texts = []

    for name, bounds in HIGHLIGHTS.items():
        left, top, right, bottom = bounds
        average, stage = place_risk(name)

        if name == st.session_state[state_key]:
            fig.add_shape(
                type="rect",
                x0=left,
                y0=top,
                x1=right,
                y1=bottom,
                fillcolor="rgba(0,0,0,0)",
                line={
                    "color": "#7C3AED",
                    "width": 2.5,
                },
                layer="above",
            )

        if average is not None:
            hover = (
                f"{name}"
                f"<br>평균 위험도 {average:.2f} / 5"
                f"<br>색상 기준 {stage}단계 · 자료 기준"
            )
        else:
            hover = (
                f"{name}"
                "<br>위험도 미등록"
            )

        # 글자를 가리는 점 없이 영역 전체를 클릭할 수 있게 합니다.
        for x in range(left, right + 1, 4):
            for y in range(top, bottom + 1, 4):
                xs.append(x)
                ys.append(y)
                names.append(name)
                texts.append(hover)

    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            customdata=names,
            text=texts,
            mode="markers",
            marker={
                "size": 6,
                "symbol": "square",
                "color": "rgba(0,0,0,0.001)",
            },
            selected={
                "marker": {
                    "opacity": 1,
                }
            },
            unselected={
                "marker": {
                    "opacity": 1,
                }
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
        xaxis={
            "range": [0, 818],
            "autorange": False,
            "visible": False,
            "fixedrange": True,
            "constrain": "domain",
            "constraintoward": "left",
        },
        yaxis={
            "range": [560, 0],
            "autorange": False,
            "visible": False,
            "fixedrange": True,
            "scaleanchor": "x",
            "scaleratio": 1,
            "constrain": "domain",
            "constraintoward": "top",
        },
        paper_bgcolor="white",
        plot_bgcolor="white",
    )

    event = st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"{chart_key}_purple_v5",
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
    ).get(
        "points",
        [],
    )

    if points:
        name = points[-1].get(
            "customdata"
        )

        if (
            name in GROUPS
            and name != st.session_state[state_key]
        ):
            st.session_state[state_key] = name
            st.rerun()


def show_legend(comparison=False):
    cards = "".join(
        (
            f'<span style="background:{background};'
            f'color:{foreground};'
            f'border:1px solid {foreground};'
            'padding:10px 13px;'
            'border-radius:10px;'
            'font-size:17px;'
            'font-weight:700;">'
            f'위험도 {stage}단계'
            '</span>'
        )
        for stage, (background, foreground)
        in RISK_COLORS.items()
    )

    cards += (
        '<span style="background:#7C3AED;'
        'color:white;'
        'padding:10px 13px;'
        'border-radius:10px;'
        'font-size:17px;'
        'font-weight:700;">'
        '현재 선택한 공간'
        '</span>'
    )

    st.markdown(
        '<div style="display:flex;'
        'gap:9px;'
        'flex-wrap:wrap;'
        'margin:8px 0 12px;">'
        + cards
        + '</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "자료 기준 · 공간별 위험도 단계의 평균값을 "
        "반올림해 색상으로 표시합니다."
    )
