    stages = [
        RISK_RESULTS[result_id][1]
        for result_id in GROUPS[place]
        if result_id in RISK_RESULTS
    ]
    if not stages:
        return None, None
    average = sum(stages) / len(stages)
    color_stage = min(5, max(1, math.floor(average + 0.5)))
    return average, color_stage


def hex_rgba(color, alpha):
    return (
        f"rgba({int(color[1:3], 16)},{int(color[3:5], 16)},"
        f"{int(color[5:7], 16)},{alpha})"
    )


def render_map(state_key, chart_key, chosen_ids=()):
    if st.session_state.get(state_key) not in GROUPS:
        st.session_state[state_key] = None
    path = BASE_DIR / "school_map.png"
    if not path.is_file():
        st.error("학교 지도 사진을 찾지 못했습니다.")
        return
    from io import BytesIO

    with Image.open(path) as source:
        map_image = source.convert("RGB").resize((818, 560))
    tint = Image.new("RGB", map_image.size, "white")
    tint_draw = ImageDraw.Draw(tint)
    for name, bounds in HIGHLIGHTS.items():
        _, stage = place_risk(name)
        color = "#E9D5FF" if name == st.session_state[state_key] else (
            RISK_COLORS[stage][0] if stage else "#E5E7EB"
        )
        tint_draw.rectangle(bounds, fill=color)
    # 곱하기 합성: 검은 글씨는 검게 유지하고 밝은 배경만 물들입니다.
    colored_map = ImageChops.multiply(map_image, tint)
    buffer = BytesIO()
    colored_map.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    fig = go.Figure()
    fig.add_layout_image(
        source=f"data:image/png;base64,{encoded}", xref="x", yref="y",
        x=0, y=0, sizex=818, sizey=560, sizing="stretch",
        xanchor="left", yanchor="top", layer="below",
    )
    chosen_places = {RESULTS[item]["place"] for item in chosen_ids if item in RESULTS}
    xs, ys, names, texts = [], [], [], []
    for name, (left, top, right, bottom) in HIGHLIGHTS.items():
        average, stage = place_risk(name)
        if name == st.session_state[state_key]:
            fill = "rgba(0,0,0,0)"
            line = {"color": "#7C3AED", "width": 2.5}
        else:
            fill = "rgba(0,0,0,0)"
            line = {"width": 0}
        fig.add_shape(
            type="rect", x0=left, y0=top, x1=right, y1=bottom,
            fillcolor=fill, line=line, layer="above",
        )
        hover = (
            f"{name}<br>평균 위험도 {average:.2f} / 5"
            f"<br>색상 기준 {stage}단계 · 자료 기준"
            if average is not None else f"{name}<br>위험도 미등록"
        )
        for x in range(left, right + 1, 4):
            for y in range(top, bottom + 1, 4):
                xs.append(x)
                ys.append(y)
                names.append(name)
                texts.append(hover)
    fig.add_trace(go.Scatter(
        x=xs, y=ys, customdata=names, text=texts, mode="markers",
        marker={"size": 6, "symbol": "square", "color": "rgba(0,0,0,0.001)"},
        selected={"marker": {"opacity": 1}},
        unselected={"marker": {"opacity": 1}},
        hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_layout(
        height=570, margin={"l": 0, "r": 0, "t": 0, "b": 0},
        showlegend=False, clickmode="event+select", dragmode=False,
        hovermode="closest", hoverdistance=8,
        xaxis={"range": [0, 818], "autorange": False, "visible": False,
               "fixedrange": True, "constrain": "domain", "constraintoward": "left"},
        yaxis={"range": [560, 0], "autorange": False, "visible": False,
               "fixedrange": True, "scaleanchor": "x", "scaleratio": 1,
               "constrain": "domain", "constraintoward": "top"},
        paper_bgcolor="white", plot_bgcolor="white",
    )
    event = st.plotly_chart(
        fig, use_container_width=True, key=f"{chart_key}_risk_v4",
        on_select="rerun", selection_mode="points",
        config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False},
    )
    points = event.get("selection", {}).get("points", [])
    if points:
        name = points[-1].get("customdata")
        if name in GROUPS and name != st.session_state[state_key]:
            st.session_state[state_key] = name
            st.rerun()


def show_legend(comparison=False):
    cards = "".join(
        f'<span style="background:{bg};color:{fg};border:1px solid {fg};'
        f'padding:10px 13px;border-radius:10px;font-size:17px;font-weight:700;">'
        f'위험도 {stage}단계</span>'
        for stage, (bg, fg) in RISK_COLORS.items()
    )
    cards += (
        '<span style="background:#7C3AED;color:white;padding:10px 13px;'
        'border-radius:10px;font-size:17px;font-weight:700;">현재 선택한 공간</span>'
    )
    st.markdown(
        '<div style="display:flex;gap:9px;flex-wrap:wrap;margin:8px 0 12px;">'
        + cards + '</div>', unsafe_allow_html=True,
    )
    st.caption("자료 기준 · 공간별 위험도 단계의 평균값을 반올림해 색상으로 표시합니다.")
