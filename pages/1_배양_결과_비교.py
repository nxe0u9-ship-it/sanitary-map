from pathlib import Path
import math

from PIL import Image, ImageOps, ImageDraw, ImageChops
import streamlit as st


st.set_page_config(
    page_title="배양 결과 비교 | 우리 학교 위생맵",
    page_icon="🧫",
    layout="wide",
)

# main.py와 사진이 있는 폴더
BASE_DIR = Path(__file__).resolve().parents[1]


# 지도 공간, 채취 대상, 플레이트 번호, 구역 번호
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


# 지도 페이지와 동일한 사진 자르기 기준
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

    ImageDraw.Draw(sector_mask).polygon(
        points,
        fill=255,
    )

    mask = ImageChops.multiply(dish_mask, sector_mask)
    mask = ImageChops.multiply(mask, image.getchannel("A"))

    box = mask.getbbox()

    if box is None:
        raise ValueError("사진 자르기 영역을 확인해주세요.")

    result = image.copy()
    result.putalpha(mask)

    return result.crop(box)


def make_display_photo(image):
    """사진의 비율을 유지하면서 같은 크기의 틀에 배치합니다."""
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


RESULTS = {
    (plate, section): {
        "place": place,
        "target": target,
    }
    for place, target, plate, section in SAMPLES
}


def result_label(result_id):
    record = RESULTS[result_id]
    plate, section = result_id

    return (
        f"{record['target']} · {record['place']} "
        f"({plate}번 플레이트 / {section}번 구역)"
    )


st.title("🧫 배양 결과 비교")

st.write(
    "비교하고 싶은 채취 대상을 하나씩 선택하면 "
    "배양 사진을 나란히 볼 수 있습니다."
)


selected = st.multiselect(
    "비교할 채취 대상 선택",
    options=list(RESULTS),
    format_func=result_label,
    key="comparison_selected_results",
    placeholder="채취 대상을 선택하거나 이름을 검색하세요",
    help=(
        "여러 개를 선택할 수 있습니다. "
        "선택한 항목의 ×를 누르면 비교에서 제외됩니다."
    ),
)


if not selected:
    st.info(
        "위 목록에서 비교하고 싶은 채취 대상을 선택해주세요."
    )

else:
    st.caption(
        f"현재 {len(selected)}개 선택 · "
        "한 줄에 최대 3개씩 표시합니다. "
        "선택한 항목의 ×를 누르면 뺄 수 있습니다."
    )

    st.divider()

    column_count = min(3, len(selected))

    for start in range(0, len(selected), column_count):
        columns = st.columns(
            column_count,
            gap="large",
        )

        row = selected[start:start + column_count]

        for column, result_id in zip(columns, row):
            plate, section = result_id
            record = RESULTS[result_id]

            with column:
                st.subheader(record["target"])
                st.write(f"📍 {record['place']}")

                st.caption(
                    f"{plate}번 플레이트 · "
                    f"{section}번 구역"
                )

                try:
                    original = get_photo(plate)

                    if original is None:
                        st.warning(
                            f"plate{plate}_front "
                            "사진 파일이 없습니다."
                        )

                    else:
                        cropped = crop_sector(
                            original,
                            plate,
                            section,
                        )

                        st.image(
                            make_display_photo(cropped),
                            use_container_width=True,
                        )

                except (OSError, ValueError) as error:
                    st.error(
                        f"사진을 표시하지 못했습니다: {error}"
                    )

                st.caption(
                    "동정 상태: 미동정 · 집락 수: 미계수"
                )

        st.divider()


st.subheader("🔎 이런 특징을 비교해보세요")

st.write(
    "집락의 색, 둥글거나 불규칙한 모양, "
    "표면의 솜털 같은 모습, 서로 겹치거나 "
    "퍼진 정도를 살펴보세요."
)

st.caption(
    "각 사진은 화면에서 보기 편하도록 크기를 맞췄습니다. "
    "실제 집락 크기를 재는 척도로 사용할 수 없습니다."
)

st.info(
    "사진의 색과 모양만으로 미생물의 종이나 병원성을 "
    "확정할 수 없습니다. 장소별 차이를 해석하려면 "
    "채취 방법과 배양 조건이 같은지도 확인해야 합니다."
)
