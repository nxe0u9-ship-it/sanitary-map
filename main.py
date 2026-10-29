import streamlit as st

from school_data import (
\RESULTS,
\GROUPS,
\RISK_RESULTS,
\render_map,
\show_legend,
\show_result_photo,
\show_identification,
)

st.set_page_config(
\page_title="둔산여고 위생맵",
\page_icon="🧫",
\layout="wide",
)

if "map_visit" not in st.session_state:
\st.session_state.map_visit = 0

# ============================================================
# 참고문헌 및 출처
# ============================================================

REFERENCES = [
(
"Aspergillus niger",
"Institut national de santé publique du Québec (INSPQ)",
"https://www.inspq.qc.ca/en/moulds/fact-sheets/aspergillus-niger",
),
(
"Cladosporium cladosporioides",
"Institut national de santé publique du Québec (INSPQ)",
"https://www.inspq.qc.ca/en/moulds/fact-sheets/cladosporium-cladosporioides",
),
(
"Mucor circinelloides",
"University of Adelaide, Mycology — Mucor",
"https://mycology.adelaide.edu.au/fungal-descriptions-and-antifungal-susceptibility/mucoromycota-pin-moulds/mucor",
),
(
"Penicillium rubens",
"Houbraken et al. (2011), IMA Fungus",
"https://pmc.ncbi.nlm.nih.gov/articles/PMC3317369/",
),
(
"Penicillium spp.",
"Institut national de santé publique du Québec (INSPQ)",
"https://www.inspq.qc.ca/en/moulds/fact-sheets/penicillium-spp",
),
(
"Fusarium oxysporum",
"European Food Safety Authority (EFSA)",
"https://efsa.onlinelibrary.wiley.com/doi/10.2903/j.efsa.2022.7092",
),
(
"Rhizopus stolonifer",
"University of California, Davis",
"https://wine.ucdavis.edu/industry-info/enology/wine-microbiology/yeast-mold/rhizopus-stolonifer",
),
(
"Alternaria alternata",
"Institut national de santé publique du Québec (INSPQ)",
"https://www.inspq.qc.ca/en/moulds/fact-sheets/alternaria-alternata",
),
(
"Bacillus subtilis",
"The Adaptive Morphology of Bacillus subtilis Biofilms (2020)",
"https://pmc.ncbi.nlm.nih.gov/articles/PMC7023499/",
),
(
"Bacillus mycoides",
"Formation of unique T-shape budding and differential impacts "
"of low surface water on Bacillus mycoides rhizoidal colony (2022)",
"https://pubmed.ncbi.nlm.nih.gov/35896814/",
),
(
"Micrococcus luteus",
"Public Health Agency of Canada — Micrococcus spp.",
"https://www.canada.ca/en/public-health/services/laboratory-biosafety-biosecurity/pathogen-safety-data-sheets-risk-assessment/micrococcus.html",
),
(
"Aureobasidium pullulans",
"University of Adelaide, Mycology",
"https://mycology.adelaide.edu.au/fungal-descriptions-and-antifungal-susceptibility/hyphomycetes-conidial-moulds/aureobasidium",
),
(
"미생물 동정 방법",
"Fungal identification based on the polyphasic approach: "
"a clinical practice guideline, Annals of Clinical Microbiology",
"https://www.acm.or.kr/2704-02/",
),
]

# ============================================================
# 전체 채취 기록
# ============================================================

def show_all_records():
\with st.expander("전체 채취 기록 확인"):
\risk_icons = {
\1: "🔵",
\2: "🟢",
\3: "🟡",
\4: "🟠",
\5: "🔴",
}

\sorted_ids = sorted(
\RESULTS,
\key=lambda result_id: (
\RISK_RESULTS.get(
\result_id,
(0, 0),
)[1],
\RISK_RESULTS.get(
\result_id,
(0, 0),
)[0],
),
\reverse=True,
)

\rows = []

\for result_id in sorted_ids:
\record = RESULTS[result_id]
\risk = RISK_RESULTS.get(result_id)

\if risk is None:
\risk_text = "미등록"
\score_text = "—"

\else:
\score, stage = risk

\risk_text = (
\f"{risk_icons[stage]} {stage}단계"
)

