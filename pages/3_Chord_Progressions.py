"""
pages/3_Chord_Progressions.py

Task 3: Chord Progression Generator.

- Key dropdown.
- Diatonic chords for the key (I, ii, iii, IV, V, vi, vii°).
- "Generate Progression" picks a common pattern and shows the actual chords.
- Embeds a (placeholder) YouTube backing track for the selected key.
"""

import random

import streamlit as st

from modules.settings import render_sidebar_settings
from modules.theory import (
    ALL_KEYS,
    COMMON_PROGRESSIONS,
    YOUTUBE_BACKING_TRACKS,
    diatonic_chords,
    generate_progression,
)

st.set_page_config(page_title="Chord Progressions", page_icon="🎶", layout="wide")
settings = render_sidebar_settings()

st.title("🎶 Chord Progression Generator")

col1, col2 = st.columns(2)
with col1:
    key = st.selectbox("Key", options=ALL_KEYS, index=0)
with col2:
    scale_type = st.selectbox("Scale Type", options=["Major", "Natural Minor"])

st.subheader(f"Diatonic Chords in {key} {scale_type}")
chords = diatonic_chords(key, scale_type)

chord_cols = st.columns(7)
for c, col in zip(chords, chord_cols):
    with col:
        st.markdown(f"**{c['roman']}**")
        st.markdown(f"### {c['symbol']}")
        st.caption(" - ".join(c["notes"]))

st.divider()

st.subheader("Generate a Progression")
pattern_name = st.selectbox("Progression Pattern", options=list(COMMON_PROGRESSIONS.keys()))

if "chosen_pattern" not in st.session_state:
    st.session_state.chosen_pattern = None

gen_col1, gen_col2 = st.columns([1, 1])
with gen_col1:
    if st.button("🎲 Generate Progression", width='stretch'):
        st.session_state.chosen_pattern = pattern_name
with gen_col2:
    if st.button("🎲 Surprise Me (random pattern)", width='stretch'):
        st.session_state.chosen_pattern = random.choice(list(COMMON_PROGRESSIONS.keys()))

if st.session_state.chosen_pattern:
    progression = generate_progression(key, scale_type, st.session_state.chosen_pattern)
    st.markdown(f"**{st.session_state.chosen_pattern}** in {key} {scale_type}:")
    prog_cols = st.columns(len(progression))
    for c, col in zip(progression, prog_cols):
        with col:
            st.markdown(f"<div style='text-align:center'><b>{c['roman']}</b><br><h3>{c['symbol']}</h3></div>",
                        unsafe_allow_html=True)

    st.divider()
    st.subheader(f"🎧 Backing Track for {key}")
    st.caption("Placeholder link — swap `YOUTUBE_BACKING_TRACKS` in `modules/theory.py` for real jam-track URLs.")
    st.link_button("Open backing track search on YouTube", YOUTUBE_BACKING_TRACKS[key])
else:
    st.info("Choose a pattern and click **Generate Progression** to see the chords.")
