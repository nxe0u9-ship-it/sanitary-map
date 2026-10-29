import streamlit as st

from school_data import (
    RESULTS,
    GROUPS,
    render_map,
    show_legend,
    show_result_photo,
    show_identification,
)


st.set_page_config(
    page_title="둔산여고 위생맵",
    page_icon="🧫",
    layout="wide",
)


def show_hygiene_map():
    st.title("🧫 둔산여고 위생맵")

    st.write(
        "형광펜으로 표시된 장소 이름을 누르면 "
        "아래에서 배양 사진과 동정 결과를 확인할 수 있습니다."
    )

    # 지도를 좌우로 나누지 않고 전체 폭으로 표시
    st.subheader("📍 학교 공간 지도")

    show_legend()

    render_map(
        "active_map_place",
        "main_map_fullwidth_v3",
    )

    st.caption(
        "‘계단’ 기록은 본관 왼쪽 아래 계단에 "
        "임시 연결했습니다."
    )

    st.divider()

    # 선택한 장소의 기록은 지도 아래에 표시
    st.subheader("🔎 선택한 공간의 전체 기록")

    place = st.session_state.get("active_map_place")

    if not place:
        st.info(
            "위 지도에서 장소 이름을 눌러주세요."
        )

    else:
        st.markdown(f"### 📍 {place}")

        result_ids = GROUPS[place]
        column_count = min(3, len(result_ids))

        for start in range(
            0,
            len(result_ids),
            column_count,
        ):
            columns = st.columns(
                column_count,
                gap="large",
            )

            row = result_ids[
                start:start + column_count
            ]

            for column, result_id in zip(columns, row):
                with column:
                    st.markdown(
                        f"#### {RESULTS[result_id]['short']}"
                    )

                    show_result_photo(
                        result_id,
                        framed=True,
                    )

                    show_identification(result_id)

            st.divider()

    with st.expander("전체 채취 기록 확인"):
        st.table([
            {
                "공간": record["place"],
                "채취 대상": record["short"],
            }
            for record in RESULTS.values()
        ])

    st.caption(
        "집락에 가려진 구역선은 보이는 부분의 "
        "연장 방향으로 추정했습니다."
    )

    st.subheader("💡 결과 해석 안내")

    st.write(
        "같은 채취 방법과 배양 조건에서 얻은 결과끼리 비교합니다. "
        "사진만으로 미생물의 종이나 병원성을 확정하거나 "
        "장소 전체의 안전성을 판단하지 않습니다."
    )


page = st.navigation([
    st.Page(
        show_hygiene_map,
        title="둔산여고 위생맵",
        icon="🧫",
        default=True,
    ),
    st.Page(
        "pages/1_배양_결과_비교.py",
        title="배양 결과 비교",
        icon="🔬",
    ),
])

page.run()