\score_text = f"{score:.2f}"

\rows.append(
{
"공간": record["place"],
"채취 대상": record["short"],
"위험도": risk_text,
"점수": score_text,
}
)

\st.table(rows)

# ============================================================
# 참고문헌 표시 (새로 추가)
# ============================================================

def show_references():

\st.subheader("📚 참고문헌 및 출처")

\st.write(
"미생물의 학명, 형태적 특징 및 생태적 특성을 "
"조사할 때 참고한 학술 논문과 공공기관 자료입니다."
)

\with st.expander(
"참고문헌 전체 보기",
\expanded=False,
):

\for number, (
\scientific_name,
\source,
\url,
) in enumerate(REFERENCES, start=1):

\st.markdown(
\f"{number}. {scientific_name}"
)

\st.markdown(
\f"출처: [{source}]({url})"
)

\if number < len(REFERENCES):
\st.divider()

\st.caption(
"※ 위 문헌은 미생물의 일반적인 특성에 관한 자료입니다. "
"배양 사진만으로 정확한 종을 확정할 수 없으므로 "
"화면에 제시된 학명은 형태적 특징에 따른 추정 후보입니다. "
"위험도 역시 실제 치사율이나 감염 위험을 측정한 값이 아닌 "
"탐구용 상대평가입니다."
)

# ============================================================
# 학교 위생 지도
# ============================================================

def show_hygiene_map():
\st.title("🧫 둔산여고 위생맵")

\st.write(
"형광펜으로 표시된 장소 이름을 누르면 "
"해당 장소의 배양 사진과 동정 결과 페이지로 이동합니다."
)

\st.subheader("📍 학교 공간 지도")

\show_legend()

\render_map(
"active_map_place",
\f"main_map_visit_{st.session_state.map_visit}",
)

\place = st.session_state.get(
"active_map_place"
)

\if place in GROUPS:
\st.session_state.detail_place = place
\st.session_state.active_map_place = None

# 지도로 돌아왔을 때 이전 클릭이
# 재실행되지 않게 합니다.
\st.session_state.map_visit += 1

\st.switch_page(result_page)

\st.divider()

# 전체 채취 기록
\show_all_records()

# 참고문헌 및 출처
\show_references()

# ============================================================
# 장소별 배양 결과
# ============================================================

def show_place_results():
\if st.button(
"← 지도로 돌아가기",
\key="back_to_map_top",
):
\st.switch_page(map_page)

\place = st.session_state.get(
"detail_place"
)

\if place not in GROUPS:
\st.info(
"지도에서 확인할 장소를 선택해주세요."
)
\return

\st.title(f"📍 {place}")

\st.subheader("🔬 배양 사진과 동정 결과")

\result_ids = GROUPS[place]
\column_count = min(3, len(result_ids))

\for start in range(
\0,
\len(result_ids),
\column_count,
):
\columns = st.columns(
\column_count,
\gap="large",
)

\row = result_ids[
\start:start + column_count
]

\for column, result_id in zip(columns, row):
\with column:
\st.markdown(
\f"### {RESULTS[result_id]['short']}"
)

\show_result_photo(
\result_id,
\framed=True,
)

\show_identification(
\result_id
)

\st.divider()

\if st.button(
"← 지도로 돌아가기",
\key="back_to_map_bottom",
):
\st.switch_page(map_page)

# ============================================================
# 페이지 설정
# ============================================================

map_page = st.Page(
\show_hygiene_map,
\title="둔산여고 위생맵",
\icon="🧫",
\default=True,
)

comparison_page = st.Page(
"pages/1_배양_결과_비교.py",
\title="배양 결과 비교",
\icon="🔬",
)

result_page = st.Page(
\show_place_results,
\title="장소별 결과",
\icon="📍",
\url_path="place-results",
)

page = st.navigation(
[
\map_page,
\comparison_page,
\result_page,
],
\position="hidden",
)

# ============================================================
# 사이드바
# ============================================================

with st.sidebar:
\st.page_link(
\map_page,
\label="둔산여고 위생맵",
\icon="🧫",
)

\st.page_link(
\comparison_page,
\label="배양 결과 비교",
\icon="🔬",
)

# ============================================================
# 앱 실행
# ============================================================

page.run()
