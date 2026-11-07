"""
app_pages/17_Chord_Finder.py

Pick a root note and a chord type, and this page shows ways to play it: a diagram and the finger
placements for each shape, worked out for the current tuning.
"""

import streamlit as st

from modules.chord_analysis import KEY_ROOTS
from modules.chord_shapes import (CHORD_TYPES, chord_symbol, chord_tone_names, find_voicings, pattern, shape_steps,
                                  shape_title)
from modules.fretboard import chord_diagram_svg
from modules.settings import render_sidebar_settings

st.set_page_config(page_title="Chord Finder", page_icon="🔍", layout="wide")
settings = render_sidebar_settings()
tuning = settings["tuning"]

st.title("🔍 Chord Finder")
st.write("Pick a note and a chord type to see how to play it.")


@st.cache_data(show_spinner=False)
def voicings_for(tuning: tuple[str, ...], root: str, quality: str) -> list[dict]:
    return find_voicings(list(tuning), root, quality)


root = st.pills("Root note", KEY_ROOTS, default="C")
type_label = st.pills("Chord type", [label for label, _, _ in CHORD_TYPES], default="Major")

if not root or not type_label:
    st.info("Pick a root note and a chord type.")
    st.stop()

quality, formula = next((q, f) for label, q, f in CHORD_TYPES if label == type_label)
notes = chord_tone_names(root, quality)

st.subheader(chord_symbol(root, quality))
st.write(f"Notes: **{' '.join(notes)}**. Formula: {formula}.")

voicings = voicings_for(tuple(tuning), root, quality)
if not voicings:
    st.warning("No playable shape with the root in the bass in this tuning.")
    st.stop()

st.caption(
    "Easiest shapes first, with the root as the lowest note. Red dots are the root, and the numbers are "
    "fingers: 1 index, 2 middle, 3 ring, 4 pinky."
)
for start in range(0, len(voicings), 3):
    for column, voicing in zip(st.columns(3), voicings[start:start + 3]):
        with column:
            st.markdown(f"**{shape_title(voicing)}**")
            st.markdown(chord_diagram_svg(tuning, voicing, root, settings["left_handed"]), unsafe_allow_html=True)
            st.caption(f"Shape {pattern(voicing['frets'])}, low string to high")
            st.markdown("\n".join(f"- {step}" for step in shape_steps(voicing)))
