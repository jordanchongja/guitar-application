"""
main.py

Entry point for the Guitar Learning App. This is the Streamlit "Home" page;
the other features live as separate pages in `pages/` and are picked up
automatically by Streamlit's multipage navigation in the sidebar.
"""

import streamlit as st

from modules.database import init_db
from modules.fretboard import draw_fretboard
from modules.settings import render_sidebar_settings

st.set_page_config(
    page_title="Guitar Learning App",
    page_icon="🎸",
    layout="wide",
)

init_db()
settings = render_sidebar_settings()

st.title("🎸 Guitar Learning App")
st.markdown(
    """
Welcome! Use the navigation in the sidebar to jump between tools:

- **Scale Reference** — visualize Major/Minor/Pentatonic scales anywhere on the neck.
- **Fretboard Tester** — a note-finding quiz to drill fretboard knowledge.
- **Chord Progressions** — generate diatonic chords and common progressions for any key.
- **Ear Training** — train your ear to recognize intervals.
- **Progress Dashboard** — log practice time and review your quiz history.

Your **Left-Handed Mode** and **Tuning** choices in the sidebar apply across every page.
"""
)

st.subheader("Standard Tuning Fretboard")
fig = draw_fretboard(
    tuning=settings["tuning"],
    num_frets=settings["num_frets"],
    left_handed=settings["left_handed"],
    title=None,
)
st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})

st.caption(
    "This is the reusable fretboard renderer (`modules/fretboard.py`) that every "
    "page in this app builds on."
)
