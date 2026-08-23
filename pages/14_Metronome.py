"""
pages/14_Metronome.py

A simple metronome / click-track generator. "Always use a metronome" is the
single most consistent piece of advice across guitar practice methodology --
this generates a click track (with an accented downbeat) as a WAV clip you
can play in-browser while practicing.
"""

import time

import streamlit as st

from modules.audio import generate_metronome_click_wav
from modules.settings import render_sidebar_settings

st.set_page_config(page_title="Metronome", page_icon="🥁", layout="wide")

# Same deferred-write pattern as the Custom Tuning Builder: the BPM slider
# below is bound to session_state via its key, so Tap Tempo (which needs to
# update that same key) has to write it *before* the slider is instantiated
# this run, not after -- Streamlit forbids the latter.
if "_pending_bpm" in st.session_state:
    st.session_state.metronome_bpm = st.session_state.pop("_pending_bpm")

render_sidebar_settings()

st.title("🥁 Metronome")
st.write("Generate a click track to practice against. Every source on guitar practice technique "
         "agrees on this: always practice technical material locked to a click.")

st.session_state.setdefault("metronome_bpm", 100)
st.session_state.setdefault("tap_times", [])

col1, col2 = st.columns([3, 1])
with col1:
    bpm = st.slider("Tempo (BPM)", min_value=40, max_value=240, key="metronome_bpm")
with col2:
    st.write("")  # vertical spacer to align the button with the slider
    if st.button("👆 Tap Tempo", width="stretch"):
        now = time.time()
        taps = st.session_state.tap_times
        if taps and (now - taps[-1]) > 2.5:
            taps = []  # long pause since the last tap -- start a fresh tempo
        taps.append(now)
        st.session_state.tap_times = taps[-8:]
        if len(st.session_state.tap_times) >= 2:
            intervals = [b - a for a, b in zip(st.session_state.tap_times, st.session_state.tap_times[1:])]
            avg_interval = sum(intervals) / len(intervals)
            tapped_bpm = round(60 / avg_interval)
            st.session_state._pending_bpm = max(40, min(240, tapped_bpm))
        st.rerun()

st.caption("Tap the button a few times in a row at your desired tempo, or drag the slider directly.")

col3, col4, col5 = st.columns(3)
with col3:
    beats_per_measure = st.selectbox("Beats per measure", options=[2, 3, 4, 5, 6], index=2)
with col4:
    duration = st.slider("Duration (seconds)", min_value=10, max_value=180, value=60, step=10)
with col5:
    accent = st.checkbox("Accent beat 1", value=True)

if st.button("▶️ Generate Click Track", type="primary"):
    st.session_state.metronome_wav = generate_metronome_click_wav(bpm, beats_per_measure, duration, accent)

if st.session_state.get("metronome_wav"):
    st.audio(st.session_state.metronome_wav, format="audio/wav")
    st.caption("Your browser's player controls handle looping/replaying -- hit play again for another pass.")
else:
    st.info("Set a tempo and click **Generate Click Track**.")
