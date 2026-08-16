"""
pages/1_Scale_Reference.py

Task 1: Scale Reference & Fretboard Visualization.

- Key + Scale Type dropdowns
- CAGED-style Position toggle (1-5, or "All Neck")
- Root notes highlighted in a different color
- Respects the global Left-Handed Mode toggle
"""

import streamlit as st

from modules.fretboard import build_scale_highlights, draw_fretboard, NOTE_COLOR, ROOT_COLOR
from modules.settings import render_sidebar_settings
from modules.theory import ALL_KEYS, SCALE_INTERVALS, get_position_windows, get_scale_notes

st.set_page_config(page_title="Scale Reference", page_icon="🎼", layout="wide")
settings = render_sidebar_settings()

st.title("🎼 Scale Reference")

col1, col2, col3 = st.columns(3)
with col1:
    key = st.selectbox("Key", options=ALL_KEYS, index=0)
with col2:
    scale_type = st.selectbox("Scale Type", options=list(SCALE_INTERVALS.keys()))
with col3:
    position_options = ["All Neck", "Position 1", "Position 2", "Position 3", "Position 4", "Position 5"]
    position = st.selectbox("CAGED Position", options=position_options)

scale_notes = get_scale_notes(key, scale_type)

st.markdown(
    f"**{key} {scale_type}** — notes: "
    + " • ".join(f"`{n}`" for n in scale_notes)
)

frets_range = None
if position != "All Neck":
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

highlights = build_scale_highlights(
    tuning=settings["tuning"],
    num_frets=settings["num_frets"],
    scale_notes=scale_notes,
    root_note=key,
    frets_range=frets_range,
)

fig = draw_fretboard(
    tuning=settings["tuning"],
    num_frets=settings["num_frets"],
    highlights=highlights,
    left_handed=settings["left_handed"],
)
st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})

legend_col1, legend_col2 = st.columns(2)
with legend_col1:
    st.markdown(f"🔴 <span style='color:{ROOT_COLOR}'>■</span> Root note ({key})", unsafe_allow_html=True)
with legend_col2:
    st.markdown(f"🔵 <span style='color:{NOTE_COLOR}'>■</span> Other scale notes", unsafe_allow_html=True)
