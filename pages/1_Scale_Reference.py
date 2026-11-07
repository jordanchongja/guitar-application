"""
pages/1_Scale_Reference.py

Task 1: Scale Reference & Fretboard Visualization.

- Key + Scale Type dropdowns
- CAGED shapes for the major, minor and pentatonic scales, one at a time or all five together
- Dots labelled with note names or intervals
- Root notes highlighted in a different color
- Respects the global Left-Handed Mode toggle
"""

import streamlit as st

from modules.fretboard import ROOT_COLOR, NOTE_COLOR, build_scale_highlights, draw_fretboard
from modules.settings import render_sidebar_settings
from modules.theory import (ALL_KEYS, CAGED_SHAPES, DEFAULT_TUNING_NAME, MINOR_PENTATONIC_BOXES, SCALE_INTERVALS,
                            TUNING_PRESETS, get_caged_shape, get_position_windows, get_scale_notes,
                            get_three_nps_pattern, interval_label)

st.set_page_config(page_title="Scale Reference", page_icon="🎼", layout="wide")
settings = render_sidebar_settings()

st.title("🎼 Scale Reference")

ALL_SHAPES = "All 5 shapes"


def shape_labels(scale_type: str) -> dict[str, str]:
    """Position dropdown label -> CAGED shape."""
    if scale_type == "Minor Pentatonic":
        return {f"Box {i} ({s} shape)": s for i, s in enumerate(MINOR_PENTATONIC_BOXES, 1)}
    return {f"{s} shape": s for s in CAGED_SHAPES}


# The shapes are fingerings for standard tuning; other tunings get the approximate positions.
use_shapes = list(settings["tuning"]) == TUNING_PRESETS[DEFAULT_TUNING_NAME]

col1, col2, col3, col4 = st.columns(4)
with col1:
    key = st.selectbox("Key", options=ALL_KEYS, index=0)
with col2:
    scale_type = st.selectbox("Scale Type", options=list(SCALE_INTERVALS.keys()))
with col3:
    shapes = shape_labels(scale_type) if use_shapes else {}
    if use_shapes:
        position_options = ["All Neck", ALL_SHAPES] + list(shapes)
    else:
        position_options = ["All Neck", "Position 1", "Position 2", "Position 3", "Position 4", "Position 5"]
    # 3-notes-per-string patterns only make sense for 7-note scales.
    if scale_type in ("Major", "Natural Minor"):
        position_options = position_options + ["3-Notes-Per-String"]
    position = st.selectbox("Position", options=position_options)
with col4:
    show_intervals = st.segmented_control("Show on the dots", ["Notes", "Intervals"], default="Notes") == "Intervals"

scale_notes = get_scale_notes(key, scale_type)


def dot_label(note: str) -> str:
    return interval_label(key, note) if show_intervals else note


def shape_highlights(notes: dict) -> dict:
    return {spot: {"color": ROOT_COLOR if note == key else NOTE_COLOR, "label": dot_label(note)}
            for spot, note in notes.items()}


st.markdown(
    f"**{key} {scale_type}** — notes: "
    + " • ".join(f"`{n}`" for n in scale_notes)
    + " — intervals: "
    + " • ".join(f"`{interval_label(key, n)}`" for n in scale_notes)
)

frets_range = None
three_nps_pattern = None
start_fret = 0
shape_notes = None

if position == ALL_SHAPES:
    if "Minor" in scale_type:
        st.caption("Named after the chord shapes of the relative major, which uses the same boxes.")
    for row in (list(shapes.items())[:3], list(shapes.items())[3:]):
        for column, (label, shape) in zip(st.columns(3), row):
            notes = get_caged_shape(key, scale_type, shape)
            frets = [fret for _, fret in notes]
            with column:
                st.markdown(f"**{label}** :gray[· frets {min(frets)}–{max(frets)}]")
                st.plotly_chart(
                    draw_fretboard(settings["tuning"], num_frets=max(frets), highlights=shape_highlights(notes),
                                   left_handed=settings["left_handed"], view=(min(frets), max(frets))),
                    width="stretch", config={"displayModeBar": False, "staticPlot": True}, key=f"shape_{shape}")
elif position in shapes:
    shape_notes = get_caged_shape(key, scale_type, shapes[position])
    frets = [fret for _, fret in shape_notes]
    st.caption(f"Frets {min(frets)}–{max(frets)}.")
elif position == "3-Notes-Per-String":
    start_fret = st.slider(
        "Starting fret", min_value=0, max_value=max(0, settings["num_frets"] - 8), value=0,
        help="Drag this to shift the whole diagonal pattern up or down the neck -- practice moving "
             "smoothly between positions instead of staying in one box.",
    )
    three_nps_pattern = get_three_nps_pattern(key, scale_type, settings["tuning"], start_fret=start_fret,
                                               num_frets=settings["num_frets"])
    strings_covered = len({s for (s, f) in three_nps_pattern})
    if strings_covered < len(settings["tuning"]):
        st.warning(
            f"Only {strings_covered} of {len(settings['tuning'])} strings fit before running out of neck "
            "from this starting fret -- try a lower starting fret to see the full 6-string pattern."
        )
    else:
        st.caption("A real 3-notes-per-string diagonal shape: exactly 3 ascending scale tones on every string.")
elif position != "All Neck":
    idx = position_options.index(position) - 1  # 0-based into windows list
    windows = get_position_windows(key, settings["tuning"])
    if idx < len(windows):
        frets_range = windows[idx]
        st.caption(
            f"Showing frets {frets_range[0]}–{frets_range[1]} "
            "(approximate movable position anchored on the root note — see "
            "`modules/theory.get_position_windows` for how this is derived)."
        )
    else:
        st.warning("This position isn't available for the current tuning; showing the full neck instead.")

if position != ALL_SHAPES:
    if shape_notes is not None or three_nps_pattern is not None:
        highlights = shape_highlights(shape_notes if shape_notes is not None else three_nps_pattern)
    else:
        highlights = build_scale_highlights(
            tuning=settings["tuning"],
            num_frets=settings["num_frets"],
            scale_notes=scale_notes,
            root_note=key,
            frets_range=frets_range,
        )
        for dot in highlights.values():
            dot["label"] = dot_label(dot["label"])

    fig = draw_fretboard(
        tuning=settings["tuning"],
        num_frets=max([settings["num_frets"]] + [fret for _, fret in highlights]),
        highlights=highlights,
        left_handed=settings["left_handed"],
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})

legend_col1, legend_col2 = st.columns(2)
with legend_col1:
    st.markdown(f"🔴 <span style='color:{ROOT_COLOR}'>■</span> Root note ({key})", unsafe_allow_html=True)
with legend_col2:
    st.markdown(f"🔵 <span style='color:{NOTE_COLOR}'>■</span> Other scale notes", unsafe_allow_html=True)
