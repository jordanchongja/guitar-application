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

from modules.theory import note_at_fret

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
    """
    highlights = highlights or {}
    num_strings = len(tuning)

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
            x=-0.35,
            y=y,
            text=f"<b>{open_note}</b>",
            showarrow=False,
            font=dict(size=12, color="#333"),
            xanchor="right",
        )

    # --- Fret number labels along the bottom --------------------------
    for fret in range(0, num_frets + 1):
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
    fig.update_xaxes(
        range=[num_frets + 0.5, -1.2] if left_handed else [-1.2, num_frets + 0.5],
        showgrid=False,
        zeroline=False,
        visible=False,
    )
    fig.update_yaxes(
        range=[0, num_strings + 1],
        showgrid=False,
        zeroline=False,
        visible=False,
    )
    fig.update_layout(
        title=title,
        height=90 + num_strings * 45,
        margin=dict(l=10, r=10, t=40 if title else 20, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


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
