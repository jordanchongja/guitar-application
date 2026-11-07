"""
modules/fretboard.py

Reusable fretboard visualization engine, built on Plotly (chosen over
Matplotlib/custom SVG because it gives us interactivity, crisp scaling in
the browser, and hover tooltips for free inside Streamlit via st.plotly_chart).

The core entry point is `draw_fretboard`, which every page reuses to render
scales, chord shapes, and quiz questions on the same visual neck.
"""

from __future__ import annotations

import plotly.graph_objects as go

from modules.theory import note_at_fret, note_index

SINGLE_DOT_FRETS = {3, 5, 7, 9, 15, 17, 19, 21}
DOUBLE_DOT_FRETS = {12}

ROOT_COLOR = "#e63946"       # highlighted root notes
NOTE_COLOR = "#457b9d"       # highlighted non-root scale/chord notes
QUESTION_COLOR = "#f4a261"   # fretboard-tester "mystery" marker
NECK_COLOR = "#f1e3c6"
FRET_LINE_COLOR = "#5c4a32"
STRING_COLOR = "#8d99ae"
NUT_COLOR = "#2b2118"


def draw_fretboard(
    tuning: list[str],
    num_frets: int = 22,
    highlights: dict | None = None,
    left_handed: bool = False,
    show_note_names: bool = True,
    title: str | None = None,
    view: tuple[int, int] | None = None,
) -> go.Figure:
    """
    Render a standard guitar neck.

    Parameters
    ----------
    tuning : list of 6 open-string note names, low string (6) -> high string (1)
    num_frets : how many frets to draw (0 = open string included)
    highlights : dict keyed by (string_number, fret) -> {
                     "color": str (optional, defaults to NOTE_COLOR),
                     "label": str (optional, defaults to the note name),
                 }
                 string_number is 1-6 where 1 = high E (thinnest) and 6 = low E.
    left_handed : if True, mirror the neck horizontally.
    show_note_names : if False, highlighted markers show no text (used for quiz
                       questions where the note should stay hidden).
    title : optional chart title.
    view : (lowest fret, highest fret) to zoom in on, for a compact shape diagram.
    """
    highlights = highlights or {}
    num_strings = len(tuning)
    left_edge = view[0] - 1 if view and view[0] > 0 else 0

    fig = go.Figure()

    # --- Neck background -------------------------------------------------
    fig.add_shape(
        type="rect",
        x0=-0.5,
        x1=num_frets + 0.5,
        y0=0.5,
        y1=num_strings + 0.5,
        fillcolor=NECK_COLOR,
        line=dict(width=0),
        layer="below",
    )

    # --- Fret wires --------------------------------------------------------
    for fret in range(num_frets + 1):
        fig.add_shape(
            type="line",
            x0=fret,
            x1=fret,
            y0=0.5,
            y1=num_strings + 0.5,
            line=dict(color=NUT_COLOR if fret == 0 else FRET_LINE_COLOR, width=6 if fret == 0 else 2),
            layer="below",
        )

    # --- Inlay dots --------------------------------------------------------
    for fret in range(1, num_frets + 1):
        if fret in DOUBLE_DOT_FRETS:
            for y_off in (-0.7, 0.7):
                fig.add_shape(
                    type="circle",
                    x0=fret - 0.5 - 0.12,
                    x1=fret - 0.5 + 0.12,
                    y0=(num_strings + 1) / 2 + y_off - 0.12,
                    y1=(num_strings + 1) / 2 + y_off + 0.12,
                    fillcolor="#c9b896",
                    line=dict(width=0),
                    layer="below",
                )
        elif fret in SINGLE_DOT_FRETS:
            fig.add_shape(
                type="circle",
                x0=fret - 0.5 - 0.12,
                x1=fret - 0.5 + 0.12,
                y0=(num_strings + 1) / 2 - 0.12,
                y1=(num_strings + 1) / 2 + 0.12,
                fillcolor="#c9b896",
                line=dict(width=0),
                layer="below",
            )

    # --- Strings -------------------------------------------------------
    # tuning[0] is string 6 (low E) ... tuning[-1] is string 1 (high E).
    # We draw string 6 at y=1 (bottom) up through string 1 at y=6 (top).
    for i, open_note in enumerate(tuning):
        string_number = num_strings - i  # tuning[0] -> string 6, tuning[-1] -> string 1
        y = i + 1
        thickness = 1 + (string_number - 1) * 0.35  # low strings drawn thicker
        fig.add_shape(
            type="line",
            x0=0,
            x1=num_frets,
            y0=y,
            y1=y,
            line=dict(color=STRING_COLOR, width=thickness),
            layer="below",
        )
        # Open-string label on the left
        fig.add_annotation(
            x=left_edge - (0.1 if left_edge else 0.35),
            y=y,
            text=f"<b>{open_note}</b>",
            showarrow=False,
            font=dict(size=12, color="#333"),
            xanchor="right",
        )

    # --- Fret number labels along the bottom --------------------------
    for fret in range(view[0] if view else 0, num_frets + 1):
        x = fret if fret == 0 else fret - 0.5
        fig.add_annotation(
            x=x,
            y=0.15,
            text=str(fret),
            showarrow=False,
            font=dict(size=10, color="#777"),
        )

    # --- Highlighted note markers --------------------------------------
    marker_x, marker_y, marker_color, marker_text, hover_text = [], [], [], [], []
    for (string_number, fret), info in highlights.items():
        i = num_strings - string_number  # invert back to array index
        if i < 0 or i >= num_strings:
            continue
        y = i + 1
        x = fret if fret == 0 else fret - 0.5
        note_name = note_at_fret(tuning[i], fret)
        marker_x.append(x)
        marker_y.append(y)
        marker_color.append(info.get("color", NOTE_COLOR))
        marker_text.append(info.get("label", note_name) if show_note_names else "")
        hover_text.append(f"String {string_number}, Fret {fret}: {note_name}")

    if marker_x:
        fig.add_trace(
            go.Scatter(
                x=marker_x,
                y=marker_y,
                mode="markers+text",
                marker=dict(size=26, color=marker_color, line=dict(width=1.5, color="white")),
                text=marker_text,
                textfont=dict(size=11, color="white"),
                hovertext=hover_text,
                hoverinfo="text",
                showlegend=False,
            )
        )

    # --- Layout -----------------------------------------------------------
    x_range = [left_edge - (0.7 if left_edge else 1.2), (view[1] if view else num_frets) + 0.5]
    fig.update_xaxes(
        range=x_range[::-1] if left_handed else x_range,
        showgrid=False,
        zeroline=False,
        visible=False,
    )
    fig.update_yaxes(
        range=[0, num_strings + (0.6 if view else 1)],
        showgrid=False,
        zeroline=False,
        visible=False,
    )
    fig.update_layout(
        # Streamlit renders fig.layout.title.text as a visible caption above
        # the chart. Passing `title=None` leaves that .text lookup undefined
        # on the frontend, which prints literally as "undefined" -- so we
        # always pass a string, empty when there's no title to show.
        title=title or "",
        height=70 + num_strings * 35 if view else 90 + num_strings * 45,
        margin=dict(l=10, r=10, t=0 if view else 40 if title else 20, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


def draw_clickable_fretboard(
    tuning: list[str],
    num_frets: int = 15,
    selected: set | None = None,
    left_handed: bool = False,
) -> go.Figure:
    """
    A fretboard where every string/fret intersection is a selectable point,
    used by the Chord Dictionary page. Pass the returned figure to
    `st.plotly_chart(fig, on_select="rerun")` and read clicked points back
    from `event.selection.points[i]["customdata"]` -> (string_number, fret).
    """
    selected = selected or set()
    num_strings = len(tuning)
    base_fig = draw_fretboard(tuning, num_frets=num_frets, left_handed=left_handed, show_note_names=False)

    grid_x, grid_y, grid_color, grid_size, grid_custom, grid_hover = [], [], [], [], [], []
    for i, open_note in enumerate(tuning):
        string_number = num_strings - i
        y = i + 1
        for fret in range(0, num_frets + 1):
            x = fret if fret == 0 else fret - 0.5
            note_name = note_at_fret(open_note, fret)
            is_selected = (string_number, fret) in selected
            grid_x.append(x)
            grid_y.append(y)
            grid_color.append(ROOT_COLOR if is_selected else "rgba(69,123,157,0.25)")
            grid_size.append(24 if is_selected else 14)
            grid_custom.append((string_number, fret))
            grid_hover.append(f"String {string_number}, Fret {fret}: {note_name}")

    base_fig.add_trace(
        go.Scatter(
            x=grid_x,
            y=grid_y,
            mode="markers",
            marker=dict(size=grid_size, color=grid_color, line=dict(width=1, color="white")),
            customdata=grid_custom,
            hovertext=grid_hover,
            hoverinfo="text",
            showlegend=False,
        )
    )
    return base_fig


def chord_diagram_svg(tuning: list[str], voicing: dict, root: str, left_handed: bool = False) -> str:
    """
    A chord box as inline SVG: nut at the top, low string on the left (flipped for left-handed
    players), finger numbers in the dots and the note names underneath. `voicing` comes from
    `modules.chord_shapes.find_voicings`.
    """
    frets = voicing["frets"]
    num_strings = len(frets)
    gap, row, left, top, rows = 34, 36, 54, 34, 5
    played = [fret for fret in frets if fret]
    start = 1 if not played or max(played) <= rows else min(played)
    width = left + gap * (num_strings - 1) + 24
    height = top + row * rows + 30

    def string_x(i: int) -> float:
        return left + gap * (num_strings - 1 - i if left_handed else i)

    def fret_y(fret: int) -> float:
        return top + (fret - start + 0.5) * row

    parts = [f'<rect x="{left}" y="{top}" width="{gap * (num_strings - 1)}" height="{row * rows}" fill="{NECK_COLOR}"/>']
    for line in range(rows + 1):
        y = top + line * row
        thick = line == 0 and start == 1
        parts.append(f'<line x1="{left}" y1="{y}" x2="{left + gap * (num_strings - 1)}" y2="{y}" '
                     f'stroke="{NUT_COLOR if thick else FRET_LINE_COLOR}" stroke-width="{6 if thick else 1.5}"/>')
    for i in range(num_strings):
        x = string_x(i)
        parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + row * rows}" stroke="{STRING_COLOR}" '
                     f'stroke-width="{1 + (num_strings - 1 - i) * 0.35}"/>')
    if start > 1:
        parts.append(f'<text x="{left - 17}" y="{fret_y(start) + 5}" text-anchor="end" font-size="14" '
                     f'fill="{NUT_COLOR}">{start}fr</text>')

    barre = voicing["barre"]
    if barre:
        ends = sorted((string_x(barre["first"]), string_x(barre["last"])))
        y = fret_y(barre["fret"])
        parts.append(f'<rect x="{ends[0] - 13}" y="{y - 13}" width="{ends[1] - ends[0] + 26}" height="26" rx="13" '
                     f'fill="{NOTE_COLOR}"/>')

    root_index = note_index(root)
    for i, fret in enumerate(frets):
        x = string_x(i)
        if fret is None or fret == 0:
            mark = "×" if fret is None else "○"
            parts.append(f'<text x="{x}" y="{top - 10}" text-anchor="middle" font-size="16" fill="{NUT_COLOR}">{mark}</text>')
        name = "" if fret is None else note_at_fret(tuning[i], fret)
        parts.append(f'<text x="{x}" y="{height - 6}" text-anchor="middle" font-size="13" fill="{NUT_COLOR}">{name}</text>')
        if fret:
            fill = ROOT_COLOR if note_index(name) == root_index else NOTE_COLOR
            y = fret_y(fret)
            parts.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{fill}" stroke="white" stroke-width="1.5"/>')
            parts.append(f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-size="14" font-weight="600" '
                         f'fill="white">{voicing["fingers"][i]}</text>')

    summary = " ".join("x" if fret is None else str(fret) for fret in frets)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" '
            f'aria-label="Chord diagram, low string to high: {summary}" '
            f'style="display:block;width:100%;max-width:{width}px;height:auto">{"".join(parts)}</svg>')


def build_scale_highlights(tuning: list[str], num_frets: int, scale_notes: list[str], root_note: str,
                            frets_range: tuple[int, int] | None = None) -> dict:
    """Highlight every occurrence of `scale_notes` on the neck (root colored differently)."""
    highlights = {}
    lo, hi = frets_range if frets_range else (0, num_frets)
    num_strings = len(tuning)
    for i, open_note in enumerate(tuning):
        string_number = num_strings - i
        for fret in range(lo, hi + 1):
            note = note_at_fret(open_note, fret)
            if note in scale_notes:
                is_root = note == root_note
                highlights[(string_number, fret)] = {
                    "color": ROOT_COLOR if is_root else NOTE_COLOR,
                    "label": note,
                }
    return highlights
