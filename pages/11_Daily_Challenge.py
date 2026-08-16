"""
pages/11_Daily_Challenge.py

Additional feature: "Daily Challenge" / "Riff of the Day".

A randomized daily goal, seeded by the date so it's the same for everyone
until midnight, then changes.
"""

import datetime as dt
import random

import streamlit as st

from modules.settings import render_sidebar_settings
from modules.theory import generate_challenge_from_seed, generate_daily_challenge

st.set_page_config(page_title="Daily Challenge", page_icon="🔥", layout="wide")
render_sidebar_settings()

st.title("🔥 Daily Challenge")

today = dt.date.today()
challenge = generate_daily_challenge(today)

st.subheader(f"{challenge['title']} — {today.strftime('%A, %B %d, %Y')}")
st.markdown(f"### {challenge['description']}")
st.caption("This challenge is the same for everyone today and refreshes at midnight.")

st.divider()
st.markdown("Feeling ambitious? Roll a bonus challenge for extra practice (today's official one stays the same):")

if st.button("🎲 Give me another challenge"):
    st.session_state.bonus_seed = f"bonus-{random.randint(0, 1_000_000)}"

if st.session_state.get("bonus_seed"):
    bonus = generate_challenge_from_seed(st.session_state.bonus_seed)
    st.info(f"**{bonus['title']}**: {bonus['description']}")
