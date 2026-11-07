"""
pages/9_Practice_Generator.py

Phase 3: Randomized Practice Generator.

Pulls from a library of exercises and builds a timed practice routine.
"""

import random

import streamlit as st

from modules.database import log_practice
from modules.settings import render_sidebar_settings
from modules.theory import EXERCISE_LIBRARY, generate_practice_routine

st.set_page_config(page_title="Practice Generator", page_icon="🗒️", layout="wide")
render_sidebar_settings()

st.title("🗒️ Randomized Practice Generator")
st.write("Generate a timed practice routine pulled from a library of exercises.")

col1, col2 = st.columns(2)
with col1:
    total_minutes = st.slider("Total practice time (minutes)", min_value=5, max_value=90, value=30, step=5)
with col2:
    categories = st.multiselect(
        "Focus areas (leave empty for all)", options=list(EXERCISE_LIBRARY.keys()), default=[]
    )

if st.button("🎲 Generate Routine", type="primary"):
    st.session_state.practice_routine = generate_practice_routine(total_minutes, categories or None, random)

routine = st.session_state.get("practice_routine")
if routine:
    st.subheader("Today's Routine")
    for item in routine:
        st.markdown(f"**{item['minutes']} min — {item['category']}**: {item['exercise']}")

    st.divider()
    if st.button("💾 Log this routine as today's practice"):
        log_practice(sum(i["minutes"] for i in routine), "Mixed (Practice Generator)")
        st.success("Added to your all-time practice total!")
else:
    st.info("Choose a duration and focus areas, then click **Generate Routine**.")
