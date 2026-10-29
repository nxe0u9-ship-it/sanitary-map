import streamlit as st

from school_data import (
    RESULTS,
    GROUPS,
    RISK_RESULTS,
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

    st.subheader("📍 학교 공간 지도")

    show_legend()

    render_map(
        "active_map_place",
        "main_map_fullwidth_v3",
    )

    st.divider()

    st.subheader("🔎 선택한 공간의 전체 기록")

    place = st.session_state.get(
        "active_map_place"
    )

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

                    show_identification(
                        result_id
                    )

            st.divider()

    with st.expander("전체 채취 기록 확인"):
        risk_icons = {
            1: "🔵",
            2: "🟢",
            3: "🟡",
            4: "🟠",
            5: "🔴",
        }

        sorted_ids = sorted(
            RESULTS,
            key=lambda result_id: (
                RISK_RESULTS.get(
                    result_id,
                    (0, 0),
                )[1],
                RISK_RESULTS.get(
                    result_id,
                    (0, 0),
                )[0],
            ),
            reverse=True,
        )

        rows = []

        for result_id in sorted_ids:
            record = RESULTS[result_id]
            risk = RISK_RESULTS.get(result_id)

            if risk is None:
                risk_text = "미등록"
                score_text = "—"

            else:
                score, stage = risk

                risk_text = (
                    f"{risk_icons[stage]} {stage}단계"
                )

                score_text = f"{score:.2f}"

            rows.append(
                {
                    "공간": record["place"],
                    "채취 대상": record["short"],
                    "위험도": risk_text,
                    "점수": score_text,
                }
            )

        st.table(rows)


page = st.navigation(
    [
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
    ]
)

page.run()
