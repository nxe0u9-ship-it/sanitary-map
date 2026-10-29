import streamlit as st

from school_data import (
    RESULTS,
    GROUPS,
    display_name,
    render_map,
    show_legend,
    show_result_photo,
    show_identification,
)


st.set_page_config(
    page_title="배양 결과 비교",
    page_icon="🧫",
    layout="wide",
)

if "compare_ids" not in st.session_state:
    st.session_state.compare_ids = []


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

    show_legend(comparison=True)

    render_map(
        "compare_place",
        "compare_map_v2",
        st.session_state.compare_ids,
    )


with selection_column:
    st.subheader("☑️ 비교할 대상 고르기")

    place = st.session_state.get("compare_place")

    if not place:
        st.info(
            "왼쪽 지도에서 장소 이름을 눌러주세요."
        )

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
                on_click=select_place_results,
                args=(place,),
            )

        st.caption(
            "체크한 대상은 아래 비교 영역에 바로 추가됩니다."
        )


st.divider()
st.subheader("🔬 선택한 배양 결과와 동정 결과")

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
            with column:
                st.markdown(
                    f"#### {display_name(RESULTS[result_id])}"
                )

                show_result_photo(
                    result_id,
                    framed=True,
                )

                show_identification(result_id)

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
    "실제 집락 크기를 재는 척도로 사용할 수 없습니다."
)

st.info(
    "집락의 색·모양·표면·퍼진 정도와 동정 근거를 "
    "함께 비교해보세요. 장소별 차이를 해석하려면 "
    "채취 방법과 배양 조건도 확인해야 합니다."
)
