"""
app_pages/6_Chord_Dictionary.py

Build a chord shape on the neck by tapping or dragging, and this page names it. Going the other way,
from a chord name to a shape, is the Chord Finder page.
"""

import streamlit as st

from modules.chord_shapes import name_voicing, pattern
from modules.fret_picker import fret_picker
from modules.settings import render_sidebar_settings

st.set_page_config(page_title="Chord Dictionary", page_icon="📖", layout="wide")
settings = render_sidebar_settings()
tuning = settings["tuning"]

st.title("📖 Chord Dictionary")
st.write("Put a shape on the neck and this names the chord.")
st.caption(
    "Click a fret to add a note, or drag across the strings to add several at once. Each string holds "
    "one note, so picking another fret moves it. Click a note to remove it, or drag from a note to remove "
    "a run of them. Left of the nut is an open string."
)

frets_to_show = st.slider("Frets to show", min_value=5, max_value=settings["num_frets"], value=12)
picked = fret_picker(tuning, frets_to_show, settings["left_handed"], key="chord_dict_picker")
voicing = name_voicing(tuning, picked)

if not picked:
    st.info("No notes yet. Drag across a few strings to build a chord.")
else:
    if voicing["matches"]:
        best = voicing["matches"][0]
        st.subheader(f"{best['symbol']}: {best['label']}")
        also = [m["symbol"] for m in voicing["matches"][1:]]
        if also:
            st.write(f"Could also be read as {', '.join(also)}.")
    else:
        st.subheader("No standard chord")
        st.write("Try adding a root, 3rd and 5th, such as C, E and G for C major.")
    st.caption(f"Shape {pattern(voicing['frets'])}, low string to high. Notes: {' '.join(voicing['notes'])}.")

st.page_link("app_pages/17_Chord_Finder.py", label="Know the chord but not the shape? Open the Chord Finder", icon="🔍")
