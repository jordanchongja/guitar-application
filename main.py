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
Welcome! Use the navigation in the sidebar to jump between tools, or the quick links below.

Your **Left-Handed Mode** and **Tuning** choices in the sidebar apply across every page.
"""
)

from modules import practice_store as _store

if _store.unlocked():
    from modules import practice as P
    from modules.pathway_seed import BRANCH_ICONS

    rc = P.month_recap()
    with st.container(border=True):
        top = st.container(horizontal=True, vertical_alignment="center")
        top.subheader(f"Your {rc['month']}")
        top.page_link("pages/0_Practice.py", label="Start practising", icon=":material/play_arrow:")
        delta = rc["minutes"] - rc["last_minutes"]
        with st.container(horizontal=True):
            st.metric("Minutes", rc["minutes"], f"{delta:+d} vs last month" if rc["last_minutes"] else None,
                      border=True)
            st.metric("Sessions", rc["sessions"], border=True)
            st.metric("Days practised", rc["days"], border=True)
        if rc["songs"]:
            st.markdown(":material/music_note: **Songs this month:** " + ", ".join(rc["songs"]))
        if rc["neglected"]:
            names = [f"{BRANCH_ICONS.get(b, '')} {b}" + (f" ({n} days)" if n else " (never)") for b, n in rc["neglected"]]
            st.markdown(":material/notifications: **Haven't touched in a while:** " + " · ".join(names))
        ls = rc["last_session"]
        if ls and ls.get("notes"):
            st.caption(f"Last time ({P.ago(ls['start'])}): {ls['notes']}")
else:
    with st.expander(":material/lock: Your practice summary"):
        _store.password_gate()

st.subheader("Practice tracker")
track_cols = st.columns(3)
with track_cols[0]:
    st.page_link("pages/0_Practice.py", label="Practice (timer + log)", icon=":material/timer:")
with track_cols[1]:
    st.page_link("pages/0_Pathway.py", label="Pathway map & songs", icon=":material/route:")
with track_cols[2]:
    st.page_link("pages/5_Progress_Dashboard.py", label="Progress Dashboard", icon=":material/monitoring:")

st.subheader("Reference")
ref_cols = st.columns(3)
with ref_cols[0]:
    st.page_link("pages/1_Scale_Reference.py", label="Scale Reference", icon="🎼")
with ref_cols[1]:
    st.page_link("pages/6_Chord_Dictionary.py", label="Chord Dictionary", icon="📖")
with ref_cols[2]:
    st.page_link("pages/7_Circle_of_Fifths.py", label="Circle of Fifths", icon="🎡")
ref_cols2 = st.columns(3)
with ref_cols2[0]:
    st.page_link("pages/8_Arpeggio_Visualizer.py", label="Arpeggio Visualizer", icon="🎹")
with ref_cols2[1]:
    st.page_link("pages/3_Chord_Progressions.py", label="Chord Progressions", icon="🎶")
with ref_cols2[2]:
    st.page_link("pages/12_Custom_Tuning_Builder.py", label="Custom Tuning Builder", icon="🎛️")

st.subheader("Practice & Quizzes")
quiz_cols = st.columns(3)
with quiz_cols[0]:
    st.page_link("pages/2_Fretboard_Tester.py", label="Fretboard Tester", icon="🎯")
with quiz_cols[1]:
    st.page_link("pages/4_Ear_Training.py", label="Ear Training (Intervals)", icon="👂")
with quiz_cols[2]:
    st.page_link("pages/13_Functional_Ear_Trainer.py", label="Functional Ear Trainer", icon="🎯")
quiz_cols2 = st.columns(3)
with quiz_cols2[0]:
    st.page_link("pages/10_Sight_Reading_Trainer.py", label="Sight-Reading Trainer", icon="🎼")
with quiz_cols2[1]:
    st.page_link("pages/9_Practice_Generator.py", label="Practice Generator", icon="🗒️")
with quiz_cols2[2]:
    st.page_link("pages/11_Daily_Challenge.py", label="Daily Challenge", icon="🔥")
quiz_cols3 = st.columns(3)
with quiz_cols3[0]:
    st.page_link("pages/14_Metronome.py", label="Metronome", icon="🥁")
with quiz_cols3[1]:
    st.page_link("pages/5_Progress_Dashboard.py", label="Progress Dashboard", icon="📊")

st.divider()

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
