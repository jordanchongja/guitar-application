"""
pages/4_Ear_Training.py

Task 4: Ear Training (Intervals).

- Tones generated dynamically with numpy (no external audio assets needed).
- Plays a root note, waits, then plays a second note (one WAV clip).
- User guesses the interval via multiple choice.
- Score tracked in st.session_state, savable to the database.
"""

import random

import streamlit as st

from modules.audio import generate_interval_wav
from modules.database import log_quiz_score
from modules.settings import render_sidebar_settings
from modules.theory import INTERVAL_NAMES

st.set_page_config(page_title="Ear Training", page_icon="👂", layout="wide")
render_sidebar_settings()

st.title("👂 Ear Training — Intervals")
st.write("Listen to the two notes, then guess the interval between them.")

defaults = {
    "et_score": 0,
    "et_total": 0,
    "et_question": None,
    "et_choices": None,
    "et_answered": False,
    "et_last_correct": None,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


def new_question():
    root = random.randint(-12, 12)
    interval = random.choice(list(INTERVAL_NAMES.keys()))
    wav_bytes = generate_interval_wav(root, interval)

    all_names = list(INTERVAL_NAMES.values())
    correct_name = INTERVAL_NAMES[interval]
    distractors = [n for n in all_names if n != correct_name]
    choices = random.sample(distractors, k=3) + [correct_name]
    random.shuffle(choices)

    st.session_state.et_question = {"root": root, "interval": interval, "name": correct_name, "wav": wav_bytes}
    st.session_state.et_choices = choices
    st.session_state.et_answered = False
    st.session_state.et_last_correct = None


if st.session_state.et_question is None:
    new_question()

question = st.session_state.et_question

col_score, col_reset = st.columns([3, 1])
with col_score:
    st.metric("Score", f"{st.session_state.et_score} / {st.session_state.et_total}")
with col_reset:
    if st.button("Reset Score"):
        st.session_state.et_score = 0
        st.session_state.et_total = 0
        new_question()
        st.rerun()

st.audio(question["wav"], format="audio/wav")
st.caption("Click play above to hear the root note, then the second note.")

btn_cols = st.columns(4)
for i, choice in enumerate(st.session_state.et_choices):
    with btn_cols[i]:
        if st.button(choice, key=f"interval_choice_{i}_{question['root']}_{question['interval']}",
                     disabled=st.session_state.et_answered, width='stretch'):
            st.session_state.et_answered = True
            st.session_state.et_total += 1
            is_correct = choice == question["name"]
            st.session_state.et_last_correct = is_correct
            if is_correct:
                st.session_state.et_score += 1
            st.rerun()

if st.session_state.et_answered:
    if st.session_state.et_last_correct:
        st.success("Correct! ✅")
    else:
        st.error(f"Incorrect, that was a **{question['name']}**.")
    if st.button("Next Question ➜"):
        new_question()
        st.rerun()

st.divider()
save_col1, save_col2 = st.columns([1, 3])
with save_col1:
    if st.button("💾 Finish & Save Score", disabled=st.session_state.et_total == 0):
        log_quiz_score("Ear Training - Intervals", st.session_state.et_score, st.session_state.et_total)
        st.session_state.et_score = 0
        st.session_state.et_total = 0
        new_question()
        st.success("Score saved to Quiz Scores!")
with save_col2:
    st.caption("Saves your current score to the database and starts a fresh session.")
