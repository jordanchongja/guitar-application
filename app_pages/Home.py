"""
app_pages/Home.py

The Guitar Learning App's home page: your month so far and links to everything else.
"""

import streamlit as st

from modules.fretboard import draw_fretboard
from modules.navigation import SECTIONS
from modules.settings import render_sidebar_settings

st.set_page_config(
    page_title="Guitar Learning App",
    page_icon="🎸",
    layout="wide",
)

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
        top.page_link("app_pages/0_Practice.py", label="Start practising", icon=":material/play_arrow:")
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

for section, pages in SECTIONS.items():
    if not section:
        continue
    st.subheader(section)
    for start in range(0, len(pages), 3):
        cols = st.columns(3)
        for col, (path, title, icon) in zip(cols, pages[start:start + 3]):
            with col:
                st.page_link(path, label=title, icon=icon)

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
