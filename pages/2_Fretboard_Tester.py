"""
pages/2_Fretboard_Tester.py

Task 2: The Fretboard Tester Quiz.

- Highlights a single random string/fret coordinate.
- 4 multiple-choice buttons to guess the note.
- Checkboxes: include sharps/flats, limit to specific strings, limit to frets 1-12.
- Score tracked in st.session_state.
- "Correct!" / "Incorrect, that was a [Note]" feedback + Next Question button.
- Final score can be saved to the database.
"""

import random

import streamlit as st

from modules.database import log_quiz_score
from modules.fretboard import QUESTION_COLOR, draw_fretboard
from modules.settings import render_sidebar_settings
from modules.theory import NOTES_SHARP, note_at_fret

st.set_page_config(page_title="Fretboard Tester", page_icon="🎯", layout="wide")
settings = render_sidebar_settings()
tuning = settings["tuning"]
num_strings = len(tuning)

st.title("🎯 Fretboard Tester")
st.write("Find the note at the highlighted position on the neck.")

# --- Quiz options -----------------------------------------------------
with st.expander("Quiz options", expanded=True):
    opt1, opt2, opt3 = st.columns(3)
    with opt1:
        include_sharps_flats = st.checkbox("Include Sharps/Flats", value=True)
    with opt2:
        limit_frets_12 = st.checkbox("Limit to frets 1–12", value=False)
    with opt3:
        string_labels = [f"String {n}" for n in range(1, num_strings + 1)]
        allowed_strings = st.multiselect("Limit to specific strings", options=string_labels, default=string_labels)

allowed_string_numbers = {int(s.split()[-1]) for s in allowed_strings} or set(range(1, num_strings + 1))
max_fret = 12 if limit_frets_12 else settings["num_frets"]

# --- Session state init -------------------------------------------------
defaults = {
    "ft_score": 0,
    "ft_total": 0,
    "ft_question": None,
    "ft_choices": None,
    "ft_answered": False,
    "ft_last_correct": None,
    "ft_last_answer": None,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


def new_question():
    string_number = random.choice(sorted(allowed_string_numbers))
    fret = random.randint(0, max_fret)
    i = num_strings - string_number
    correct_note = note_at_fret(tuning[i], fret)

    note_pool = NOTES_SHARP if include_sharps_flats else [n for n in NOTES_SHARP if "#" not in n]
    if correct_note not in note_pool:
        note_pool = note_pool + [correct_note]

    distractors = [n for n in note_pool if n != correct_note]
    choices = random.sample(distractors, k=min(3, len(distractors))) + [correct_note]
    random.shuffle(choices)

    st.session_state.ft_question = {"string_number": string_number, "fret": fret, "note": correct_note}
    st.session_state.ft_choices = choices
    st.session_state.ft_answered = False
    st.session_state.ft_last_correct = None
    st.session_state.ft_last_answer = None


if st.session_state.ft_question is None:
    new_question()

question = st.session_state.ft_question

col_score, col_reset = st.columns([3, 1])
with col_score:
    st.metric("Score", f"{st.session_state.ft_score} / {st.session_state.ft_total}")
with col_reset:
    if st.button("Reset Score"):
        st.session_state.ft_score = 0
        st.session_state.ft_total = 0
        new_question()
        st.rerun()

highlights = {
    (question["string_number"], question["fret"]): {"color": QUESTION_COLOR, "label": "?"}
}
fig = draw_fretboard(
    tuning=tuning,
    num_frets=settings["num_frets"],
    highlights=highlights,
    left_handed=settings["left_handed"],
    show_note_names=False,
)
st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})
st.write(f"**String {question['string_number']}, Fret {question['fret']}** — what note is this?")

# --- Answer buttons -------------------------------------------------
btn_cols = st.columns(4)
for i, choice in enumerate(st.session_state.ft_choices):
    with btn_cols[i]:
        if st.button(choice, key=f"choice_{i}_{question['string_number']}_{question['fret']}",
                     disabled=st.session_state.ft_answered, width='stretch'):
            st.session_state.ft_answered = True
            st.session_state.ft_last_answer = choice
            st.session_state.ft_total += 1
            is_correct = choice == question["note"]
            st.session_state.ft_last_correct = is_correct
            if is_correct:
                st.session_state.ft_score += 1
            st.rerun()

if st.session_state.ft_answered:
    if st.session_state.ft_last_correct:
        st.success("Correct! ✅")
    else:
        st.error(f"Incorrect, that was a **{question['note']}**.")
    if st.button("Next Question ➜"):
        new_question()
        st.rerun()

st.divider()
save_col1, save_col2 = st.columns([1, 3])
with save_col1:
    if st.button("💾 Finish & Save Score", disabled=st.session_state.ft_total == 0):
        log_quiz_score("Fretboard Tester", st.session_state.ft_score, st.session_state.ft_total)
        st.session_state.ft_score = 0
        st.session_state.ft_total = 0
        new_question()
        st.success("Score saved to your Progress Dashboard!")
with save_col2:
    st.caption("Saves your current score to the database and starts a fresh session.")
