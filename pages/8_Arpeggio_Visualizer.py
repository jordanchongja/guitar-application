"""
pages/8_Arpeggio_Visualizer.py

Phase 3: Arpeggio Visualizer.

Shows Major, Minor, Major 7, Minor 7, Dominant 7, and Diminished 7 arpeggio
shapes across the fretboard, reusing the same fretboard renderer as the
Scale Reference page.
"""

import streamlit as st

from modules.fretboard import ROOT_COLOR, build_scale_highlights, draw_fretboard
from modules.settings import render_sidebar_settings
from modules.theory import ALL_KEYS, ARPEGGIO_INTERVALS, get_arpeggio_notes, get_position_windows

st.set_page_config(page_title="Arpeggio Visualizer", page_icon="🎹", layout="wide")
settings = render_sidebar_settings()

st.title("🎹 Arpeggio Visualizer")
st.write("Visualize arpeggio shapes across the neck -- essential for lead playing and jazz vocabulary.")

col1, col2, col3 = st.columns(3)
with col1:
    key = st.selectbox("Root", options=ALL_KEYS, index=0)
with col2:
    arpeggio_type = st.selectbox("Arpeggio Type", options=list(ARPEGGIO_INTERVALS.keys()), index=2)
with col3:
    position_options = ["All Neck", "Position 1", "Position 2", "Position 3", "Position 4", "Position 5"]
    position = st.selectbox("Position", options=position_options)

arpeggio_notes = get_arpeggio_notes(key, arpeggio_type)
st.markdown(f"**{key} {arpeggio_type}** — notes: " + " • ".join(f"`{n}`" for n in arpeggio_notes))

frets_range = None
if position != "All Neck":
    idx = position_options.index(position) - 1
    windows = get_position_windows(key, settings["tuning"])
    if idx < len(windows):
        frets_range = windows[idx]
        st.caption(f"Showing frets {frets_range[0]}–{frets_range[1]} (approximate position, anchored on the root).")

highlights = build_scale_highlights(
    tuning=settings["tuning"],
    num_frets=settings["num_frets"],
    scale_notes=arpeggio_notes,
    root_note=key,
    frets_range=frets_range,
)

fig = draw_fretboard(
    tuning=settings["tuning"],
    num_frets=settings["num_frets"],
    highlights=highlights,
    left_handed=settings["left_handed"],
)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
st.markdown(f"🔴 <span style='color:{ROOT_COLOR}'>■</span> Root note ({key})", unsafe_allow_html=True)
